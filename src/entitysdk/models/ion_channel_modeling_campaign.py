"""Ion channel modeling campaign model."""

from entitysdk.models.entity import Entity
from entitysdk.models.ion_channel_modeling_config import IonChannelModelingConfig
from entitysdk.models.ion_channel_recording import IonChannelRecording


class IonChannelModelingCampaign(Entity):
    """IonChannelModelingCampaign model."""

    scan_parameters: dict
    ion_channel_modeling_configs: list[IonChannelModelingConfig] | None = None
    input_recordings: list[IonChannelRecording] | None = None
