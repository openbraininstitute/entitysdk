"""Runtime context, execution manifest, and migration lifecycle."""

import getpass
import hashlib
import logging
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Literal

from obi_auth import get_token
from obi_auth.typedef import DeploymentEnvironment as AuthEnvironment
from pydantic import BaseModel
from rich import print as rprint

from entitysdk.client import Client
from entitysdk.migration.settings import CommonSettings
from entitysdk.migration.tracking import ExecutionSummary
from entitysdk.token_manager import TokenFromFunction, TokenManager
from entitysdk.types import DeploymentEnvironment, Token

# filename for logs and manifest, without extension
FILENAME = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

L = logging.getLogger(__name__)


class RuntimeContext(BaseModel):
    """Runtime environment metadata, computed once at startup."""

    script: str
    user: str
    command_line: list[str]
    git_remote_url: str
    git_commit: str
    git_dirty: list[str]
    script_hash: str
    uv_lock_hash: str

    @classmethod
    def collect(cls) -> "RuntimeContext":
        """Collect and return the current runtime context."""
        git_root = cls._git_root()
        script = cls._get_script_name(git_root)
        return cls(
            script=script,
            user=getpass.getuser(),
            command_line=sys.argv,
            git_remote_url=cls._git_remote_url(),
            git_commit=cls._git_commit(),
            git_dirty=cls._git_dirty(),
            script_hash=cls._get_file_hash(git_root, script),
            uv_lock_hash=cls._get_file_hash(git_root, "uv.lock"),
        )

    @staticmethod
    def _git_root() -> str:  # pragma: no cover
        return subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()  # noqa: S607

    @staticmethod
    def _git_remote_url() -> str:  # pragma: no cover
        return subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()  # noqa: S607

    @staticmethod
    def _git_commit() -> str:  # pragma: no cover
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()  # noqa: S607

    @staticmethod
    def _git_dirty() -> list[str]:  # pragma: no cover
        """Return the list of uncommitted changed files in the script's directory.

        This ignores changes in logs/ and manifests/ directories.
        """
        cmd = [
            "git",  # noqa: S607
            "diff",
            "--name-only",
            "HEAD",
            "--",
            str(script_dir()),
            ":!**/logs/",
            ":!**/manifests/",
        ]
        output = subprocess.check_output(cmd, text=True).strip()  # noqa: S603
        return output.splitlines() if output else []

    @staticmethod
    def _get_script_name(git_root: str) -> str:
        return str(Path(sys.argv[0]).resolve().relative_to(git_root))

    @staticmethod
    def _get_file_hash(git_root: str, filename: str) -> str:
        content = (Path(git_root) / filename).read_bytes()
        return hashlib.sha256(content).hexdigest()


class ExecutionManifest(BaseModel):
    """Structured audit record written after each execution."""

    version: str
    context: RuntimeContext
    settings: CommonSettings
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    outcome: Literal["success", "failure"]
    error: str | None
    summary: ExecutionSummary


def init_client(settings: CommonSettings) -> Client:
    """Initialise and return the entitysdk client."""
    token_manager: TokenManager | Token
    if settings.environment == DeploymentEnvironment.local:
        token_manager = "DISABLED"  # noqa: S105
    else:
        token_manager = TokenFromFunction(
            partial(
                get_token,
                environment=AuthEnvironment(settings.environment),
            ),
        )
    return Client(
        environment=settings.environment,
        project_context=settings.project_context,
        token_manager=token_manager,
    )


def load_manifest(path: Path) -> ExecutionManifest:
    """Load and return an execution manifest from a file path."""
    return ExecutionManifest.model_validate_json(path.read_bytes())


def script_dir() -> Path:
    """Return the directory of the main script (sys.argv[0])."""
    return Path(sys.argv[0]).resolve().parent


@contextmanager
def migration_context(
    settings: CommonSettings, *, subcommand: str, base: Path | None = None
) -> Generator[ExecutionSummary]:
    """Manage the full lifecycle of a migration script execution.

    Sets up file and console logging, collects git and runtime metadata,
    prompts the user for confirmation, and yields an ``ExecutionSummary``
    for the caller to record operations and snapshots.  On exit (whether
    successful or not) an ``ExecutionManifest`` is written to disk for
    audit purposes.

    Args:
        settings: Parsed CLI settings shared by apply/revert commands.
        subcommand: Name of the active subcommand (``"apply"`` or
            ``"revert"``), shown in the confirmation prompt.
        base: Root directory for logs and manifests.  Defaults to the
            parent directory of the running script (``sys.argv[0]``).

    Yields:
        An ``ExecutionSummary`` instance that the caller should populate
        with ``record_operation`` / ``record_snapshot`` calls.
    """
    base = base or script_dir()
    _setup_logging(settings, base)
    ctx = RuntimeContext.collect()
    L.info(f"Running {ctx.command_line} settings={settings.model_dump_json()}")
    _confirm_execution(settings, ctx, subcommand=subcommand)
    summary = ExecutionSummary()
    start_time = datetime.now(UTC)
    error = None
    try:
        yield summary
    except Exception as exc:
        error = str(exc)
        L.exception("Script failed")
        raise
    finally:
        end_time = datetime.now(UTC)
        summary.log_summary()
        _write_execution_manifest(
            settings, ctx, summary, start_time, end_time, error=error, base=base
        )


def _setup_logging(settings: CommonSettings, base: Path) -> None:
    """Configure logging to console and file.

    HTTP client loggers are capped at WARNING to prevent auth tokens
    from leaking into log files via request/response headers.
    """
    log_dir = base / settings.dir.logs / settings.environment
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{FILENAME}.log"
    logging.basicConfig(
        level=settings.log.level,
        format=settings.log.format,
        datefmt=settings.log.datefmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )
    for noisy_logger in ("urllib3", "httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    L.info(f"Log file: {log_file}")


def _confirm_execution(settings: CommonSettings, ctx: RuntimeContext, *, subcommand: str) -> None:
    """Print execution plan and require confirmation."""
    dry_run_label = "DRY-RUN" if settings.dry_run else "LIVE"
    dry_run_color = "green" if settings.dry_run else "red"
    rprint(f"\n[bold]{'=' * 60}[/]")
    rprint(f"Script      : [bold cyan]{ctx.script}[/]")
    rprint(f"Subcommand  : [bold cyan]{subcommand}[/]")
    rprint(f"Environment : [bold cyan]{settings.environment}[/]")
    rprint(f"Mode        : [bold {dry_run_color}]{dry_run_label}[/]")
    rprint(f"User        : {ctx.user}")
    rprint(f"[bold]{'=' * 60}[/]\n")
    try:
        input("Press Enter to continue or Ctrl+C to abort.")
    except KeyboardInterrupt:
        rprint("\n[bold red]Execution aborted by user[/]")
        sys.exit(1)


def _write_execution_manifest(
    settings: CommonSettings,
    ctx: RuntimeContext,
    summary: ExecutionSummary,
    start_time: datetime,
    end_time: datetime,
    *,
    error: str | None,
    base: Path,
) -> None:
    """Write a JSON execution manifest for audit purposes."""
    manifest_dir = base / settings.dir.manifests / settings.environment
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{FILENAME}.json"
    manifest = ExecutionManifest(
        version=settings.version,
        context=ctx,
        settings=settings,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=(end_time - start_time).total_seconds(),
        outcome="failure" if error else "success",
        error=error,
        summary=summary,
    )
    manifest_path.write_text(manifest.model_dump_json(indent=2))
    L.info(f"Execution manifest written to {manifest_path}")
