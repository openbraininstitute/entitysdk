from pathlib import Path

from entitysdk.migration import settings as test_module
from entitysdk.types import DeploymentEnvironment


def test_log_settings_defaults():
    s = test_module.LogSettings()
    assert s.level == "INFO"
    assert "%(asctime)s" in s.format
    assert s.datefmt


def test_dir_settings_defaults():
    s = test_module.DirSettings()
    assert s.logs == Path("logs")
    assert s.data == Path("data")
    assert s.manifests == Path("manifests")


def test_common_settings_defaults():
    s = test_module.CommonSettings()
    assert s.version == "0.1.0"
    assert s.dry_run is True
    assert s.environment == DeploymentEnvironment.local
    assert s.project_context is None
    assert isinstance(s.log, test_module.LogSettings)
    assert isinstance(s.dir, test_module.DirSettings)


def test_apply_settings_is_common_settings():
    s = test_module.ApplySettings()
    assert isinstance(s, test_module.CommonSettings)


def test_revert_settings_has_input_manifest():
    s = test_module.RevertSettings(input_manifest=Path("/path/to/manifest.json"))
    assert s.input_manifest == Path("/path/to/manifest.json")
    assert isinstance(s, test_module.CommonSettings)
