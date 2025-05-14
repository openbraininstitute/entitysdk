"""Morphology models."""

from typing import Annotated

from pydantic import Field

from entitysdk.mixin import HasAssets
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.contribution import Contribution
from entitysdk.models.core import Struct
from entitysdk.models.entity import Entity
from entitysdk.models.mtype import MTypeClass
from entitysdk.typedef import ID


class License(Entity):
    """License model."""

    name: Annotated[
        str,
        Field(
            examples=["Apache 2.0"],
            description="The name of the license.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            examples=["The 2.0 version of the Apache License"],
            description="The description of the license.",
        ),
    ]
    label: Annotated[
        str,
        Field(
            examples=["Apache 2.0"],
            description="The label of the license.",
        ),
    ]


class BrainLocation(Struct):
    """BrainLocation model."""

    x: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The x coordinate of the brain location.",
        ),
    ]
    y: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The y coordinate of the brain location.",
        ),
    ]
    z: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The z coordinate of the brain location.",
        ),
    ]


class Taxonomy(Entity):
    """Taxonomy model."""

    name: Annotated[
        str,
        Field(
            examples=["Homo sapiens"],
            description="The name of the taxonomy.",
        ),
    ]
    pref_label: Annotated[
        str,
        Field(
            examples=["Homo sapiens"],
            description="The preferred label of the taxonomy.",
        ),
    ]


class Species(Entity):
    """Species model."""

    name: Annotated[
        str,
        Field(
            examples=["Mus musculus"],
            description="The name of the species.",
        ),
    ]
    taxonomy_id: Annotated[
        str,
        Field(
            examples=["1"],
            description="The taxonomy id of the species.",
        ),
    ]


class Strain(Entity):
    """Strain model."""

    name: Annotated[
        str,
        Field(
            examples=["C57BL/6J"],
            description="The name of the strain.",
        ),
    ]
    taxonomy_id: Annotated[
        str,
        Field(
            examples=["1"],
            description="The taxonomy id of the strain.",
        ),
    ]
    species_id: Annotated[
        ID,
        Field(
            description="The species id of the strain.",
        ),
    ]


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
    ]
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
    ]
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
