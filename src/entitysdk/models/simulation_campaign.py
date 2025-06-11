"""Simulation campaign model."""

from entitysdk.models.entity import Entity
from entitysdk.models.simulation import Simulation


class SimulationCampaign(Entity):
    """SimulationCampaign model."""

    simulations: list[Simulation] | None = None
