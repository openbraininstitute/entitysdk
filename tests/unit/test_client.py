import io
import re
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from entitysdk.client import Client
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset, MTypeClass
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import DeploymentEnvironment


def test_client_api_url():
    client = Client(api_url="foo")
    assert client.api_url == "foo"

    client = Client(api_url=None, environment="staging")
    assert client.api_url == settings.staging_api_url

    client = Client(api_url=None, environment="production")
    assert client.api_url == settings.production_api_url

    with pytest.raises(
        EntitySDKError, match="Either the api_url or environment must be defined, not both."
    ):
        Client(api_url="foo", environment="staging")

    with pytest.raises(EntitySDKError, match="Neither api_url nor environment have been defined."):
        Client()

    with pytest.raises(EntitySDKError, match="Either api_url or environment is of the wrong type."):
        Client(api_url=int)

    str_envs = [str(env) for env in DeploymentEnvironment]
    expected = f"'foo' is not a valid DeploymentEnvironment. Choose one of: {str_envs}"
    with pytest.raises(EntitySDKError, match=re.escape(expected)):
        Client(environment="foo")


def test_client_get_token():
    class Foo:
        def get_token(self):
            return "foo"

    client = Client(api_url="foo", project_context=None, token_manager=Foo())

    res = client._get_token()
    assert res == "foo"

    res = client._get_token(override_token="override")
    assert res == "override"


def test_client__get_token__raises():
    client = Client(api_url="foo", project_context=None)

    with pytest.raises(
        EntitySDKError, match="Either override_token or token_manager must be provided."
    ):
        client._get_token()


def test_client_project_context__raises():
    client = Client(api_url="foo", project_context=None)

    with pytest.raises(EntitySDKError, match="A project context is mandatory for this operation."):
        client._required_user_context(override_context=None)


def test_client_search(client, httpx_mock, auth_token):
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        json={
            "data": [
                {"id": str(id1), "name": "foo", "description": "bar", "type": "zee"},
                {"id": str(id2), "name": "foo", "description": "bar", "type": "zee"},
            ],
            "pagination": {"page": 1, "page_size": 10, "total_items": 2},
        },
    )
    res = list(
        client.search_entity(
            entity_type=Entity,
            query={"name": "foo"},
            token=auth_token,
            limit=2,
        )
    )
    assert len(res) == 2
    assert res[0].id == id1
    assert res[1].id == id2


@patch("entitysdk.route.get_route_name")
def test_client_nupdate(mocked_route, client, httpx_mock, auth_token):
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
        token=auth_token,
    )

    assert res.id == id1
    assert res.name == new_name

    httpx_mock.add_response(method="PATCH", json={"id": str(id1), "name": new_name})

    res = client.update_entity(
        entity_id=id1,
        entity_type=Foo,
        attrs_or_entity=Foo(name=new_name),
        token=auth_token,
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
        "path": "path/to/asset",
        "full_path": "full/path/to/asset",
        "is_directory": False,
        "content_type": "text/plain",
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def test_client_upload_file(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )

    path = tmp_path / "foo.h5"
    path.write_bytes(b"foo")

    res = client.upload_file(
        entity_id=entity_id,
        entity_type=Entity,
        file_name="foo",
        file_path=path,
        file_content_type="text/plain",
        file_metadata={"key": "value"},
        token=auth_token,
    )

    assert res.id == asset_id


def test_client_upload_content(
    client, httpx_mock, api_url, project_context, auth_token, request_headers
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    buffer = io.BytesIO(b"foo")
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/{entity_id}/assets",
        match_headers=request_headers,
        match_files={
            "file": (
                "foo.txt",
                buffer,
                "text/plain",
            )
        },
        json=_mock_asset_response(asset_id),
    )
    res = client.upload_content(
        entity_id=entity_id,
        entity_type=Entity,
        file_name="foo.txt",
        file_content=buffer,
        file_content_type="text/plain",
        file_metadata={"key": "value"},
        token=auth_token,
    )

    assert res.id == asset_id


def test_client_download_content(
    client, httpx_mock, api_url, project_context, auth_token, request_headers
):
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
        token=auth_token,
    )
    assert res == b"foo"


def test_client_download_file__output_file(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
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
        token=auth_token,
    )
    assert output_path.read_bytes() == b"foo"


def test_client_download_file__output_file__inconsistent_ext(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
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
            token=auth_token,
        )


def test_client_download_file__output_file__user_subdirectory_path(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
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
        token=auth_token,
    )
    assert output_path.read_bytes() == b"foo"


def test_client_download_file__asset_subdirectory_paths(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
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
        token=auth_token,
    )
    client.download_file(
        entity_id=entity_id,
        entity_type=Entity,
        asset_id=asset2_id,
        output_path=output_path,
        token=auth_token,
    )

    assert Path(output_path, "foo/bar/foo.h5").read_bytes() == b"foo"
    assert Path(output_path, "foo/bar/bar.swc").read_bytes() == b"bar"


@patch("entitysdk.route.get_route_name")
def test_client_get(
    mock_route,
    client,
    httpx_mock,
    api_url,
    project_context,
    auth_token,
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
            "type": "entity",
            "assets": [
                _mock_asset_response(asset_id1),
                _mock_asset_response(asset_id2),
            ],
        },
    )

    res = client.get_entity(
        entity_id=str(entity_id),
        entity_type=Entity,
        token=auth_token,
    )
    assert res.id == entity_id
    assert len(res.assets) == 2
    assert res.assets[0].id == asset_id1
    assert res.assets[1].id == asset_id2


def _mock_asset_delete_response(asset_id):
    return {
        "path": "buffer.h5",
        "full_path": "private/103d7868/103d7868/assets/reconstruction_morphology/8703/buffer.h5",
        "is_directory": False,
        "content_type": "application/swc",
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
    project_context,
    auth_token,
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
        token=auth_token,
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
    project_context,
    auth_token,
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
        token=auth_token,
    )

    assert res.id == asset_id
    assert res.status == "created"


def test_client_download_assets(
    tmp_path, api_url, client, project_context, auth_token, request_headers, httpx_mock
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
                | {"path": "foo/bar/bar.h5", "content_type": "application/hdf5"},
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
        token=auth_token,
    ).one()

    assert res.asset.path == "foo/bar/bar.swc"
    assert res.output_path == tmp_path / "foo/bar/bar.swc"
    assert res.output_path.read_bytes() == b"bar"


def test_client_download_assets__no_assets_raise(
    tmp_path, api_url, client, project_context, auth_token, request_headers, httpx_mock
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
            token=auth_token,
        ).one()


def test_client_download_assets__non_entity(
    tmp_path, api_url, client, project_context, auth_token, request_headers, httpx_mock
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
            token=auth_token,
        ).one()


def test_client_download_assets__directory_not_supported(
    tmp_path, api_url, client, project_context, auth_token, request_headers, httpx_mock
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
            token=auth_token,
        ).one()


def test_client_download_assets__entity(
    tmp_path, api_url, client, project_context, auth_token, request_headers, httpx_mock
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
        token=auth_token,
    ).all()

    assert len(res) == 1
