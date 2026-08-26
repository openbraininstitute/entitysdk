"""Simulation model."""

from entitysdk.models.entity import Entity
from entitysdk.models.simulatable_extracellular_recording_array import (
    SimulatableExtracellularRecordingArray,
)
from entitysdk.types import ID


class Simulation(Entity):
    """Simulation model."""

    simulation_campaign_id: ID
    entity_id: ID
    scan_parameters: dict
    number_neurons: int
    recording_arrays: list[SimulatableExtracellularRecordingArray] = []
