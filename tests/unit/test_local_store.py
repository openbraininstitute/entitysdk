from pathlib import Path

import pytest

from entitysdk import store as test_module
from entitysdk.exception import EntitySDKError


def test_prefix_raises():
    with pytest.raises(EntitySDKError, match="does not exist"):
        test_module.LocalAssetStore("/foo")


@pytest.fixture(scope="module")
def local_store(tmp_path_factory):
    prefix = tmp_path_factory.mktemp("data")

    path = prefix / "file1.txt"
    path.write_bytes(b"file1")

    directory = prefix / "directory"
    directory.mkdir(parents=True, exist_ok=True)
    Path(directory, "file2.txt").write_bytes(b"file2")

    return test_module.LocalAssetStore(prefix=prefix)


def test_path_exists(local_store):
    assert local_store.path_exists("file1.txt")
    assert local_store.path_exists("directory")
    assert local_store.path_exists("directory/file2.txt")


def test_link_path(local_store, tmp_path):
    ofile1 = tmp_path / "my_file1.txt"
    local_store.link_path("file1.txt", ofile1)
    assert ofile1.is_symlink()
    assert ofile1.resolve() == local_store.prefix / "file1.txt"
    assert ofile1.read_bytes() == b"file1"


def test_read_bytes(local_store):
    assert local_store.read_bytes("file1.txt") == b"file1"
    assert local_store.read_bytes("directory/file2.txt") == b"file2"
