"""Core models."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

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


class Entity(Identifiable):
    """Entity is a model with id and authorization."""

    authorized_public: Annotated[
        bool | None,
        Field(
            examples=[True, False],
            description="Whether the resource is authorized to be public.",
        ),
    ] = None
    authorized_project_id: Annotated[
        UUID | None,
        Field(
            examples=[UUID("12345678-1234-1234-1234-123456789012")],
            description="The project ID the resource is authorized to be public.",
        ),
    ] = None


class Activity(Identifiable):
    """Activity model."""
