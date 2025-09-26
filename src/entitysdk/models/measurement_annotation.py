"""Measurement annotation."""

from entitysdk.models.base import BaseModel
from entitysdk.models.core import Identifiable
from entitysdk.types import (
    ID,
    MeasurableEntity,
    MeasurementStatistic,
    MeasurementUnit,
    StructuralDomain,
)


class MeasurementItem(BaseModel):
    """Measurement item."""

    name: MeasurementStatistic | None
    unit: MeasurementUnit | None
    value: float | None


class MeasurementKind(BaseModel):
    """Measurement kind."""

    structural_domain: StructuralDomain
    measurement_items: list[MeasurementItem]
    pref_label: str


class MeasurementAnnotation(Identifiable):
    """Measurement annotation."""

    entity_id: ID
    entity_type: MeasurableEntity
    measurement_kinds: list[MeasurementKind]
