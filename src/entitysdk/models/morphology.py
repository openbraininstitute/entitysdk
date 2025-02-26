"""Morphology models."""

from entitysdk.core import Entity


class License(Entity):
    """License model."""

    name: str
    description: str
    label: str

    legacy_id: str | None = None


class BrainRegion(Entity):
    """BrainRegion model."""

    name: str
    acronym: str
    children: list[int]


class BrainLocation(Entity):
    """BrainLocation model."""

    x: float
    y: float
    z: float


class Taxonomy(Entity):
    """Taxonomy model."""

    name: str
    pref_label: str


class Species(Entity):
    """Species model."""

    name: str
    taxonomy_id: str


class Strain(Entity):
    """Strain model."""

    name: str
    taxonomy_id: str

    species_id: int


class ReconstructionMorphology(Entity):
    """Morphology model."""

    name: str
    description: str
    pref_label: str | None = None

    species: Species
    strain: Strain | None = None
    brain_region: BrainRegion
    brain_location: BrainLocation | None = None

    license: License | None = None

    legacy_id: str | None = None
