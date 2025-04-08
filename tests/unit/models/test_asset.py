from entitysdk.models import asset as test_module

from ..util import MOCK_UUID


def test_asset():
    res = test_module.Asset(
        id=MOCK_UUID,
        path="path/to/asset",
        full_path="full/path/to/asset",
        is_directory=False,
        content_type="text/plain",
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
        "content_type": "text/plain",
        "size": 100,
        "status": None,
        "sha256_digest": None,
        "meta": {},
    }


def test_local_asset_metadata():
    res = test_module.LocalAssetMetadata(
        file_name="file_name",
        content_type="text/plain",
        metadata={"key": "value"},
    )
    assert res.model_dump() == {
        "file_name": "file_name",
        "content_type": "text/plain",
        "metadata": {"key": "value"},
    }
