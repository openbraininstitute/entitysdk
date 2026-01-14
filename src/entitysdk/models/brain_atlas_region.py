"""BrainAtlasRegion model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class BrainAtlasRegion(Entity):
    """BrainAtlasRegion model."""

    volume: Annotated[
        float,
        Field(
            examples=[0.25],
            description=(
                "The volume of the brain region. "
                "only the volume for leaf nodes is saved; the consumer must calculate"
                "volumes depending on which view of the hierarchy they are using"
            ),
        ),
    ]
    is_leaf_region: Annotated[
        bool,
        Field(examples=[], description="Whether this is a leaf region"),
    ]
    brain_atlas_id: Annotated[
        ID, Field(examples=[], description="The BrainAtlas to which this region belongs")
    ]
    brain_region_id: Annotated[ID, Field(examples=[], description="The BrainRegion with the atlas")]
