import io
import re
import uuid
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from entitysdk.client import Client
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset, Circuit, MTypeClass
from entitysdk.models.asset import DetailedFile, DetailedFileList
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import (
    AssetLabel,
    ContentType,
    DeploymentEnvironment,
    DerivationType,
    StorageType,
)


def test_client_api_url():
    client = Client(api_url="foo", token_manager="foo")
    assert client.api_url == "foo"

    client = Client(api_url=None, environment="staging", token_manager="foo")
    assert client.api_url == settings.staging_api_url

    client = Client(api_url=None, environment="production", token_manager="foo")
    assert client.api_url == settings.production_api_url

    with pytest.raises(
        EntitySDKError, match="Either the api_url or environment must be defined, not both."
    ):
        Client(api_url="foo", environment="staging", token_manager="foo")

    with pytest.raises(EntitySDKError, match="Neither api_url nor environment have been defined."):
        Client(token_manager="foo")

    with pytest.raises(EntitySDKError, match="Either api_url or environment is of the wrong type."):
        Client(api_url=int, token_manager="foo")

    str_envs = [str(env) for env in DeploymentEnvironment]
    expected = f"'foo' is not a valid DeploymentEnvironment. Choose one of: {str_envs}"
    with pytest.raises(EntitySDKError, match=re.escape(expected)):
        Client(environment="foo", token_manager="foo")


def test_client_project_context__raises():
    client = Client(api_url="foo", project_context=None, token_manager="foo")

    with pytest.raises(EntitySDKError, match="A project context is mandatory for this operation."):
        client._required_user_context(override_context=None)


def test_client_search(client, httpx_mock):
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        json={
            "data": [
                {"id": str(id1), "name": "foo", "description": "bar", "type": "circuit"},
                {"id": str(id2), "name": "foo", "description": "bar", "type": "circuit"},
            ],
            "pagination": {"page": 1, "page_size": 10, "total_items": 2},
        },
    )
    res = list(
        client.search_entity(
            entity_type=Entity,
            query={"name": "foo"},
            limit=2,
        )
    )
    assert len(res) == 2
    assert res[0].id == id1
    assert res[1].id == id2


@patch("entitysdk.route.get_route_name")
def test_client_nupdate(mocked_route, client, httpx_mock):
    class Foo(Identifiable):
        name: str

    id1 = uuid.uuid4()

    new_name = "bar"

    httpx_mock.add_response(
        method="PATCH", json={"id": str(id1), "name": new_name, "description": "bar"}
    )

    res = client.update_entity(
        entity_id=id1,
        entity_type=Foo,
        attrs_or_entity={"name": new_name},
    )

    assert res.id == id1
    assert res.name == new_name

    httpx_mock.add_response(method="PATCH", json={"id": str(id1), "name": new_name})

    res = client.update_entity(
        entity_id=id1,
        entity_type=Foo,
        attrs_or_entity=Foo(name=new_name),
    )

    assert res.id == id1
    assert res.name == new_name


def _mock_entity_response(entity_id):
    return {
        "id": str(entity_id),
        "description": "my-entity",
    }


def _mock_asset_response(asset_id):
    return {
        "id": str(asset_id),
        "path": "path_to_asset",
        "full_path": "full/path_to_asset",
        "is_directory": False,
        "content_type": "text/plain",
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
        "label": "morphology",
    }


def test_client_upload_file(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets",
        match_headers=request_headers,
        match_files={"file": ("foo", b"foo", "application/swc")},
        match_data={"label": "morphology"},
        json=_mock_asset_response(asset_id),
    )

    path = tmp_path / "foo.h5"
    path.write_bytes(b"foo")

    res = client.upload_file(
        entity_id=entity_id,
        entity_type=Entity,
        file_name="foo",
        file_path=path,
        file_content_type="application/swc",
        file_metadata={"key": "value"},
        asset_label="morphology",
    )

    assert res.id == asset_id


def test_client_upload_content(client, httpx_mock, api_url, request_headers):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    buffer = io.BytesIO(b"foo")
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets",
        match_headers=request_headers,
        match_files={"file": ("foo.swc", buffer, "application/swc")},
        match_data={"label": "morphology"},
        json=_mock_asset_response(asset_id),
    )
    res = client.upload_content(
        entity_id=entity_id,
        entity_type=Entity,
        file_name="foo.swc",
        file_content=buffer,
        file_content_type="application/swc",
        file_metadata={"key": "value"},
        asset_label="morphology",
    )

    assert res.id == asset_id


def test_client_download_content(client, httpx_mock, api_url, request_headers):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=b"foo",
    )

    res = client.download_content(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
    )
    assert res == b"foo"


def test_client_download_content__asset_path(
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    # for downloading the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download?asset_path=foo.txt",
        match_headers=request_headers,
        content=b"foo",
    )

    res = client.download_content(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
        asset_path="foo.txt",
    )
    assert res == b"foo"


def test_client_download_file__output_file(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.h5"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=b"foo",
    )

    output_path = tmp_path / "foo.h5"

    client.download_file(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
        output_path=output_path,
    )
    assert output_path.read_bytes() == b"foo"


def test_client_download_file__output_file__inconsistent_ext(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """User must provide a path extension that is consitent with the asset path."""

    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.swc"},
    )
    output_path = tmp_path / "foo.h5"

    with pytest.raises(
        EntitySDKError, match=f"File path {output_path} does not have expected extension .swc."
    ):
        client.download_file(
            entity_id=entity_id,
            entity_type=Entity,
            asset_id=asset_id,
            output_path=output_path,
        )


def test_client_download_file__output_file__user_subdirectory_path(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """User provides a nested output path that overrides the asset path."""

    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.h5"},
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=b"foo",
    )

    output_path = tmp_path / "foo" / "bar" / "bar.h5"

    client.download_file(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
        output_path=output_path,
    )
    assert output_path.read_bytes() == b"foo"


def test_client_download_file__asset_path(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"is_directory": True},
    )

    with pytest.raises(EntitySDKError, match="require an `asset_path`"):
        client.download_file(
            entity_id=entity_id,
            entity_type=Entity,
            asset_id=asset_id,
            output_path=tmp_path,
            asset_path=None,
        )

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )

    with pytest.raises(EntitySDKError, match="Cannot pass `asset_path`"):
        client.download_file(
            entity_id=entity_id,
            entity_type=Entity,
            asset_id=asset_id,
            output_path=tmp_path,
            asset_path="wrong/to/have/asset_path",
        )


def test_client_download_file__asset_subdirectory_paths(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """User provides directory, relative file paths from assets are written to it."""

    entity_id = uuid.uuid4()
    asset1_id = uuid.uuid4()
    asset2_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset1_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset1_id) | {"path": "foo/bar/foo.h5"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset1_id}/download",
        match_headers=request_headers,
        content=b"foo",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset2_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset2_id) | {"path": "foo/bar/bar.swc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset2_id}/download",
        match_headers=request_headers,
        content=b"bar",
    )
    output_path = tmp_path

    client.download_file(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset1_id,
        output_path=output_path,
    )
    client.download_file(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset2_id,
        output_path=output_path,
    )

    assert Path(output_path, "foo/bar/foo.h5").read_bytes() == b"foo"
    assert Path(output_path, "foo/bar/bar.swc").read_bytes() == b"bar"


@patch("entitysdk.route.get_route_name")
def test_client_get(
    mock_route,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id1 = uuid.uuid4()
    asset_id2 = uuid.uuid4()

    mock_route.return_value = "entity"

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}",
        match_headers=request_headers,
        json={
            "id": str(entity_id),
            "name": "foo",
            "description": "bar",
            "type": "circuit",
            "assets": [
                _mock_asset_response(asset_id1),
                _mock_asset_response(asset_id2),
            ],
        },
    )

    res = client.get_entity(
        entity_id=str(entity_id),
        entity_type=Entity,
    )
    assert res.id == entity_id
    assert len(res.assets) == 2
    assert res.assets[0].id == asset_id1
    assert res.assets[1].id == asset_id2


def _mock_asset_delete_response(asset_id):
    return {
        "path": "buffer.h5",
        "full_path": "private/103d7868/103d7868/assets/reconstruction_morphology/8703/buffer.swc",
        "is_directory": False,
        "content_type": "application/swc",
        "label": "morphology",
        "size": 18,
        "sha256_digest": "47ddc1b6e05dcbfbd2db9dcec4a49d83c6f9f10ad595649bacdcb629671fd954",
        "meta": {},
        "id": str(asset_id),
        "status": "deleted",
    }


@patch("entitysdk.route.get_route_name")
def test_client_delete_asset(
    mock_route,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    mock_route.return_value = "reconstruction-morphology"

    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="DELETE",
        url=f"{api_url}/reconstruction-morphology/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_delete_response(asset_id),
    )

    res = client.delete_asset(
        entity_id=entity_id,
        entity_type=None,
        asset_id=asset_id,
    )

    assert res.id == asset_id
    assert res.status == "deleted"


@patch("entitysdk.route.get_route_name")
def test_client_update_asset(
    mock_route,
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    mock_route.return_value = "reconstruction-morphology"

    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="DELETE",
        url=f"{api_url}/reconstruction-morphology/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/reconstruction-morphology/{entity_id}/assets",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )

    path = tmp_path / "file.txt"
    path.touch()

    res = client.update_asset_file(
        entity_id=entity_id,
        entity_type=None,
        file_path=path,
        file_name="foo.txt",
        file_content_type="application/swc",
        asset_id=asset_id,
    )

    assert res.id == asset_id
    assert res.status == "created"


def test_client_download_assets(
    tmp_path, api_url, client, project_context, request_headers, httpx_mock
):
    entity_id = uuid.uuid4()
    asset1_id = uuid.uuid4()
    asset2_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}",
        match_headers=request_headers,
        json=_mock_entity_response(entity_id)
        | {
            "assets": [
                _mock_asset_response(asset1_id)
                | {"path": "foo/bar/bar.h5", "content_type": "application/x-hdf5"},
                _mock_asset_response(asset2_id)
                | {"path": "foo/bar/bar.swc", "content_type": "application/swc"},
            ]
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset2_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset2_id)
        | {"path": "foo/bar/bar.swc", "content_type": "application/swc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset2_id}/download",
        match_headers=request_headers,
        content=b"bar",
    )

    res = client.download_assets(
        (entity_id, Entity),
        selection={"content_type": "application/swc"},
        output_path=tmp_path,
        project_context=project_context,
    ).one()

    assert res.asset.path == "foo/bar/bar.swc"
    assert res.path == tmp_path / "foo/bar/bar.swc"
    assert res.path.read_bytes() == b"bar"


def test_client_download_assets__no_assets_raise(
    tmp_path, api_url, client, project_context, request_headers, httpx_mock
):
    entity_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}",
        match_headers=request_headers,
        json=_mock_entity_response(entity_id) | {"assets": []},
    )

    with pytest.raises(EntitySDKError, match="has no assets"):
        client.download_assets(
            (entity_id, Entity),
            selection={"content_type": "application/swc"},
            output_path=tmp_path,
            project_context=project_context,
        ).one()


def test_client_download_assets__non_entity(
    tmp_path, api_url, client, project_context, request_headers, httpx_mock
):
    entity_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/mtype/{entity_id}",
        match_headers=request_headers,
        json=_mock_entity_response(entity_id) | {"pref_label": "foo", "definition": "bar"},
    )

    with pytest.raises(EntitySDKError, match="has no assets"):
        client.download_assets(
            (entity_id, MTypeClass),
            selection={"content_type": "application/swc"},
            output_path=tmp_path,
            project_context=project_context,
        ).one()


def test_client_download_assets__directory_not_supported(
    tmp_path, api_url, client, project_context, request_headers, httpx_mock
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}",
        match_headers=request_headers,
        json=_mock_entity_response(entity_id)
        | {"assets": [_mock_asset_response(asset_id) | {"is_directory": True}]},
    )

    with pytest.raises(
        NotImplementedError, match="Downloading asset directories is not supported yet."
    ):
        client.download_assets(
            (entity_id, Entity),
            output_path=tmp_path,
            project_context=project_context,
        ).one()


def test_client_download_assets__entity(
    tmp_path, api_url, client, project_context, request_headers, httpx_mock
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    entity = Entity(
        id=entity_id,
        name="foo",
        description="bar",
        assets=[
            Asset(
                id=asset_id,
                path="foo.json",
                full_path="/foo/asset1",
                is_directory=False,
                content_type="application/json",
                label="cell_composition_summary",
                size=1,
            ),
        ],
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id)
        | {"path": "foo.json", "content_type": "application/json"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=b"bar",
    )

    res = client.download_assets(
        entity,
        selection={"content_type": "application/json"},
        output_path=tmp_path,
        project_context=project_context,
    ).all()

    assert len(res) == 1


def test_upload_directory_by_paths(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    request_headers,
):
    entity_id = uuid.uuid4()

    paths = {
        Path("foo/bar/baz/subdir0/file1.txt"): tmp_path / "subdir0/file1.txt",
        Path("foo/bar/baz/file0.txt"): tmp_path / "file0.txt",
        Path("subdir0/subdir1/file2.txt"): tmp_path / "subdir0/subdir1/file2.txt",
    }
    with pytest.raises(Exception, match="does not exist"):
        client.upload_directory(
            entity_id=entity_id,
            entity_type=Entity,
            name="test-directory",
            paths=paths,
            label="sonata_circuit",
            metadata=None,
        )

    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.open("w").close()

    asset = {
        "content_type": "application/vnd.directory",
        "full_path": "asdf",
        "id": "a370a57b-7211-4426-8046-970758ceaf68",
        "is_directory": True,
        "label": "sonata_circuit",
        "meta": {},
        "path": "",
        "sha256_digest": None,
        "size": -1,
        "status": "created",
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets/directory/upload",
        match_headers=request_headers,
        json={
            "asset": asset,
            "files": {
                "foo/bar/baz/subdir0/file1.txt": "http://upload_url0",
                "foo/bar/baz/file0.txt": "http://upload_url1",
                "subdir0/subdir1/file2.txt": "http://upload_url2",
            },
        },
    )

    httpx_mock.add_response(method="PUT", url="http://upload_url0")
    httpx_mock.add_response(method="PUT", url="http://upload_url1")
    httpx_mock.add_response(method="PUT", url="http://upload_url2")

    res = client.upload_directory(
        entity_id=entity_id,
        entity_type=Entity,
        name="test-directory",
        paths=paths,
        label=None,
        metadata=None,
    )
    assert res == Asset.model_validate(asset)

    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets/directory/upload",
        match_headers=request_headers,
        json={
            "asset": asset,
            "files": {
                "foo/bar/baz/subdir0/file1.txt": "http://upload_url0",
            },
        },
    )

    # have read error / exception
    httpx_mock.add_exception(
        httpx.ReadTimeout("Unable to read within timeout"),
        method="PUT",
        url="http://upload_url0",
    )
    httpx_mock.add_exception(
        httpx.ReadTimeout("Unable to read within timeout"),
        method="PUT",
        url="http://upload_url0",
    )
    httpx_mock.add_exception(
        httpx.ReadTimeout("Unable to read within timeout"),
        method="PUT",
        url="http://upload_url0",
    )

    with pytest.raises(EntitySDKError, match="Uploading these files failed"):
        client.upload_directory(
            entity_id=entity_id,
            entity_type=Entity,
            name="test-directory",
            paths=paths,
            label=None,
            metadata=None,
        )

    # have s3 upload fail:
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets/directory/upload",
        match_headers=request_headers,
        json={
            "asset": asset,
            "files": {
                "file0.txt": "http://upload_url0",
            },
        },
    )

    httpx_mock.add_response(method="PUT", url="http://upload_url0", status_code=404)
    httpx_mock.add_response(method="PUT", url="http://upload_url0", status_code=404)
    httpx_mock.add_response(method="PUT", url="http://upload_url0", status_code=404)

    with pytest.raises(EntitySDKError, match="Uploading these files failed"):
        client.upload_directory(
            entity_id=entity_id,
            entity_type=Entity,
            name="test-directory",
            paths={Path("file0.txt"): tmp_path / "file0.txt"},
            label=None,
            metadata=None,
        )


def test_client_list_directory(
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    date = "2025-01-01T00:00:00Z"
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/list",
        match_headers=request_headers,
        json={
            "files": {
                "a/b/foo.txt": {"name": "a/b/foo.txt", "size": 1, "last_modified": date},
                "a/foo.txt": {"name": "a/foo.txt", "size": 2, "last_modified": date},
                "foo.txt": {"name": "foo.txt", "size": 3, "last_modified": date},
            }
        },
    )

    res = client.list_directory(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
    )
    assert isinstance(res, DetailedFileList)
    assert len(res.files) == 3
    assert isinstance(res.files[Path("a/b/foo.txt")], DetailedFile)
    assert res.files[Path("a/b/foo.txt")].name == "a/b/foo.txt"


@pytest.mark.parametrize("max_concurrent", [1, 4])
def test_client_download_directory_ignore_directory(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
    max_concurrent,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    date = "2025-01-01T00:00:00Z"
    # for listing dirs
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/list",
        match_headers=request_headers,
        json={
            "files": {
                "foo.txt": {"name": "foo.txt", "size": 3, "last_modified": date},
            }
        },
    )
    # for getting the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"is_directory": True},
    )

    # for downloading the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download?asset_path=foo.txt",
        match_headers=request_headers,
        text="file contents",
    )

    res = client.download_directory(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
        output_path=tmp_path,
        ignore_directory_name=True,
        max_concurrent=max_concurrent,
    )
    assert len(res) == 1
    assert res[0] == (tmp_path / "foo.txt").absolute()


@pytest.mark.parametrize("max_concurrent", [1, 4])
def test_client_download_directory(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
    max_concurrent,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    date = "2025-01-01T00:00:00Z"
    # for listing dirs
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/list",
        match_headers=request_headers,
        json={
            "files": {
                "foo.txt": {"name": "foo.txt", "size": 3, "last_modified": date},
            }
        },
    )
    # for getting the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"is_directory": True},
    )

    # for downloading the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download?asset_path=foo.txt",
        match_headers=request_headers,
        text="file contents",
    )

    res = client.download_directory(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset_id,
        output_path=tmp_path,
        ignore_directory_name=False,
    )
    assert len(res) == 1
    assert res[0] == (tmp_path / "path_to_asset/foo.txt").absolute()

    # fail if file already exists
    target = tmp_path / "foo"
    target.open("w").close()
    with pytest.raises(EntitySDKError):
        res = client.download_directory(
            entity_id=entity_id,
            entity_type=Entity,
            asset_id=asset_id,
            output_path=target,
            ignore_directory_name=False,
            max_concurrent=max_concurrent,
        )


@pytest.mark.parametrize("max_concurrent", [1, 4])
def test_client_download_directory__asset(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
    max_concurrent,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    date = "2025-01-01T00:00:00Z"

    asset = Asset(
        id=asset_id,
        path="path_to_asset",
        full_path="/circuit",
        is_directory=True,
        size=0,
        content_type="application/vnd.directory",
        label="sonata_circuit",
    )

    # for listing dirs
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/list",
        match_headers=request_headers,
        json={
            "files": {
                "foo.txt": {"name": "foo.txt", "size": 3, "last_modified": date},
            }
        },
    )

    # for downloading the asset
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download?asset_path=foo.txt",
        match_headers=request_headers,
        text="file contents",
    )

    res = client.download_directory(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset,
        output_path=tmp_path,
        ignore_directory_name=False,
        max_concurrent=max_concurrent,
    )
    assert len(res) == 1
    assert res[0] == (tmp_path / "path_to_asset/foo.txt").absolute()


@patch("entitysdk.route.get_route_name")
def test_client_register_asset(
    mock_route,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    mock_route.return_value = "reconstruction-morphology"

    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/reconstruction-morphology/{entity_id}/assets/register",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )

    res = client.register_asset(
        entity_id=entity_id,
        entity_type=None,
        name="foo.swc",
        storage_path="path/to/foo.swc",
        storage_type=StorageType.aws_s3_open,
        is_directory=False,
        content_type=ContentType.application_swc,
        asset_label=AssetLabel.morphology,
    )

    assert res.id == asset_id
    assert res.status == "created"


@patch("entitysdk.route.get_route_name")
def test_client_get_entity_derivations(mock_route, client, httpx_mock, api_url, request_headers):
    mock_route.return_value = "circuit"
    entity_id = uuid.uuid4()

    derivation_1 = uuid.uuid4()
    derivation_2 = uuid.uuid4()

    used_id = uuid.uuid4()
    generated_id = uuid.uuid4()

    def add_response(derivation_type: DerivationType):
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/circuit/{entity_id}/derived-from?derivation_type={derivation_type}",
            match_headers=request_headers,
            json={
                "data": [
                    {
                        "id": str(derivation_1),
                        "used_id": str(used_id),
                        "generated_id": str(generated_id),
                        "derivation_type": derivation_type,
                    },
                    {
                        "id": str(derivation_2),
                        "used_id": str(used_id),
                        "generated_id": str(generated_id),
                        "derivation_type": derivation_type,
                    },
                ]
            },
        )

    add_response(DerivationType.circuit_extraction)
    res = client.get_entity_derivations(
        entity_id=entity_id, entity_type=Circuit, derivation_type=DerivationType.circuit_extraction
    ).all()
    assert len(res) == 2
    assert res[0].id == derivation_1
    assert res[1].id == derivation_2

    add_response(DerivationType.circuit_rewiring)
    res = client.get_entity_derivations(
        entity_id=entity_id, entity_type=Circuit, derivation_type=DerivationType.circuit_rewiring
    ).all()
    assert len(res) == 2
    assert res[0].id == derivation_1
    assert res[1].id == derivation_2

    add_response(DerivationType.unspecified)
    res = client.get_entity_derivations(
        entity_id=entity_id, entity_type=Circuit, derivation_type=DerivationType.unspecified
    ).all()
    assert len(res) == 2
    assert res[0].id == derivation_1
    assert res[1].id == derivation_2
