"""Simulation campaign model."""

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.models.simulation import Simulation
from entitysdk.types import ID


class SimulationCampaign(NameDescriptionMixin, Entity):
    """SimulationCampaign model."""

    scan_parameters: dict
    entity_id: ID
    simulations: list[Simulation] | None = None
