from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx
import pytest

from entitysdk import core as test_module
from entitysdk import models
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset
from entitysdk.types import FetchContentStrategy, FetchFileStrategy, StorageType


@pytest.fixture
def token_manager():
    class TokenManager:
        def get_token(self):
            return "my-token"

    return TokenManager()


@pytest.fixture
def asset_file(tmp_path):
    """Create a temporary file with dummy content."""
    file_path = tmp_path / "test_asset.json"
    # 20 bytes repeated 10 times = 200 bytes
    file_path.write_bytes(b"01234567890123456789" * 10)
    return file_path


def test_upload_asset_file(asset_file, token_manager):

    transfer_config = Mock()
    transfer_config.threshold = 100

    with (
        patch("entitysdk.core.get_filesize", return_value=101, autospec=True),
        patch("entitysdk.core.upload_asset_content", autospec=True) as patched_content,
    ):
        test_module.upload_asset_file(
            api_url="my-url",
            entity_id=uuid4(),
            entity_type=models.CellMorphology,
            project_context=None,
            token_manager=token_manager,
            asset_path=asset_file,
            asset_metadata=None,
        )
        patched_content.assert_called_once()

    with (
        patch("entitysdk.core.get_filesize", return_value=99, autospec=True),
        patch("entitysdk.core.upload_asset_content", autospec=True) as patched_content,
    ):
        test_module.upload_asset_file(
            api_url="my-url",
            entity_id=uuid4(),
            entity_type=models.CellMorphology,
            project_context=None,
            token_manager=token_manager,
            asset_path=asset_file,
            asset_metadata=None,
            transfer_config=transfer_config,
        )
        patched_content.assert_called_once()

    with (
        patch("entitysdk.core.get_filesize", return_value=101, autospec=True),
        patch("entitysdk.core.multipart_upload_asset_file", autospec=True) as patched_file,
    ):
        test_module.upload_asset_file(
            api_url="my-url",
            entity_id=uuid4(),
            entity_type=models.CellMorphology,
            project_context=None,
            token_manager=token_manager,
            asset_path=asset_file,
            asset_metadata=None,
            transfer_config=transfer_config,
        )
        patched_file.assert_called_once()


def test_fetch_asset_content_copy_or_download_reads_from_store_when_asset_is_provided():
    entity_id = uuid4()
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    store = Mock()
    store.path_exists.return_value = True
    store.read_bytes.return_value = b"from-store"

    content = test_module.fetch_asset_content(
        api_url="http://mock-host:8000",
        entity_id=entity_id,
        entity_type=models.Entity,
        asset_or_id=asset,
        token="my-token",
        local_store=store,
        strategy=FetchContentStrategy.local_or_download,
    )

    assert content == b"from-store"
    store.read_bytes.assert_called_once()


def test_fetch_asset_file_download_streams_to_disk(tmp_path):
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.bin",
        full_path="/foo/foo.bin",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    with (
        patch(
            "entitysdk.core.fetch_asset_content", side_effect=AssertionError("should not be called")
        ),
        patch("entitysdk.core.download_asset_file", autospec=True) as download_asset_file,
    ):

        def _write(*, target_path, **_kwargs):
            target_path.write_bytes(b"abcdef")
            return target_path

        download_asset_file.side_effect = _write
        out = test_module.fetch_asset_file(
            api_url="http://mock-host:8000",
            entity_id=uuid4(),
            entity_type=models.Entity,
            asset_or_id=asset,
            output_path=tmp_path,
            token="my-token",
            strategy=FetchFileStrategy.download_only,
        )

    assert out.read_bytes() == b"abcdef"
    download_asset_file.assert_called_once()


def test_fetch_asset_file_download_stream_sets_context_headers(tmp_path):
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    ctx = ProjectContext(
        project_id="f373e771-3a2f-4f45-ab59-0955efd7b1f4",
        virtual_lab_id="ff888f05-f314-4702-8a92-b86f754270bb",
    )

    with patch("entitysdk.core.download_asset_file", autospec=True) as download_asset_file:

        def _write(*, target_path, **_kwargs):
            target_path.write_text("x")
            return target_path

        download_asset_file.side_effect = _write
        out = test_module.fetch_asset_file(
            api_url="http://mock-host:8000",
            entity_id=uuid4(),
            entity_type=models.Entity,
            asset_or_id=asset,
            output_path=tmp_path,
            token="my-token",
            project_context=ctx,
            strategy=FetchFileStrategy.download_only,
        )

    assert out.read_text() == "x"
    _, kwargs = download_asset_file.call_args
    assert kwargs["token"] == "my-token"  # noqa: S105
    assert kwargs["project_context"] == ctx


def test_fetch_asset_file_download_request_error_raises(tmp_path):
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    err = EntitySDKError("Request error: boom")
    with patch("entitysdk.core.download_asset_file", side_effect=err):
        with pytest.raises(EntitySDKError, match="Request error: boom"):
            test_module.fetch_asset_file(
                api_url="http://mock-host:8000",
                entity_id=uuid4(),
                entity_type=models.Entity,
                asset_or_id=asset,
                output_path=tmp_path,
                token="my-token",
                strategy=FetchFileStrategy.download_only,
            )


def test_fetch_asset_file_download_http_status_error_raises(tmp_path):
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    err = EntitySDKError("HTTP error 404 for GET http://mock-host:8000/entity/x/assets/y/download")
    with patch("entitysdk.core.download_asset_file", side_effect=err):
        with pytest.raises(EntitySDKError, match="HTTP error 404 for GET"):
            test_module.fetch_asset_file(
                api_url="http://mock-host:8000",
                entity_id=uuid4(),
                entity_type=models.Entity,
                asset_or_id=asset,
                output_path=tmp_path,
                token="my-token",
                strategy=FetchFileStrategy.download_only,
            )


def test_fetch_asset_file_unsupported_strategy_raises(tmp_path):
    entity_id = uuid4()
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    with pytest.raises(EntitySDKError, match="Unsupported strategy"):
        test_module.fetch_asset_file(
            api_url="http://mock-host:8000",
            entity_id=entity_id,
            entity_type=models.Entity,
            asset_or_id=asset,
            output_path=tmp_path / "out.txt",
            token="my-token",
            strategy="unsupported-strategy",
        )


def test_fetch_asset_content_unsupported_strategy_raises():
    entity_id = uuid4()
    asset_id = uuid4()
    asset = Asset(
        id=asset_id,
        path="foo.txt",
        full_path="/foo/foo.txt",
        storage_type=StorageType.aws_s3_internal,
        is_directory=False,
        content_type="text/plain",
        label="morphology",
        size=1,
        status="created",
    )

    with pytest.raises(EntitySDKError, match="Unsupported strategy"):
        test_module.fetch_asset_content(
            api_url="http://mock-host:8000",
            entity_id=entity_id,
            entity_type=models.Entity,
            asset_or_id=asset,
            token="my-token",
            strategy="unsupported-strategy",
        )


def test_download_asset_file_without_project_context(tmp_path, httpx_mock):
    out = tmp_path / "downloaded.bin"
    endpoint = "http://mock-host:8000/entity/e1/assets/a1"
    httpx_mock.add_response(
        method="GET",
        url=f"{endpoint}/download",
        match_headers={"Authorization": "Bearer my-token"},
        content=b"payload",
    )

    with httpx.Client() as client:
        res = test_module.download_asset_file(
            asset_endpoint=endpoint,
            target_path=out,
            token="my-token",
            project_context=None,
            http_client=client,
        )

    assert res == out
    assert out.read_bytes() == b"payload"


def test_download_asset_file_project_context_without_virtual_lab_id(tmp_path, httpx_mock):
    out = tmp_path / "downloaded.bin"
    endpoint = "http://mock-host:8000/entity/e1/assets/a1"
    ctx = ProjectContext(project_id="f373e771-3a2f-4f45-ab59-0955efd7b1f4")
    httpx_mock.add_response(
        method="GET",
        url=f"{endpoint}/download",
        match_headers={
            "Authorization": "Bearer my-token",
            "project-id": str(ctx.project_id),
        },
        content=b"z",
    )

    with httpx.Client() as client:
        res = test_module.download_asset_file(
            asset_endpoint=endpoint,
            target_path=out,
            token="my-token",
            project_context=ctx,
            http_client=client,
        )

    assert res == out
    assert out.read_bytes() == b"z"


def test_download_asset_file_with_asset_path_query(tmp_path, httpx_mock):
    out = tmp_path / "nested.txt"
    endpoint = "http://mock-host:8000/entity/e1/assets/a1"
    httpx_mock.add_response(
        method="GET",
        url=f"{endpoint}/download?asset_path=sub%2Ffile.txt",
        match_headers={"Authorization": "Bearer my-token"},
        content=b"inner",
    )

    with httpx.Client() as client:
        res = test_module.download_asset_file(
            asset_endpoint=endpoint,
            target_path=out,
            token="my-token",
            project_context=None,
            http_client=client,
            asset_path=Path("sub/file.txt"),
        )

    assert res == out
    assert out.read_bytes() == b"inner"


def test_download_asset_file_skips_empty_chunks(tmp_path):
    out = tmp_path / "out.bin"

    def _fake_stream(**_kwargs):
        yield b""
        yield b"ab"

    with patch("entitysdk.core.stream_response", side_effect=_fake_stream):
        with httpx.Client() as client:
            res = test_module.download_asset_file(
                asset_endpoint="http://mock-host:8000/x",
                target_path=out,
                token="t",
                http_client=client,
            )

    assert res == out
    assert out.read_bytes() == b"ab"
