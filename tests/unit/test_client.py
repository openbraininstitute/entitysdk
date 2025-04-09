import io
import re
import uuid
from unittest.mock import patch

import pytest

from entitysdk.client import Client
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.mixin import HasAssets
from entitysdk.models.entity import Entity
from entitysdk.typedef import DeploymentEnvironment


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
            "data": [{"id": str(id1)}, {"id": str(id2)}],
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
    class Foo(Entity):
        name: str

    id1 = uuid.uuid4()

    new_name = "bar"

    httpx_mock.add_response(method="PATCH", json={"id": str(id1), "name": new_name})

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


def test_client_download_file(
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

    class EntityWithAssets(HasAssets, Entity):
        """Entity plus assets."""

    mock_route.return_value = "entity"

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}",
        match_headers=request_headers,
        json={"id": str(entity_id)},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets",
        match_headers=request_headers,
        json={
            "data": [_mock_asset_response(asset_id1), _mock_asset_response(asset_id2)],
            "pagination": {"page": 1, "page_size": 10, "total_items": 2},
        },
    )

    res = client.get_entity(
        entity_id=str(entity_id),
        entity_type=EntityWithAssets,
        token=auth_token,
        with_assets=True,
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
