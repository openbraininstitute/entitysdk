"""Simulation model."""

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class Simulation(Entity):
    """Simulation model."""

    simulation_campaign_id: ID
    entity_id: ID
    scan_parameters: dict
    number_neurons: int | None = None  # Make non optional after 2026.1.3 prod deployment
