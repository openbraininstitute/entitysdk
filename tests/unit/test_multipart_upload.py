from unittest.mock import Mock, call, patch
from uuid import uuid4

import httpx
import pytest

from entitysdk import ProjectContext, models
from entitysdk import multipart_upload as test_module
from entitysdk.models.asset import LocalAssetMetadata
from entitysdk.schemas.asset import MultipartUploadTransferConfig, PartUpload
from entitysdk.types import AssetLabel, ContentType

ENTITY_ID = uuid4()
ASSET_ID = uuid4()
ASSET_CONTENT_TYPE = ContentType.application_json
ASSET_LABEL = AssetLabel.morphology
ENTITY_TYPE = models.CellMorphology
API_URL = "http://my-url"
VIRTUAL_LAB_ID = uuid4()
PROJECT_ID = uuid4()


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


@pytest.fixture
def asset_metadata(asset_file):
    return LocalAssetMetadata(
        file_name=asset_file.name,
        content_type=ASSET_CONTENT_TYPE,
        label=ASSET_LABEL,
    )


@pytest.fixture
def asset_payload(asset_file, parts):
    return {
        "id": str(ASSET_ID),
        "content_type": ASSET_CONTENT_TYPE,
        "label": ASSET_LABEL,
        "path": asset_file.name,
        "status": "UPLOADING",
        "full_path": (
            f"/private/{VIRTUAL_LAB_ID}/{PROJECT_ID}/assets/"
            f"cell_morphology/{ENTITY_ID}/{asset_file.name}"
        ),
        "size": 200,
        "storage_type": "aws_s3_internal",
        "is_directory": False,
        "upload_meta": {
            "part_count": 2,
            "parts": [
                {
                    "part_number": 1,
                    "url": "http://part-1",
                },
                {
                    "part_number": 2,
                    "url": "http://part-2",
                },
            ],
            "part_size": 100,
        },
    }


@pytest.fixture
def project_context():
    return ProjectContext(
        virtual_lab_id=VIRTUAL_LAB_ID,
        project_id=PROJECT_ID,
    )


@pytest.fixture
def parts(asset_file):
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


@pytest.fixture
def transfer_config_threaded():
    return MultipartUploadTransferConfig(
        preferred_part_count=2, use_threads=True, max_concurrency=2
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

    with (
        patch("entitysdk.multipart_upload._initiate_upload", autospec=True) as mock_initiate,
        patch("entitysdk.multipart_upload._upload_parts", autospec=True) as mock_parts,
        patch("entitysdk.multipart_upload._complete_upload", autospec=True) as mock_complete,
    ):
        mock_initiate.return_value = (asset_id, [])

        http_client = httpx.Client()

        test_module.multipart_upload_asset_file(
            api_url=API_URL,
            entity_id=ENTITY_ID,
            entity_type=ENTITY_TYPE,
            asset_path=asset_file,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token_manager=token_manager,
            transfer_config=transfer_config_sequential,
            http_client=http_client,
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


def test_initiate_upload(asset_file, asset_metadata, project_context, httpx_mock, asset_payload):

    httpx_mock.add_response(
        url=f"http://my-url/cell-morphology/{ENTITY_ID}/assets/multipart-upload/initiate",
        json=asset_payload,
    )

    res_asset_id, res_parts = test_module._initiate_upload(
        api_url=API_URL,
        entity_id=ENTITY_ID,
        entity_type=ENTITY_TYPE,
        asset_path=asset_file,
        asset_metadata=asset_metadata,
        project_context=project_context,
        preferred_part_count=10,
        token="my-token",
        http_client=None,
    )

    assert res_asset_id == ASSET_ID
    assert len(res_parts) == 2
    assert res_parts[0].model_dump() == {
        "part_number": 1,
        "offset": 0,
        "size": 100,
        "url": "http://part-1",
    }
    assert res_parts[1].model_dump() == {
        "part_number": 2,
        "offset": 100,
        "size": 100,
        "url": "http://part-2",
    }


def test_upload_parts():

    with (
        patch("entitysdk.multipart_upload._upload_parts_threaded", autospec=True) as p_thread,
        patch("entitysdk.multipart_upload._upload_parts_sequential", autospec=True) as p_seq,
    ):
        transfer_config = MultipartUploadTransferConfig(use_threads=False)
        test_module._upload_parts(
            parts=[], file_path="foo.txt", http_client=None, transfer_config=transfer_config
        )
        p_seq.assert_called_once()

        transfer_config = MultipartUploadTransferConfig(use_threads=True)
        test_module._upload_parts(
            parts=[], file_path="foo.txt", http_client=None, transfer_config=transfer_config
        )
        p_thread.assert_called_once()


def test_send_part(httpx_mock):
    httpx_mock.add_response(
        method="PUT",
        url="http://my-url",
    )
    client = httpx.Client()
    test_module._send_part(data=b"my_data", url="http://my-url", http_client=client)


def test_complete_upload(httpx_mock, project_context, asset_payload):

    del asset_payload["upload_meta"]

    asset_payload |= {"status": "created"}

    httpx_mock.add_response(
        url=f"http://my-url/cell-morphology/{ENTITY_ID}/assets/{ASSET_ID}/multipart-upload/complete",
        json=asset_payload,
    )

    http_client = httpx.Client()

    res = test_module._complete_upload(
        api_url=API_URL,
        entity_id=ENTITY_ID,
        entity_type=ENTITY_TYPE,
        asset_id=ASSET_ID,
        project_context=project_context,
        token="my-token",
        http_client=http_client,
    )
    assert res.status == "created"


def test_upload_parts_sequential_calls_upload_part_in_order(parts, asset_file):
    http_client = httpx.Client()
    with patch("entitysdk.multipart_upload._upload_part") as mock_upload_part:
        test_module._upload_parts_sequential(
            parts=parts,
            file_path=asset_file,
            http_client=http_client,
        )

        expected_calls = [
            call(file_path=asset_file, part=part, http_client=http_client) for part in parts
        ]

        mock_upload_part.assert_has_calls(expected_calls)
        assert mock_upload_part.call_count == len(parts)


def test_upload_parts_threaded_executes_all_parts(parts, asset_file, httpx_mock):
    http_client = httpx.Client()
    with patch("entitysdk.multipart_upload._upload_part") as mock_upload_part:
        test_module._upload_parts_threaded(
            file_path=asset_file,
            parts=parts,
            http_client=http_client,
            max_concurrency=3,
        )

        assert mock_upload_part.call_count == len(parts)

        for part in parts:
            mock_upload_part.assert_any_call(asset_file, part, http_client)


@patch("entitysdk.multipart_upload._send_part")
def test_upload_part(asset_file, parts):
    http_client = httpx.Client()
    test_module._upload_part(file_path=asset_file, part=parts[0], http_client=http_client)
