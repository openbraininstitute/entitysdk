"""Utility functions."""

from pathlib import Path

from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.types import DeploymentEnvironment


def build_api_url(environment: DeploymentEnvironment) -> str:
    """Return API url for the respective deployment environment."""
    return {
        DeploymentEnvironment.staging: settings.staging_api_url,
        DeploymentEnvironment.production: settings.production_api_url,
    }[environment]


def validate_filename_extension_consistency(path: Path, expected_extension: str) -> Path:
    """Validate file path extension against expected extension."""
    if path.suffix.lower() == expected_extension.lower():
        return path
    raise EntitySDKError(f"File path {path} does not have expected extension {expected_extension}.")
