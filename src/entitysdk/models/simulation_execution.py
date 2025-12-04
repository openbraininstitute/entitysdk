"""Simulation execution model."""

from entitysdk.models.execution import Execution
from entitysdk.types import SimulationExecutionStatus


class SimulationExecution(Execution):
    """Simulation execution model."""

    status: SimulationExecutionStatus
