"""Url related utils."""

from entitysdk.config import settings
from entitysdk.types import DeploymentEnvironment


def build_api_url(environment: DeploymentEnvironment) -> str:
    """Return API url for the respective deployment environment."""
    return {
        DeploymentEnvironment.staging: settings.staging_api_url,
        DeploymentEnvironment.production: settings.production_api_url,
    }[environment]
