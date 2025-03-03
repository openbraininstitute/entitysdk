"""Morphology models."""

from entitysdk.mixin import HasAssets
from entitysdk.models.contribution import Contribution
from entitysdk.models.core import Entity, Struct


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


class BrainLocation(Struct):
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


class ReconstructionMorphology(HasAssets, Entity):
    """Morphology model."""

    name: str
    description: str
    pref_label: str | None = None

    species: Species
    strain: Strain | None = None
    brain_region: BrainRegion
    location: BrainLocation | None = None
    contributions: list[Contribution] | None = None

    license: License | None = None

    legacy_id: str | None = None
