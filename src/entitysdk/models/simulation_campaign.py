"""Simulation campaign model."""

from entitysdk.models.entity import Entity
from entitysdk.models.simulation import Simulation


class SimulationCampaign(Entity):
    """SimulationCampaign model."""

    scan_parameters: dict
    simulations: list[Simulation] | None = None
