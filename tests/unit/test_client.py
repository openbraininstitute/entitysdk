import io
from unittest.mock import patch

import pytest

from entitysdk.client import Client
from entitysdk.mixin import HasAssets
from entitysdk.models.entity import Entity


def test_client_project_context__raises():
    client = Client(api_url="foo", project_context=None)

    with pytest.raises(ValueError, match="A project context must be specified."):
        client._project_context(override_context=None)


def test_client_search(client, httpx_mock, auth_token):
    httpx_mock.add_response(
        method="GET",
        json={
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "page_size": 10, "total_items": 2},
        },
    )
    res = list(
        client.search(
            entity_type=Entity,
            query={"name": "foo"},
            token=auth_token,
            limit=2,
        )
    )
    assert len(res) == 2
    assert res[0].id == 1
    assert res[1].id == 2


def test_client_update(client, httpx_mock, auth_token):
    httpx_mock.add_response(method="PATCH", json={"id": 1})

    res = client.update(
        entity_id=1,
        entity_type=Entity,
        attrs_or_entity=Entity(id=1),
        token=auth_token,
    )

    assert res.id == 1


@pytest.fixture
def mock_asset_response():
    return {
        "id": 1,
        "path": "path/to/asset",
        "full_path": "full/path/to/asset",
        "bucket_name": "bucket_name",
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
    mock_asset_response,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/1/assets",
        match_headers=request_headers,
        json=mock_asset_response,
    )

    path = tmp_path / "foo.h5"
    path.write_bytes(b"foo")

    res = client.upload_file(
        entity_id=1,
        entity_type=Entity,
        file_name="foo",
        file_path=path,
        file_content_type="text/plain",
        file_metadata={"key": "value"},
        token=auth_token,
    )

    assert res.id == 1


def test_client_upload_content(
    client, httpx_mock, mock_asset_response, api_url, project_context, auth_token, request_headers
):
    buffer = io.BytesIO(b"foo")
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity/1/assets",
        match_headers=request_headers,
        match_files={
            "file": (
                "foo.txt",
                buffer,
                "text/plain",
            )
        },
        json=mock_asset_response,
    )
    res = client.upload_content(
        entity_id=1,
        entity_type=Entity,
        file_name="foo.txt",
        file_content=buffer,
        file_content_type="text/plain",
        file_metadata={"key": "value"},
        token=auth_token,
    )

    assert res.id == 1


def test_client_download_content(
    client, httpx_mock, mock_asset_response, api_url, project_context, auth_token, request_headers
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/1/assets/2/download",
        match_headers=request_headers,
        content=b"foo",
    )

    res = client.download_content(
        entity_id=1,
        entity_type=Entity,
        asset_id=2,
        token=auth_token,
    )
    assert res == b"foo"


def test_client_download_file(
    tmp_path,
    client,
    httpx_mock,
    mock_asset_response,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/1/assets/2/download",
        match_headers=request_headers,
        content=b"foo",
    )

    output_path = tmp_path / "foo.h5"

    client.download_file(
        entity_id=1,
        entity_type=Entity,
        asset_id=2,
        output_path=output_path,
        token=auth_token,
    )
    assert output_path.read_bytes() == b"foo"


@patch("entitysdk.route.get_route_name")
def test_client_get(
    mock_route,
    client,
    httpx_mock,
    mock_asset_response,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    class EntityWithAssets(HasAssets, Entity):
        """Entity plus assets."""

    mock_route.return_value = "entity"

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/1",
        match_headers=request_headers,
        json={"id": 1},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/1/assets",
        match_headers=request_headers,
        json={
            "data": [mock_asset_response, mock_asset_response],
            "pagination": {"page": 1, "page_size": 10, "total_items": 2},
        },
    )

    res = client.get(
        entity_id=1,
        entity_type=EntityWithAssets,
        token=auth_token,
        with_assets=True,
    )
    assert res.id == 1
    assert len(res.assets) == 2


@pytest.fixture
def mock_asset_delete_response():
    return {
        "path": "buffer.h5",
        "full_path": "private/103d7868/103d7868/assets/reconstruction_morphology/8703/buffer.h5",
        "bucket_name": "obi-private",
        "is_directory": False,
        "content_type": "application/swc",
        "size": 18,
        "sha256_digest": "47ddc1b6e05dcbfbd2db9dcec4a49d83c6f9f10ad595649bacdcb629671fd954",
        "meta": {},
        "id": 16393,
        "status": "deleted",
    }


@patch("entitysdk.route.get_route_name")
def test_client_delete_asset(
    mock_route,
    client,
    httpx_mock,
    mock_asset_delete_response,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    mock_route.return_value = "reconstruction-morphology"

    httpx_mock.add_response(
        method="DELETE",
        url=f"{api_url}/reconstruction-morphology/1/assets/2",
        match_headers=request_headers,
        json=mock_asset_delete_response,
    )

    res = client.delete_asset(
        entity_id=1,
        entity_type=None,
        asset_id=2,
        token=auth_token,
    )

    assert res.status == "deleted"


@patch("entitysdk.route.get_route_name")
def test_client_update_asset(
    mock_route,
    tmp_path,
    client,
    httpx_mock,
    mock_asset_response,
    api_url,
    project_context,
    auth_token,
    request_headers,
):
    mock_route.return_value = "reconstruction-morphology"

    httpx_mock.add_response(
        method="DELETE",
        url=f"{api_url}/reconstruction-morphology/1/assets/2",
        match_headers=request_headers,
        json=mock_asset_response,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/reconstruction-morphology/1/assets",
        match_headers=request_headers,
        json=mock_asset_response,
    )

    path = tmp_path / "file.txt"
    path.touch()

    res = client.update_asset_file(
        entity_id=1,
        entity_type=None,
        file_path=path,
        file_name="foo.txt",
        file_content_type="application/swc",
        asset_id=2,
        token=auth_token,
    )

    assert res.status == "created"
