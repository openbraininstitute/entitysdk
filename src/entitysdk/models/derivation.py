"""Derivation model."""

from entitysdk.models.core import Identifiable
from entitysdk.types import DerivationType


class Derivation(Identifiable):
    """Derivation model."""

    used: "Entity | None" = None
    generated: "Entity | None" = None
    derivation_type: DerivationType | None = None
    label: str | None = None


# Update forward references
from entitysdk.models.entity import Entity  # noqa: E402

Derivation.model_rebuild()
