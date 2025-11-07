from pathlib import Path
from uuid import UUID

import pytest

from entitysdk import Client
from entitysdk.models import CellMorphology
from entitysdk.mount import DataMount
from entitysdk.route import get_assets_endpoint


@pytest.fixture(scope="module")
def virtual_lab_id():
    return UUID(int=10)


@pytest.fixture(scope="module")
def project_id():
    return UUID(int=20)


@pytest.fixture(scope="module")
def entity_id():
    return UUID(int=0)


@pytest.fixture(scope="module")
def entity_type():
    return CellMorphology


@pytest.fixture(scope="module")
def public_asset_file_id():
    return UUID(int=1)


@pytest.fixture(scope="module")
def public_asset_file_metadata(virtual_lab_id, project_id, entity_id, public_asset_file_id):
    path = "cell.swc"
    full_path = f"public/{virtual_lab_id}/{project_id}/assets/cell_morphology/{entity_id}/{path}"
    return {
        "id": str(public_asset_file_id),
        "path": path,
        "full_path": full_path,
        "is_directory": False,
        "content_type": "application/swc",
        "label": "morphology",
        "size": 18,
        "sha256_digest": "123456",
        "meta": {},
        "status": "created",
        "storage_type": "aws_s3_internal",
    }


def _mock_httpx_asset_metadata(httpx_mock, api_url, asset_id, entity_id, entity_type, metadata):
    url = get_assets_endpoint(
        api_url=api_url,
        asset_id=asset_id,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    httpx_mock.add_response(
        url=url,
        method="GET",
        json=metadata,
    )


@pytest.fixture
def public_asset_file_httpx_mock(
    httpx_mock, public_asset_file_metadata, api_url, entity_type, entity_id, public_asset_file_id
):
    _mock_httpx_asset_metadata(
        httpx_mock,
        api_url,
        public_asset_file_id,
        entity_id,
        entity_type,
        public_asset_file_metadata,
    )


@pytest.fixture(scope="module")
def public_asset_directory_id():
    return UUID(int=2)


@pytest.fixture(scope="module")
def public_asset_directory_metadata(
    virtual_lab_id, project_id, entity_id, public_asset_directory_id
):
    path = "morphologies"
    full_path = f"public/{virtual_lab_id}/{project_id}/assets/cell_morphology/{entity_id}/{path}"
    return {
        "id": str(public_asset_directory_id),
        "path": path,
        "full_path": full_path,
        "is_directory": True,
        "content_type": "application/vnd.directory",
        "label": "morphology",
        "size": 18,
        "sha256_digest": "123456",
        "meta": {},
        "status": "created",
        "storage_type": "aws_s3_internal",
    }


@pytest.fixture
def public_asset_directory_httpx_mock(
    httpx_mock,
    public_asset_directory_metadata,
    api_url,
    entity_type,
    entity_id,
    public_asset_directory_id,
):
    _mock_httpx_asset_metadata(
        httpx_mock,
        api_url,
        public_asset_directory_id,
        entity_id,
        entity_type,
        public_asset_directory_metadata,
    )


@pytest.fixture(scope="module")
def data_mount(tmp_path_factory, public_asset_file_metadata, public_asset_directory_metadata):
    prefix = tmp_path_factory.mktemp("data")

    public_file = prefix / public_asset_file_metadata["full_path"]
    public_file.parent.mkdir(parents=True, exist_ok=True)
    public_file.write_bytes(b"public")

    public_directory = prefix / public_asset_directory_metadata["full_path"]
    public_directory.mkdir(parents=True, exist_ok=True)
    Path(public_directory, "dir_cell.swc").write_bytes(b"public_directory_file")

    return DataMount(prefix=prefix)


@pytest.fixture(scope="module")
def client_with_mount(api_url, data_mount):
    return Client(api_url=api_url, token_manager="bar", data_mount=data_mount)


def test_client__download_content__data_mount__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_httpx_mock,
):
    """If a data mount is available Client.download_content will fetch the bytes from there."""

    res = client_with_mount.download_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
    )
    assert res == b"public"


def test_client__download_content__data_mount__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    public_asset_directory_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the mounted path."""
    res = client_with_mount.download_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
    )
    assert res == b"public_directory_file"


def test_client__download_file__data_mount(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.download_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
    )
    assert res.is_symlink()
    assert res.resolve().name == "cell.swc"
    assert res.read_bytes() == b"public"


def test_client__download_file__data_mount__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.download_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        asset_path="dir_cell.swc",
    )
    assert res.is_symlink()
    assert res.resolve().name == "dir_cell.swc"
    assert res.read_bytes() == b"public_directory_file"
