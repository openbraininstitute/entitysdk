"""BrainAtlas model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.models.taxonomy import Species, Strain
from entitysdk.types import ID


class BrainAtlas(Entity):
    """BrainAtlas model."""

    name: Annotated[
        str,
        Field(
            examples=["Thalamus"],
            description="The name of the brain region.",
        ),
    ]
    hierarchy_id: Annotated[
        ID, Field(examples=[], description="The brain hierarchy that includes this brain region.")
    ]
    species: Annotated[
        Species,
        Field(description="The species for which the emodel applies."),
    ]
    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = None
