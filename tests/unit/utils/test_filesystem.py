import pytest

from entitysdk.utils.filesystem import create_dir, get_filesize


def test_create_dir(tmp_path):
    """Test creating a directory with create_dir function."""
    assert create_dir(tmp_path / "test_dir").is_dir() is True


def test_get_filesize_existing_file(tmp_path):
    file = tmp_path / "test.txt"
    content = b"hello world"
    file.write_bytes(content)

    assert get_filesize(file) == len(content)


def test_get_filesize_empty_file(tmp_path):
    file = tmp_path / "empty.txt"
    file.touch()

    assert get_filesize(file) == 0


def test_get_filesize_nonexistent_file(tmp_path):
    file = tmp_path / "missing_1.txt"

    with pytest.raises(FileNotFoundError):
        get_filesize(file)


def test_get_filesize_nonexistent_path(tmp_path):
    file_path = tmp_path / "missing_2.txt"

    with pytest.raises(FileNotFoundError, match="does not exist"):
        get_filesize(file_path)


def test_get_filesize_directory(tmp_path):
    dir_path = tmp_path / "subdir"
    dir_path.mkdir()

    with pytest.raises(IsADirectoryError, match="is not a file"):
        get_filesize(dir_path)


def test_get_filesize_with_string_path(tmp_path):
    file_path = tmp_path / "string_path.txt"
    content = b"abc"
    file_path.write_bytes(content)

    size = get_filesize(str(file_path))
    assert size == len(content)
