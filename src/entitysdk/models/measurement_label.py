"""Measurement label."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable
from entitysdk.types import MeasurableEntity


class MeasurementLabel(Identifiable):
    """Measurement label."""

    entity_type: Annotated[
        MeasurableEntity,
        Field(
            description="The type of entity being measured.",
        ),
    ]
    pref_label: Annotated[
        str,
        Field(
            description="The preferred human-readable label for the measurement.",
        ),
    ]
    definition: Annotated[
        str,
        Field(
            description="A textual definition describing the meaning of the measurement.",
        ),
    ]
    alt_label: Annotated[
        str | None,
        Field(description="An alternative human-readable label for the measurement."),
    ] = None
