"""Simulation result model."""

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class SimulationResult(Entity):
    """Simulation model."""

    simulation_id: ID
