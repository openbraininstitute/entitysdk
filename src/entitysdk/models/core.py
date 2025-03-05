"""Core models."""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: Annotated[
        int | None,
        Field(
            examples=[1, 2, 3],
            description="The primary key identifier of the resource.",
        ),
    ] = None
    update_date: Annotated[
        datetime | None,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was last updated.",
        ),
    ] = None
    creation_date: Annotated[
        datetime | None,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was created.",
        ),
    ] = None


class Activity(Identifiable):
    """Activity model."""
