"""Simulation result model."""

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.types import ID


class SimulationResult(NameDescriptionMixin, Entity):
    """Simulation model."""

    simulation_id: ID
