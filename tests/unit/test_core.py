from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from entitysdk import core as test_module
from entitysdk import models


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
