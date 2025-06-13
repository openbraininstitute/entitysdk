from entitysdk.utils.filesystem import create_dir


def test_create_dir(tmp_path):
    """Test creating a directory with create_dir function."""
    assert create_dir(tmp_path / "test_dir").is_dir() is True
