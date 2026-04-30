"""Migration library: shared infrastructure for entitycore migration scripts."""

from entitysdk.migration.cli import run
from entitysdk.migration.context import ExecutionManifest, init_client, load_manifest, script_dir
from entitysdk.migration.settings import ApplySettings, CommonSettings, RevertSettings
from entitysdk.migration.tracking import (
    EntityKey,
    ExecutionSummary,
    OperationType,
    SnapshotLabel,
)

__all__ = [
    "ApplySettings",
    "CommonSettings",
    "EntityKey",
    "ExecutionManifest",
    "ExecutionSummary",
    "OperationType",
    "RevertSettings",
    "SnapshotLabel",
    "init_client",
    "load_manifest",
    "run",
    "script_dir",
]
