"""CLI settings models."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from pydantic_settings import CliPositionalArg

from entitysdk.common import ProjectContext
from entitysdk.types import DeploymentEnvironment


class LogSettings(BaseModel):
    """Logging configuration."""

    level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        Field(description="Logging level"),
    ] = "INFO"
    format: Annotated[str, Field(description="Log format")] = (
        "%(asctime)s %(levelname)-8s %(message)s"
    )
    datefmt: Annotated[str, Field(description="Log format to be used for the timestamps")] = (
        "%Y-%m-%d %H:%M:%S %z"
    )


class DirSettings(BaseModel):
    """Directory paths, resolved relative to the main script's directory."""

    logs: Annotated[Path, Field(description="Log files directory")] = Path("logs")
    data: Annotated[Path, Field(description="Data files directory")] = Path("data")
    manifests: Annotated[Path, Field(description="Execution manifests directory")] = Path(
        "manifests"
    )


class CommonSettings(BaseModel):
    """Base settings shared by apply and revert commands."""

    version: Annotated[str, Field(description="Migration script version")] = "0.1.0"
    log: Annotated[LogSettings, Field(description="Logging configuration")] = LogSettings()
    dir: Annotated[DirSettings, Field(description="Directory configuration")] = DirSettings()
    dry_run: Annotated[bool, Field(description="If true, execute the script in dry-run mode")] = (
        True
    )
    environment: Annotated[DeploymentEnvironment, Field(description="Execution environment")] = (
        DeploymentEnvironment.local
    )
    project_context: Annotated[
        ProjectContext | None, Field(description="Default project context")
    ] = None


class ApplySettings(CommonSettings):
    """Default settings for the apply command."""


class RevertSettings(CommonSettings):
    """Settings for the revert command, adding the input manifest path."""

    input_manifest: Annotated[
        CliPositionalArg[Path],
        Field(description="Path to the manifest file of the migration to be reverted."),
    ]
