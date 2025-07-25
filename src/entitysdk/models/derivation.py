"""Derivation model."""

from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import DerivationType


class Derivation(Identifiable):
    """Derivation model."""

    used: Entity
    generated: Entity
    derivation_type: DerivationType | None = None
