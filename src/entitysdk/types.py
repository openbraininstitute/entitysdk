"""Types definitions."""

import os
import uuid
from enum import StrEnum, auto

ID = uuid.UUID
Token = str
StrOrPath = str | os.PathLike[str]


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


class SingleNeuronSimulationStatus(StrEnum):
    """Single neuron simulation status."""

    started = auto()
    failure = auto()
    success = auto()


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


class CircuitBuildCategory(StrEnum):
    """Information about how/from what source a circuit was built.

    - computational_model: Any type of data-driven or statistical model
    - em_reconstruction: Reconstruction from EM
    (More categories may be added later, if needed).
    """

    computational_model = auto()
    em_reconstruction = auto()


class CircuitScale(StrEnum):
    """Scale of the circuit.

    - single: Single neuron + extrinsic connectivity
    - pair: Two connected neurons + intrinsic connectivity + extrinsic connectivity
    - small: Small microcircuit (3-20 neurons) + intrinsic connectivity + extrinsic connectivity;
      usually containing specific connectivity motifs
    - microcircuit: Any circuit larger than 20 neurons but not being a region, system, or
      whole-brain circuit; may be atlas-based or not
    - region: Atlas-based continuous volume of an entire brain region or a set of continuous
      sub-regions
    - system: Non-continuous circuit consisting of at least two microcircuits/regions that are
      connected by inter-region connectivity
    - whole_brain: Circuit representing an entire brain.
    """

    single = auto()
    pair = auto()
    small = auto()
    microcircuit = auto()
    region = auto()
    system = auto()
    whole_brain = auto()


class SimulationExecutionStatus(StrEnum):
    """Simulation execution activity status."""

    created = auto()
    pending = auto()
    running = auto()
    done = auto()
    error = auto()


class ContentType(StrEnum):
    """Content types."""

    json = "application/json"
