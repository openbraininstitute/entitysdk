"""Validation result."""

from typing import Annotated

from pydantic import MISSING, Field

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class ValidationResult(Entity):
    """Validation result."""

    # entitycore ValidationResult has name but not NameDescriptionMixin / description.
    passed: Annotated[
        bool,
        Field(
            description="True if the validation passed, False otherwise.",
            examples=[True],
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Name of the validation.",
            examples=["Neuron spiking validation"],
        ),
    ] = MISSING  # type: ignore[assignment]
    validated_entity_id: Annotated[
        ID,
        Field(
            description="ID of the validated entity.",
            examples=["85663316-a7ff-4107-9eb9-236de8868c5c"],
        ),
    ]
