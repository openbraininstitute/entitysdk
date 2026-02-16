from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from entitysdk import ProjectContext, models
from entitysdk import multipart_upload as test_module
from entitysdk.models.asset import LocalAssetMetadata
from entitysdk.schemas.asset import MultipartUploadTransferConfig, PartUpload
from entitysdk.types import AssetLabel, ContentType

ENTITY_ID = uuid4()
ENTITY_TYPE = models.CellMorphology
API_URL = "http://my-url"


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
    file_path.write_bytes(b"0123456789" * 10)  # 100 bytes
    return file_path


@pytest.fixture
def asset_metadata(asset_file):
    return LocalAssetMetadata(
        file_name=asset_file.name,
        content_type=ContentType.application_json,
        label=AssetLabel.morphology,
    )


@pytest.fixture
def project_context():
    return ProjectContext(
        virtual_lab_id=uuid4(),
        project_id=uuid4(),
    )


@pytest.fixture
def parts(fake_file):
    """Return a list of fake PartUpload objects."""
    return [
        PartUpload(part_number=1, offset=0, size=50, url="https://example.com/part1"),
        PartUpload(part_number=2, offset=50, size=50, url="https://example.com/part2"),
    ]


@pytest.fixture
def transfer_config_sequential():
    return MultipartUploadTransferConfig(
        preferred_part_count=2, use_threads=False, max_concurrency=2
    )


def test_multipart_upload_asset_file(
    asset_file, asset_metadata, project_context, token_manager, transfer_config_sequential
):

    asset_id = uuid4()

    with (
        patch("entitysdk.multipart_upload._initiate_upload", autospec=True) as mock_initiate,
        patch("entitysdk.multipart_upload._upload_parts", autospec=True) as mock_parts,
        patch("entitysdk.multipart_upload._complete_upload", autospec=True) as mock_complete,
    ):
        mock_initiate.return_value = (asset_id, [])

        test_module.multipart_upload_asset_file(
            api_url=API_URL,
            entity_id=ENTITY_ID,
            entity_type=ENTITY_TYPE,
            asset_path=asset_file,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token_manager=token_manager,
            transfer_config=transfer_config_sequential,
        )

        mock_initiate.assert_called_once()
        mock_parts.assert_called_once()
        mock_complete.assert_called_once()


def test_execute_with_retry_retries_on_exception():
    # Mock function that fails first two times, then succeeds
    mock_fn = Mock(
        side_effect=[
            test_module.RETRIABLE_EXCEPTIONS[0]("fail 1"),
            test_module.RETRIABLE_EXCEPTIONS[0]("fail 2"),
            "success",
        ]
    )

    # Patch time.sleep to avoid slowing down the test
    with patch("entitysdk.utils.execution.time.sleep", return_value=None) as mock_sleep:
        result = test_module.execute_with_retry(
            mock_fn, max_retries=3, backoff_base=0.1, retry_on=test_module.RETRIABLE_EXCEPTIONS
        )

    # The function should eventually return "success"
    assert result == "success"

    # The mock function should have been called 3 times
    assert mock_fn.call_count == 3

    # time.sleep should have been called twice (between retries)
    assert mock_sleep.call_count == 2


def test_execute_with_retry_raises_after_max_retries():
    # Function that always fails
    mock_fn = Mock(side_effect=test_module.RETRIABLE_EXCEPTIONS[0]("always fail"))

    with patch("entitysdk.utils.execution.time.sleep", return_value=None):
        with pytest.raises(test_module.RETRIABLE_EXCEPTIONS[0], match="always fail"):
            test_module.execute_with_retry(
                mock_fn, max_retries=3, backoff_base=0.1, retry_on=test_module.RETRIABLE_EXCEPTIONS
            )

    # It should try 3 times
    assert mock_fn.call_count == 3
