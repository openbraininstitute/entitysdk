"""BrainRegionHierarchy model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable
from entitysdk.models.taxonomy import Species, Strain


class BrainRegionHierarchy(Identifiable):
    """BrainRegionHierarchy model."""

    name: Annotated[
        str,
        Field(
            examples=["Thalamus"],
            description="The name of the brain region.",
        ),
    ]

    species: Annotated[
        Species,
        Field(description="The species for which the emodel applies."),
    ]

    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = None
