"""Morphology models."""

from typing import ClassVar

from entitysdk.core import Entity


class License(Entity):
    """License model."""

    __route__: ClassVar[str] = "license"

    name: str
    description: str
    label: str

    legacy_id: str | None = None


class BrainRegion(Entity):
    """BrainRegion model."""

    __route__: ClassVar[str] = "brain_region"

    name: str
    acronym: str
    children: list[int]


class BrainLocation(Entity):
    """BrainLocation model."""

    __route__: ClassVar[str] = "brain_location"

    x: float
    y: float
    z: float


class Taxonomy(Entity):
    """Taxonomy model."""

    __route__: ClassVar[str] = "taxonomy"

    name: str
    pref_label: str


class Species(Entity):
    """Species model."""

    __route__: ClassVar[str] = "species"

    name: str
    taxonomy_id: str


class Strain(Entity):
    """Strain model."""

    __route__: ClassVar[str] = "strain"

    name: str
    taxonomy_id: str

    species: Species


class ReconstructionMorphology(Entity):
    """Morphology model."""

    __route__: ClassVar[str] = "reconstruction_morphology"

    name: str
    description: str
    pref_label: str | None = None

    species: Species
    strain: Strain | None = None
    brain_region: BrainRegion
    brain_location: BrainLocation | None = None

    license: License | None = None

    legacy_id: str | None = None
