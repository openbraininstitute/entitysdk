"""Simulation campaign model."""

from entitysdk.models.activity import Activity
from entitysdk.models.entity import Entity
from entitysdk.models.execution import Execution
from entitysdk.types import ID, CircuitExtractionExecutionStatus


class CircuitExtractionCampaign(Entity):
    """Simulation extraction campaign model."""

    scan_parameters: dict


class CircuitExtractionConfig(Entity):
    """Circuit extraction config model."""

    circuit_id: ID
    scan_parameters: dict


class CircuitExtractionConfigGeneration(Activity):
    """Circuit extraction config generation activity."""

    pass


class CircuitExtractionExecution(Execution):
    """Circuit extraction execution activity."""

    status: CircuitExtractionExecutionStatus
