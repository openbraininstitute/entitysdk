from entitysdk.models import asset as test_module
from entitysdk.types import AssetLabel, ContentType, StorageType

from ..util import MOCK_UUID


def test_asset():
    res = test_module.Asset(
        id=MOCK_UUID,
        path="path/to/asset",
        full_path="full/path/to/asset",
        label=AssetLabel.sonata_circuit,
        is_directory=False,
        content_type=ContentType.text_plain,
        size=100,
        meta={},
    )
    assert res.model_dump() == {
        "update_date": None,
        "creation_date": None,
        "id": MOCK_UUID,
        "path": "path/to/asset",
        "full_path": "full/path/to/asset",
        "is_directory": False,
        "content_type": ContentType.text_plain,
        "size": 100,
        "status": None,
        "sha256_digest": None,
        "meta": {},
        "label": AssetLabel.sonata_circuit,
    }


def test_local_asset_metadata():
    res = test_module.LocalAssetMetadata(
        file_name="file_name",
        content_type=ContentType.text_plain,
        metadata={"key": "value"},
        label=AssetLabel.sonata_circuit,
    )
    assert res.model_dump() == {
        "file_name": "file_name",
        "content_type": ContentType.text_plain,
        "metadata": {"key": "value"},
        "label": AssetLabel.sonata_circuit,
    }


def test_existing_asset_metadata():
    res = test_module.ExistingAssetMetadata(
        path="custom_name.txt",
        full_path="path/to/original_name.txt",
        storage_type=StorageType.aws_s3_open,
        is_directory=False,
        content_type=ContentType.text_plain,
        label=AssetLabel.morphology,
    )
    assert res.model_dump() == {
        "path": "custom_name.txt",
        "full_path": "path/to/original_name.txt",
        "storage_type": StorageType.aws_s3_open,
        "is_directory": False,
        "content_type": ContentType.text_plain,
        "label": AssetLabel.morphology,
    }
