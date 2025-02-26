from entitysdk.models import asset as test_module


def test_asset():
    res = test_module.Asset(
        id=1,
        path="path/to/asset",
        fullpath="full/path/to/asset",
        bucket_name="bucket_name",
        is_directory=False,
        content_type="text/plain",
        size=100,
        meta={},
    )
    assert res.model_dump() == {
        "update_date": None,
        "creation_date": None,
        "id": 1,
        "path": "path/to/asset",
        "fullpath": "full/path/to/asset",
        "bucket_name": "bucket_name",
        "is_directory": False,
        "content_type": "text/plain",
        "size": 100,
        "status": None,
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
