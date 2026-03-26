from entitysdk import util as test_module


def test_validate_filename_extension_consistency(tmp_path):
    assert test_module.validate_filename_extension_consistency(tmp_path / "foo.txt", ".txt")
    assert test_module.validate_filename_extension_consistency(tmp_path / "foo.txt", ".TXT")
