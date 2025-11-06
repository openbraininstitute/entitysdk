"""Skeletonization campaign model."""

from entitysdk.models.em_cell_mesh import EMCellMesh
from entitysdk.models.entity import Entity
from entitysdk.models.skeletonization_config import SkeletonizationConfig


class SkeletonizationCampaign(Entity):
    """SkeletonizationCampaign model."""

    scan_parameters: dict
    skeletonization_configs: list[SkeletonizationConfig] | None = None
    input_meshes: list[EMCellMesh] | None = None
