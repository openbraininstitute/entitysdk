"""Morphology models."""

from typing import Annotated

from pydantic import Field

from entitysdk.mixin import HasAssets
from entitysdk.models.brain_location import BrainLocation
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.mtype import MTypeClass
from entitysdk.models.taxonomy import Species, Strain


class ReconstructionMorphology(HasAssets, Entity):
    """Morphology model."""

    name: Annotated[
        str,
        Field(
            examples=["layer 5 Pyramidal Cell"],
            description="The name of the morphology.",
        ),
    ]
    location: Annotated[
        BrainLocation | None,
        Field(
            description="The location of the morphology in the brain.",
        ),
    ] = None
    brain_region: Annotated[
        BrainRegion,
        Field(
            description="The region of the brain where the morphology is located.",
        ),
    ] = None
    description: Annotated[
        str,
        Field(
            examples=["A layer 5 pyramidal cell"],
            description="The description of the morphology.",
        ),
    ]
    species: Annotated[
        Species,
        Field(
            description="The species of the morphology.",
        ),
    ] = None
    strain: Annotated[
        Strain | None,
        Field(
            description="The strain of the morphology.",
        ),
    ] = None
    license: Annotated[
        License | None,
        Field(
            description="The license attached to the morphology.",
        ),
    ] = None
    contributions: Annotated[
        list[Contribution] | None,
        Field(
            description="List of contributions.",
        ),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the morphology.",
        ),
    ] = None
    legacy_id: list[str] | None = None
