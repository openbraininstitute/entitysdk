"""Morphology models."""

from entitysdk.mixin import HasAssets
from pydantic import Field

from entitysdk.models.contribution import Contribution
from entitysdk.models.core import Entity, Struct


class License(Entity):
    """License model."""

    name: str = Field(
        ...,
        examples=["Apache 2.0"],
        description="The name of the license.",
    )
    description: str = Field(
        ...,
        examples=["The 2.0 version of the Apache License"],
        description="The description of the license.",
    )
    label: str = Field(
        ...,
        examples=["Apache 2.0"],
        description="The label of the license.",
    )
    legacy_id: str | None = None


class BrainRegion(Entity):
    """BrainRegion model."""

    name: str = Field(
        ...,
        examples=["Prefrontal Cortex"],
        description="The name of the brain region.",
    )
    acronym: str = Field(
        ...,
        examples=["PFC"],
        description="The acronym of the brain region.",
    )
    children: list[int] = Field(
        ...,
        examples=[1, 2],
        description="The children of the brain region hierarchy.",
    )


class BrainLocation(Struct):
    """BrainLocation model."""

    x: float = Field(
        ...,
        examples=[1.0, 2.0, 3.0],
        description="The x coordinate of the brain location.",
    )
    y: float = Field(
        ...,
        examples=[1.0, 2.0, 3.0],
        description="The y coordinate of the brain location.",
    )
    z: float = Field(
        ...,
        examples=[1.0, 2.0, 3.0],
        description="The z coordinate of the brain location.",
    )


class Taxonomy(Entity):
    """Taxonomy model."""

    name: str = Field(
        ...,
        examples=["Homo sapiens"],
        description="The name of the taxonomy.",
    )
    pref_label: str = Field(
        ...,
        examples=["Homo sapiens"],
        description="The preferred label of the taxonomy.",
    )


class Species(Entity):
    """Species model."""

    name: str = Field(
        ...,
        examples=["Mus musculus"],
        description="The name of the species.",
    )
    taxonomy_id: str = Field(
        ...,
        examples=["1"],
        description="The taxonomy id of the species.",
    )


class Strain(Entity):
    """Strain model."""

    name: str = Field(
        ...,
        examples=["C57BL/6J"],
        description="The name of the strain.",
    )
    taxonomy_id: str = Field(
        ...,
        examples=["1"],
        description="The taxonomy id of the strain.",
    )
    species_id: int = Field(
        ...,
        examples=[1],
        description="The species id of the strain.",
    )


class ReconstructionMorphology(HasAssets, Entity):
    """Morphology model."""

    name: str = Field(
        ...,
        examples=["layer 5 Pyramidal Cell"],
        description="The name of the morphology.",
    )
    location: BrainLocation | None = Field(
        default=None,
        description="The location of the morphology in the brain.",
    )
    brain_region: BrainRegion = Field(
        ...,
        description="The region of the brain where the morphology is located.",
    )
    description: str = Field(
        ...,
        examples=["A layer 5 pyramidal cell"],
        description="The description of the morphology.",
    )
    pref_label: str | None = Field(
        default=None,
        examples=["layer 5 Pyramidal Cell"],
        description="The preferred label of the morphology.",
    )
    species: Species = Field(
        ...,
        description="The species of the morphology.",
    )
    strain: Strain | None = Field(
        default=None,
        description="The strain of the morphology.",
    )
    license: License | None = Field(
        default=None,
        description="The license attached to the morphology.",
    )
    contributions: list[Contribution] | None = Field(
        default=None, description="List of contributions."
    )
    legacy_id: str | None = None
