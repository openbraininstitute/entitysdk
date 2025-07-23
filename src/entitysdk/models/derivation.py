"""Derivation model."""

from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity


class Derivation(Identifiable):
    """Derivation model."""

    used: Entity
    generated: Entity

    # TODO: Fetch enum type from server schema when latest changes land on staging
    derivation_type: str | None = None
