from pathlib import Path
from uuid import UUID

import pytest

from entitysdk import Client, ProjectContext
from entitysdk.models import Asset, CellMorphology
from entitysdk.mount import DataMount
from entitysdk.route import get_assets_endpoint

MOCK_DATE = "2025-11-07 13:59:27.938208+00:00"


@pytest.fixture(scope="module")
def virtual_lab_id():
    return UUID(int=10)


@pytest.fixture(scope="module")
def project_id():
    return UUID(int=20)


@pytest.fixture(scope="module")
def project_context(virtual_lab_id, project_id):
    return ProjectContext(virtual_lab_id=virtual_lab_id, project_id=project_id)


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
def public_asset_file_metadata_httpx_mock(
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


@pytest.fixture
def public_asset_file_download_httpx_mock(
    httpx_mock, public_asset_file_metadata, api_url, entity_type, entity_id, public_asset_file_id
):
    url = get_assets_endpoint(
        api_url=api_url,
        asset_id=public_asset_file_id,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    httpx_mock.add_response(
        url=f"{url}/download",
        method="GET",
        content=b"public",
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


@pytest.fixture
def public_asset_directory_list_httpx_mock(
    httpx_mock,
    public_asset_directory_metadata,
    api_url,
    entity_type,
    entity_id,
    public_asset_directory_id,
):
    url = get_assets_endpoint(
        api_url=api_url,
        asset_id=public_asset_directory_id,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    httpx_mock.add_response(
        url=f"{url}/list",
        method="GET",
        json={
            "files": {
                "dir_cell.swc": {
                    "name": "dir_cell.swc",
                    "size": 0,
                    "last_modified": MOCK_DATE,
                },
                "dir_cell.h5": {"name": "dir_cell.h5", "size": 0, "last_modified": str(MOCK_DATE)},
            }
        },
    )


@pytest.fixture(scope="module")
def entity(entity_id, public_asset_file_metadata, public_asset_directory_metadata):
    return CellMorphology(
        id=entity_id,
        name="morphology",
        description="morphology",
        assets=[
            Asset(**public_asset_file_metadata),
            Asset(**public_asset_directory_metadata),
        ],
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
    Path(public_directory, "dir_cell.h5").write_bytes(b"public_directory_file")

    return DataMount(prefix=prefix)


@pytest.fixture(scope="module")
def client_with_mount(api_url, data_mount, project_context):
    return Client(
        api_url=api_url,
        token_manager="bar",
        data_mount=data_mount,
        project_context=project_context,
    )


@pytest.fixture(scope="module")
def client_with_mount__no_files(api_url, tmp_path_factory):
    prefix = tmp_path_factory.mktemp("data")
    data_mount = DataMount(prefix=prefix)
    return Client(api_url=api_url, token_manager="bar", data_mount=data_mount)


def test_client__download_content__data_mount__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available Client.download_content will fetch the bytes from there."""

    res = client_with_mount.download_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
    )
    assert res == b"public"


def test_client__download_content__data_mount__no_file(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
):
    res = client_with_mount__no_files.download_content(
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
    public_asset_file_metadata_httpx_mock,
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


def test_client__download_directory__data_mount(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    res = client_with_mount.download_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert data["dir_cell.swc"].is_symlink()
    assert data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_client__download_directory__data_mount__concurrent(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    res = client_with_mount.download_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        max_concurrent=2,
    )
    assert len(res) == 2
    assert res[0].is_symlink()
    assert res[1].is_symlink()


def test_client__download_assets__data_mount(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.download_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
    ).one()

    assert res.path.is_symlink()
    assert res.path.resolve().name == "cell.swc"
    assert res.path.read_bytes() == b"public"
