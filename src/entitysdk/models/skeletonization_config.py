"""Skeletonization config model."""

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class SkeletonizationConfig(Entity):
    """SkeletonizationConfig model."""

    skeletonization_campaign_id: ID
    em_cell_mesh_id: ID
    scan_parameters: dict
