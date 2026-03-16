from pathlib import Path
from uuid import UUID

import pytest

from entitysdk import Client, ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset, CellMorphology
from entitysdk.route import get_assets_endpoint
from entitysdk.types import OutputStrategy
from entitysdk.utils.store import LocalAssetStore

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


@pytest.fixture
def public_asset_directory_file1_download_httpx_mock(
    httpx_mock,
    public_asset_file_metadata,
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
        url=f"{url}/download?asset_path=dir_cell.swc",
        method="GET",
        content=b"public_directory_file",
    )


@pytest.fixture
def public_asset_directory_file2_download_httpx_mock(
    httpx_mock, api_url, entity_type, entity_id, public_asset_directory_id
):
    url = get_assets_endpoint(
        api_url=api_url,
        asset_id=public_asset_directory_id,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    httpx_mock.add_response(
        url=f"{url}/download?asset_path=dir_cell.h5",
        method="GET",
        content=b"public_directory_file",
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
def local_store(tmp_path_factory, public_asset_file_metadata, public_asset_directory_metadata):
    prefix = tmp_path_factory.mktemp("data")

    public_file = (
        prefix
        / public_asset_file_metadata["storage_type"]
        / public_asset_file_metadata["full_path"]
    )
    public_file.parent.mkdir(parents=True, exist_ok=True)
    public_file.write_bytes(b"public")

    public_directory = (
        prefix
        / public_asset_file_metadata["storage_type"]
        / public_asset_directory_metadata["full_path"]
    )
    public_directory.mkdir(parents=True, exist_ok=True)
    Path(public_directory, "dir_cell.swc").write_bytes(b"public_directory_file")
    Path(public_directory, "dir_cell.h5").write_bytes(b"public_directory_file")

    return LocalAssetStore(prefix=prefix)


@pytest.fixture(scope="module")
def client_with_mount(api_url, local_store, project_context):
    return Client(
        api_url=api_url,
        token_manager="bar",
        local_store=local_store,
        project_context=project_context,
    )


@pytest.fixture(scope="module")
def client_wout_mount(api_url, local_store, project_context):
    return Client(
        api_url=api_url,
        token_manager="bar",
        project_context=project_context,
    )


@pytest.fixture(scope="module")
def client_with_mount__no_files(api_url, tmp_path_factory):
    prefix = tmp_path_factory.mktemp("data")
    local_store = LocalAssetStore(prefix=prefix)
    return Client(api_url=api_url, token_manager="bar", local_store=local_store)


def test_download_content__wout_mount__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_download_httpx_mock,
):
    """Test download strategy."""
    res = client_wout_mount.download_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
    )
    assert res == b"public"


def test_download_content__with_mount__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the mounted path."""
    res = client_with_mount.download_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
    )
    assert res == b"public_directory_file"


def test_download_file__with_mount__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_download_httpx_mock,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.download_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_download_file__with_mount__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"
    res = client_with_mount.download_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        asset_path="dir_cell.swc",
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_download_directory__with_mount(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
    public_asset_directory_file2_download_httpx_mock,
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
    assert not data["dir_cell.swc"].is_symlink()
    assert not data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_download_content__wout_mount__link__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the path."""
    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            asset_path="dir_cell.swc",
            output_strategy=OutputStrategy.link,
        )


def test_download_directory__with_mount__link__concurrent(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
    public_asset_directory_file2_download_httpx_mock,
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
    assert not res[0].is_symlink()
    assert not res[1].is_symlink()


def test_download_assets__with_mount(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_download_httpx_mock,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.download_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_content__wout_mount__copy_or_download__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    public_asset_directory_file1_download_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the path."""
    res = client_wout_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.copy_or_download,
    )
    assert res == b"public_directory_file"


def test_fetch_content__wout_mount__copy_or_download__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_download_httpx_mock,
):
    """Test download fallback strategy."""
    res = client_wout_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_strategy=OutputStrategy.copy_or_download,
    )
    assert res == b"public"


def test_fetch_content__wout_mount__download__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    public_asset_directory_file1_download_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the path."""
    res = client_wout_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.download,
    )
    assert res == b"public_directory_file"


def test_fetch_content__wout_mount__download__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_download_httpx_mock,
):
    """Test download strategy."""
    res = client_wout_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_strategy=OutputStrategy.download,
    )
    assert res == b"public"


def test_fetch_content__wout_mount__link__directory(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            asset_path="dir_cell.swc",
            output_strategy=OutputStrategy.link,
        )


def test_fetch_content__wout_mount__link__file(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link,
        )


def test_fetch_content__wout_mount__link_or_download__directory(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link_or_download strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            asset_path="dir_cell.swc",
            output_strategy=OutputStrategy.link_or_download,
        )


def test_fetch_content__wout_mount__link_or_download__file(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link_or_download strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link_or_download,
        )


def test_fetch_content__wout_mount__copy__directory(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            asset_path="dir_cell.swc",
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_content__wout_mount__copy__file(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test copy strategy fails if there is no mount to copy from."""
    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_content__with_mount__no_files__download(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_download_httpx_mock,
):
    """Test download."""
    res = client_with_mount__no_files.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_strategy=OutputStrategy.download,
    )
    assert res == b"public"


def test_fetch_content__with_mount__no_files__copy(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_metadata_httpx_mock,  # needed for fetching full_path for copy
):
    """Test fallback to download when copy fails."""

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_with_mount__no_files.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_content__with_mount__no_files__copy_or_download(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    public_asset_file_metadata_httpx_mock,  # needed for fetching full_path for copy
    public_asset_file_download_httpx_mock,
):
    """Test fallback to download when copy fails."""
    res = client_with_mount__no_files.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_strategy=OutputStrategy.copy_or_download,
    )
    assert res == b"public"


def test_fetch_content__with_mount__copy__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    public_asset_directory_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the mounted path."""
    res = client_with_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.copy,
    )
    assert res == b"public_directory_file"


def test_fetch_content__with_mount__link__directory(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link_or_download is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link,
            asset_path="dir_cell.swc",
        )


def test_fetch_content__with_mount__link__file(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link_or_download is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link,
        )


def test_fetch_content__with_mount__link_or_download__directory(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link_or_download is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link_or_download strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link_or_download,
            asset_path="dir_cell.swc",
        )


def test_fetch_content__with_mount__link_or_download__file(
    client_wout_mount, entity_id, entity_type, public_asset_file_id
):
    """Test link_or_download is not a valid strategy from fetch_content()."""
    with pytest.raises(EntitySDKError, match="link_or_download strategy failed"):
        client_wout_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_strategy=OutputStrategy.link_or_download,
        )


def test_fetch_content__with_mount__download__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If the asset is a directory, the asset_path is used to specify the mounted path."""
    res = client_with_mount.fetch_content(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.download,
    )
    assert res == b"public_directory_file"


def test_fetch_content__with_mount__copy__directory__no_asset_path(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_with_mount.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_file__with_mount__copy__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy,
        asset_path="dir_cell.swc",
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__copy__directory__no_asset_path(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="requires an `asset_path`"):
        client_with_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_path,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_file__with_mount__copy__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__with_mount__copy_or_download__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy_or_download,
        asset_path="dir_cell.swc",
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__copy_or_download__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy_or_download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__with_mount__download__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"
    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__download__directory__no_asset_path(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="requires an `asset_path`"):
        client_with_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_path,
            output_strategy=OutputStrategy.download,
        )


def test_fetch_file__with_mount__download__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"
    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__with_mount__link__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.link,
        asset_path="dir_cell.swc",
    )
    assert res.is_symlink()
    assert res.resolve().name == "dir_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__link__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.link,
    )
    assert res.is_symlink()
    assert res.resolve().name == "dir_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__link_or_download__directory(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.link_or_download,
        asset_path="dir_cell.swc",
    )
    assert res.is_symlink()
    assert res.resolve().name == "dir_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__with_mount__link_or_download__file(
    client_with_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.link_or_download,
    )
    assert res.is_symlink()
    assert res.resolve().name == "cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__wout_mount__copy__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_path,
            output_strategy=OutputStrategy.copy,
            asset_path="dir_cell.swc",
        )


def test_fetch_file__wout_mount__copy__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_path=output_path,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_file__wout_mount__copy_or_download__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy_or_download,
        asset_path="dir_cell.swc",
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__wout_mount__copy_or_download__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.copy_or_download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__wout_mount__download_directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If a data mount is available and link_from_store is False Client.download_file won't link."""

    output_path = tmp_path / "my_cell.swc"
    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        asset_path="dir_cell.swc",
        output_strategy=OutputStrategy.download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__wout_mount__download__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__wout_mount__link__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_path,
            output_strategy=OutputStrategy.link,
            asset_path="dir_cell.swc",
        )


def test_fetch_file__wout_mount__link__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_path,
            asset_path="dir_cell.swc",
            output_strategy=OutputStrategy.link,
        )


def test_fetch_file__wout_mount__link_or_download__directory(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_path,
        output_strategy=OutputStrategy.link_or_download,
        asset_path="dir_cell.swc",
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public_directory_file"


def test_fetch_file__wout_mount__link_or_download__file(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
):
    """If a data mount is available Client.download_file will symlink the file from there."""

    output_path = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_file(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_file_id,
        output_path=output_path,
        output_strategy=OutputStrategy.link_or_download,
    )
    assert not res.is_symlink()
    assert res.resolve().name == "my_cell.swc"
    assert res.read_bytes() == b"public"


def test_fetch_file__with_mount__no_files__copy(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,  # needed for fetching full_path for copy
):
    """Test fallback to download when copy fails."""
    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_with_mount__no_files.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_path=output_path,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_file__with_mount__no_files__link(
    client_with_mount__no_files,
    entity_id,
    entity_type,
    public_asset_file_id,
    tmp_path,
    public_asset_file_metadata_httpx_mock,  # needed for fetching full_path for copy
):
    """Test fallback to download when copy fails."""
    output_path = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_with_mount__no_files.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_file_id,
            output_path=output_path,
            output_strategy=OutputStrategy.link,
        )


def test_fetch_directory__with_mount__copy(
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

    res = client_with_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.copy,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert not data["dir_cell.swc"].is_symlink()
    assert not data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__with_mount__copy_or_download(
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

    res = client_with_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.copy_or_download,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert not data["dir_cell.swc"].is_symlink()
    assert not data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__with_mount__link(
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

    res = client_with_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.link,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert data["dir_cell.swc"].is_symlink()
    assert data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__with_mount__link_or_download(
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

    res = client_with_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.link_or_download,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert data["dir_cell.swc"].is_symlink()
    assert data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__with_mount__link__concurrent(
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

    res = client_with_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        max_concurrent=2,
        output_strategy=OutputStrategy.link,
    )
    assert len(res) == 2
    assert res[0].is_symlink()
    assert res[1].is_symlink()


def test_fetch_directory__wout_mount__copy(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_directory(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_dir,
            output_strategy=OutputStrategy.copy,
        )


def test_fetch_directory__wout_mount__copy_or_download(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
    public_asset_directory_file2_download_httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    res = client_wout_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.copy_or_download,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert not data["dir_cell.swc"].is_symlink()
    assert not data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__wout_mount__link(
    client_wout_mount,
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

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_directory(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_dir,
            output_strategy=OutputStrategy.link,
        )


def test_fetch_directory__wout_mount__link_or_download(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
    public_asset_directory_file1_download_httpx_mock,
    public_asset_directory_file2_download_httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    res = client_wout_mount.fetch_directory(
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=public_asset_directory_id,
        output_path=output_dir,
        output_strategy=OutputStrategy.link_or_download,
    )
    data = {r.name: r for r in res}
    assert len(res) == 2
    assert not data["dir_cell.swc"].is_symlink()
    assert not data["dir_cell.h5"].is_symlink()
    assert data["dir_cell.swc"].resolve().name == "dir_cell.swc"
    assert data["dir_cell.h5"].resolve().name == "dir_cell.h5"


def test_fetch_directory__wout_mount__link__concurrent(
    client_wout_mount,
    entity_id,
    entity_type,
    public_asset_directory_id,
    tmp_path,
    public_asset_directory_httpx_mock,
    public_asset_directory_list_httpx_mock,
):
    output_dir = tmp_path / "directory"
    output_dir.mkdir()

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_directory(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=public_asset_directory_id,
            output_path=output_dir,
            max_concurrent=2,
            output_strategy=OutputStrategy.link,
        )


def test_fetch_assets__with_mount__copy(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.copy,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__with_mount__copy_or_download(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.copy_or_download,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__with_mount__download(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_download_httpx_mock,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.download,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__with_mount__link(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.link,
    ).one()

    assert res.path.is_symlink()
    assert res.path.resolve().name == "cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__with_mount__link_or_download(
    client_with_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_with_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.link_or_download,
    ).one()

    assert res.path.is_symlink()
    assert res.path.resolve().name == "cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__wout_mount__copy(
    client_wout_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="copy strategy failed"):
        client_wout_mount.fetch_assets(
            entity_or_id=entity,
            selection={"label": "morphology", "content_type": "application/swc"},
            output_path=output_file,
            output_strategy=OutputStrategy.copy,
        ).one()


def test_fetch_assets__wout_mount__copy_or_download(
    client_wout_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.copy_or_download,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__wout_mount__download(
    client_wout_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_download_httpx_mock,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.download,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"


def test_fetch_assets__wout_mount__link(
    client_wout_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    with pytest.raises(EntitySDKError, match="link strategy failed"):
        client_wout_mount.fetch_assets(
            entity_or_id=entity,
            selection={"label": "morphology", "content_type": "application/swc"},
            output_path=output_file,
            output_strategy=OutputStrategy.link,
        ).one()


def test_fetch_assets__wout_mount__link_or_download(
    client_wout_mount,
    entity_id,
    entity_type,
    tmp_path,
    public_asset_file_metadata_httpx_mock,
    public_asset_file_download_httpx_mock,
    entity,
):
    output_file = tmp_path / "my_cell.swc"

    res = client_wout_mount.fetch_assets(
        entity_or_id=entity,
        selection={"label": "morphology", "content_type": "application/swc"},
        output_path=output_file,
        output_strategy=OutputStrategy.link_or_download,
    ).one()

    assert not res.path.is_symlink()
    assert res.path.resolve().name == "my_cell.swc"
    assert res.path.read_bytes() == b"public"
