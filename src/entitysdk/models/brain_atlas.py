"""BrainAtlas model."""

from typing import Annotated

from pydantic import Field

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.models.taxonomy import Species, Strain
from entitysdk.types import ID


class BrainAtlas(NameDescriptionMixin, Entity):
    """BrainAtlas model."""

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
