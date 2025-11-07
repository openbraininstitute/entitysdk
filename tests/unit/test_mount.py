from pathlib import Path

import pytest

from entitysdk import mount as test_module
from entitysdk.exception import EntitySDKError


def test_prefix_raises():
    with pytest.raises(EntitySDKError, match="does not exist"):
        test_module.DataMount("/foo")


@pytest.fixture(scope="module")
def data_mount(tmp_path_factory):
    prefix = tmp_path_factory.mktemp("data")

    path = prefix / "file1.txt"
    path.write_bytes(b"file1")

    directory = prefix / "directory"
    directory.mkdir(parents=True, exist_ok=True)
    Path(directory, "file2.txt").write_bytes(b"file2")

    return test_module.DataMount(prefix=prefix)


def test_path_exists(data_mount):
    assert data_mount.path_exists("file1.txt")
    assert data_mount.path_exists("directory")
    assert data_mount.path_exists("directory/file2.txt")


def test_link_path(data_mount, tmp_path):
    ofile1 = tmp_path / "my_file1.txt"
    data_mount.link_path("file1.txt", ofile1)
    assert ofile1.is_symlink()
    assert ofile1.resolve() == data_mount.prefix / "file1.txt"
    assert ofile1.read_bytes() == b"file1"


def test_read_bytes(data_mount):
    assert data_mount.read_bytes("file1.txt") == b"file1"
    assert data_mount.read_bytes("directory/file2.txt") == b"file2"
