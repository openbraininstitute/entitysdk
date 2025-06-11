"""Simulation model."""

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class Simulation(Entity):
    """Simulation model."""

    simulation_campaign_id: ID
    entity_id: ID
    scan_parameters: dict
