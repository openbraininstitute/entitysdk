from typing import ClassVar

from entitysdk.core import Entity


class BrainRegion(Entity):
    """BrainRegion model."""

    __route__: ClassVar[str] = "brain_region"

    acronym: str
    children: list[int]


class Taxonomy(Entity):
    """Taxonomy model."""

    __route__: ClassVar[str] = "taxonomy"

    name: str
    pref_label: str


class Species(Entity):
    """Species model."""

    __route__: ClassVar[str] = "species"

    taxonomy_id: str


class Strain(Entity):
    """Strain model."""

    __route__: ClassVar[str] = "strain"

    name: str
    pref_label: str


class ReconstructionMorphology(Entity):
    """Morphology model."""

    __route__: ClassVar[str] = "reconstruction_morphology"

    name: str
    pref_label: str | None = None

    species: Species
    strain: Strain | None = None
    brain_region: BrainRegion
