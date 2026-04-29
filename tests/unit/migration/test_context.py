import builtins
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from entitysdk.common import ProjectContext
from entitysdk.migration import context as test_module
from entitysdk.migration.settings import CommonSettings
from entitysdk.migration.tracking import EntityKey, ExecutionSummary, OperationType
from entitysdk.types import DeploymentEnvironment
from tests.unit.util import PROJECT_ID, VIRTUAL_LAB_ID


@pytest.fixture()
def common_settings():
    return CommonSettings(
        environment=DeploymentEnvironment.local,
        project_context=ProjectContext(project_id=PROJECT_ID, virtual_lab_id=VIRTUAL_LAB_ID),
    )


@pytest.fixture()
def runtime_context():
    return test_module.RuntimeContext(
        script="migrations/001/run.py",
        user="testuser",
        command_line=["run.py", "apply"],
        git_remote_url="https://github.com/org/repo.git",
        git_commit="abc123",
        git_dirty=[],
        script_hash="aaa",
        uv_lock_hash="bbb",
    )


@pytest.fixture()
def _patch_git(monkeypatch, tmp_path):
    monkeypatch.setattr(
        test_module.RuntimeContext, "_git_root", staticmethod(lambda: str(tmp_path))
    )
    monkeypatch.setattr(
        test_module.RuntimeContext,
        "_git_remote_url",
        staticmethod(lambda: "https://github.com/org/repo.git"),
    )
    monkeypatch.setattr(test_module.RuntimeContext, "_git_commit", staticmethod(lambda: "abc123"))
    monkeypatch.setattr(test_module.RuntimeContext, "_git_dirty", staticmethod(lambda: []))


@pytest.fixture()
def _patch_migration_context(monkeypatch, runtime_context):
    monkeypatch.setattr(
        test_module.RuntimeContext, "collect", staticmethod(lambda: runtime_context)
    )
    monkeypatch.setattr(test_module, "_setup_logging", lambda *a, **kw: None)
    monkeypatch.setattr(test_module, "_confirm_execution", lambda *a, **kw: None)


@pytest.mark.usefixtures("_patch_git")
def test_runtime_context_collect(tmp_path, monkeypatch):
    script = tmp_path / "migrations" / "001" / "run.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('hello')")
    (tmp_path / "uv.lock").write_text("lockfile")

    monkeypatch.setattr(sys, "argv", [str(script), "apply"])

    ctx = test_module.RuntimeContext.collect()

    assert ctx.script == "migrations/001/run.py"
    assert ctx.git_commit == "abc123"
    assert ctx.git_dirty == []
    assert ctx.script_hash
    assert ctx.uv_lock_hash


def test_load_manifest(tmp_path, common_settings, runtime_context):
    now = datetime.now(UTC)
    manifest = test_module.ExecutionManifest(
        version="0.1.0",
        context=runtime_context,
        settings=common_settings,
        start_time=now,
        end_time=now,
        duration_seconds=0.0,
        outcome="success",
        error=None,
        summary=ExecutionSummary(),
    )
    path = tmp_path / "manifest.json"
    path.write_text(manifest.model_dump_json())
    loaded = test_module.load_manifest(path)
    assert loaded.outcome == "success"
    assert loaded.error is None


def test_init_client_local(common_settings):
    client = test_module.init_client(common_settings)
    assert client is not None


def test_init_client_non_local(monkeypatch, common_settings):
    common_settings.environment = DeploymentEnvironment.staging
    monkeypatch.setattr(test_module, "get_token", lambda **kw: "fake-token")
    client = test_module.init_client(common_settings)
    assert client is not None


def test_script_dir(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["/some/path/script.py"])
    assert test_module.script_dir() == Path("/some/path")


@pytest.mark.usefixtures("_patch_migration_context")
def test_migration_context_success(tmp_path, common_settings):
    with test_module.migration_context(
        common_settings, subcommand="apply", base=tmp_path
    ) as summary:
        summary.record_operation(
            EntityKey(type="X", id=PROJECT_ID),
            OperationType.created,
        )

    manifest_dir = tmp_path / "manifests" / "local"
    manifests = list(manifest_dir.glob("*.json"))
    assert len(manifests) == 1
    loaded = test_module.load_manifest(manifests[0])
    assert loaded.outcome == "success"


@pytest.mark.usefixtures("_patch_migration_context")
def test_migration_context_failure(tmp_path, common_settings):
    with pytest.raises(RuntimeError, match="boom"):
        with test_module.migration_context(common_settings, subcommand="apply", base=tmp_path):
            raise RuntimeError("boom")

    manifest_dir = tmp_path / "manifests" / "local"
    manifests = list(manifest_dir.glob("*.json"))
    assert len(manifests) == 1
    loaded = test_module.load_manifest(manifests[0])
    assert loaded.outcome == "failure"
    assert loaded.error == "boom"


def test_setup_logging_creates_log_dir(tmp_path, common_settings):
    common_settings.dir.logs = Path("test_logs")
    test_module._setup_logging(common_settings, tmp_path)
    log_dir = tmp_path / "test_logs" / str(common_settings.environment)
    assert log_dir.exists()


def test_confirm_execution_continue(monkeypatch, common_settings, runtime_context):
    monkeypatch.setattr(builtins, "input", lambda *a: "")
    test_module._confirm_execution(common_settings, runtime_context, subcommand="apply")


def test_confirm_execution_abort(monkeypatch, common_settings, runtime_context):
    def raise_keyboard_interrupt(*a):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", raise_keyboard_interrupt)
    with pytest.raises(SystemExit):
        test_module._confirm_execution(common_settings, runtime_context, subcommand="apply")


def test_write_execution_manifest(tmp_path, common_settings, runtime_context):
    now = datetime.now(UTC)
    test_module._write_execution_manifest(
        common_settings,
        runtime_context,
        ExecutionSummary(),
        now,
        now,
        error=None,
        base=tmp_path,
    )
    manifest_dir = tmp_path / "manifests" / str(common_settings.environment)
    manifests = list(manifest_dir.glob("*.json"))
    assert len(manifests) == 1
