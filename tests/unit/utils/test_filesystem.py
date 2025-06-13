from entitysdk.utils.filesystem import create_dir


def test_create_dir():
    """Test creating a directory with create_dir function."""
    assert create_dir("test_dir").is_dir() is True
