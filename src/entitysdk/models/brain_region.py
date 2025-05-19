"""BrainRegion model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable
from entitysdk.types import ID


class BrainRegion(Identifiable):
    """BrainRegion model."""

    name: Annotated[
        str,
        Field(
            examples=["Thalamus"],
            description="The name of the brain region.",
        ),
    ]
    annotation_value: Annotated[
        int, Field(examples=[997], description="The annotation voxel value.")
    ]
    acronym: Annotated[
        str,
        Field(
            examples=["TH"],
            description="The acronym of the brain region.",
        ),
    ]
    parent_structure_id: Annotated[
        ID | None, Field(examples=[], description="The parent region structure UUID.")
    ]
    hierarchy_id: Annotated[
        ID, Field(examples=[], description="The brain hierarchy that includes this brain region.")
    ]
    color_hex_triplet: Annotated[str, Field(description="Region's color hex triplet.")]
