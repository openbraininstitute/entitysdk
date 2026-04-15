"""Cell Composition."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.taxonomy import Species, Strain


class CellComposition(Entity):
    """Cell Composition."""

    species: Annotated[
        Species,
        Field(description="The species for which the emodel applies."),
    ]
    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = None
    brain_region: BrainRegion | None = None
