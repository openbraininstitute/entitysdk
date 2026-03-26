from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from entitysdk import core as test_module
from entitysdk import models
from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset
from entitysdk.types import FetchContentStrategy, StorageType


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
