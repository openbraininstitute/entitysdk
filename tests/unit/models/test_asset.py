from entitysdk.models import asset as test_module


def test_asset():
    asset = test_module.Asset(
        id=1,
        path="path/to/asset",
        fullpath="full/path/to/asset",
        bucket_name="bucket_name",
        is_directory=False,
        content_type="text/plain",
        size=100,
        meta={},
    )
    assert asset.id == 1
    assert asset.path == "path/to/asset"
    assert asset.fullpath == "full/path/to/asset"
    assert asset.bucket_name == "bucket_name"
    assert not asset.is_directory
    assert asset.content_type == "text/plain"
    assert asset.size == 100
    assert asset.meta == {}


def test_local_asset():
    local_asset = test_module.LocalAsset(
        filename="asset.txt",
        content_type="text/plain",
        path_or_bytes="asset.txt",
    )
    assert local_asset.filename == "asset.txt"
    assert local_asset.content_type == "text/plain"
    assert local_asset.path_or_bytes == "asset.txt"
