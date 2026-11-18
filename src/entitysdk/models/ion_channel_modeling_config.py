"""Ion channel modeling config model."""

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.types import ID


class IonChannelModelingConfig(NameDescriptionMixin, Entity):
    """IonChannelModelingConfig model."""

    ion_channel_modeling_campaign_id: ID
    scan_parameters: dict
