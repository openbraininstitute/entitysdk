"""Types definitions."""

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


class ElectricalRecordingType(StrEnum):
    """Electrical cell recording type."""

    intracellular = auto()
    extracellular = auto()
    both = auto()
    unknown = auto()


class ElectricalRecordingStimulusType(StrEnum):
    """Electrical cell recording stimulus type ."""

    voltage_clamp = auto()
    current_clamp = auto()
    conductance_clamp = auto()
    extracellular = auto()
    other = auto()
    unknown = auto()


class ElectricalRecordingStimulusShape(StrEnum):
    """Electrical cell recording stimulus shape."""

    cheops = auto()
    constant = auto()
    pulse = auto()
    step = auto()
    ramp = auto()
    noise = auto()
    sinusoidal = auto()
    other = auto()
    two_steps = auto()
    unknown = auto()


class ElectricalRecordingOrigin(StrEnum):
    """Electrical cell recording origin."""

    in_vivo = auto()
    in_vitro = auto()
    in_silico = auto()
    unknown = auto()
