"""Validation result."""

from typing import Annotated

from pydantic import Field

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.entity import Entity
from entitysdk.types import ID


class ValidationResult(NameDescriptionMixin, Entity):
    """Validation result."""

    passed: Annotated[
        bool,
        Field(
            description="True if the validation passed, False otherwise.",
            examples=[True],
        ),
    ]
    validated_entity_id: Annotated[
        ID,
        Field(
            description="ID of the validated entity.",
            examples=["85663316-a7ff-4107-9eb9-236de8868c5c"],
        ),
    ]
