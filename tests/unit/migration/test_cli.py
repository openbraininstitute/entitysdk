from contextlib import contextmanager

from entitysdk.migration import cli as test_module
from entitysdk.migration.settings import ApplySettings, RevertSettings
from entitysdk.migration.tracking import ExecutionSummary


@contextmanager
def _fake_migration_context(*_args, **_kwargs):
    yield ExecutionSummary()


def test_run_apply_subcommand(monkeypatch):
    calls = []

    monkeypatch.setattr(test_module, "migration_context", _fake_migration_context)
    test_module.run(
        apply=lambda settings, summary: calls.append(("apply", settings, summary)),
        revert=lambda *a: None,
        cli_args=["apply"],
    )

    assert len(calls) == 1
    assert isinstance(calls[0][1], ApplySettings)
    assert isinstance(calls[0][2], ExecutionSummary)


def test_run_revert_subcommand(monkeypatch, tmp_path):
    calls = []
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}")

    monkeypatch.setattr(test_module, "migration_context", _fake_migration_context)
    test_module.run(
        apply=lambda *a: None,
        revert=lambda settings, summary: calls.append(("revert", settings, summary)),
        cli_args=["revert", str(manifest_path)],
    )

    assert len(calls) == 1
    assert isinstance(calls[0][1], RevertSettings)
    assert calls[0][1].input_manifest == manifest_path


def test_run_custom_settings_types(monkeypatch):
    class MyApplySettings(ApplySettings):
        extra_flag: bool = False

    calls = []

    monkeypatch.setattr(test_module, "migration_context", _fake_migration_context)
    test_module.run(
        apply=lambda settings, summary: calls.append(settings),
        apply_settings=MyApplySettings,
        revert=lambda *a: None,
        cli_args=["apply"],
    )

    assert len(calls) == 1
    assert isinstance(calls[0], MyApplySettings)
