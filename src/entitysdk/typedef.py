"""Type definitions."""

import uuid
from enum import StrEnum

ID = uuid.UUID


class DeploymentEnvironment(StrEnum):
    """Deployment environment."""

    staging = "staging"
    production = "production"
