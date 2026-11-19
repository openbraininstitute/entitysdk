"""simulatable_extracellular_recording_array module."""

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.types import ID, ElectrodeType


class SimulatableExtracellularRecordingArray(NameDescriptionMixin, Entity):
    """SimulatableExtracellularRecordingArray class."""

    electrode_type: ElectrodeType
    circuit_id: ID
