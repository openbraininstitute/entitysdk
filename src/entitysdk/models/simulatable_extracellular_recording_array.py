"""simulatable_extracellular_recording_array module."""

from entitysdk.models.entity import Entity
from entitysdk.types import ID, ElectrodeType


class SimulatableExtracellularRecordingArray(Entity):
    """SimulatableExtracellularRecordingArray class."""

    electrode_type: ElectrodeType
    circuit_id: ID
