"""Type definitions."""

import uuid
from enum import StrEnum, auto

ID = uuid.UUID


class DeploymentEnvironment(StrEnum):
    """Deployment environment."""

    staging = "staging"
    production = "production"


class ValidationStatus(StrEnum):
    """Validation status."""

    created = auto()
    initialized = auto()
    running = auto()
    done = auto()
    error = auto()
