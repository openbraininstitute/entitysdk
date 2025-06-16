"""Simulation execution model."""

from entitysdk.models.activity import Activity
from entitysdk.types import SimulationExecutionStatus


class SimulationExecution(Activity):
    """Simulation execution model."""

    status: SimulationExecutionStatus
