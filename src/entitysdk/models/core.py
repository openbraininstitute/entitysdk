"""Core models."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from entitysdk.models.base import BaseModel


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: int | None = Field(
        default=None,
        examples=[1, 2, 3],
        description="The primary key identifier of the resource.",
    )
    update_date: datetime | None = Field(
        default=None,
        examples=[datetime(2025, 1, 1)],
        description="The date and time the resource was last updated.",
    )
    creation_date: datetime | None = Field(
        default=None,
        examples=[datetime(2025, 1, 1)],
        description="The date and time the resource was created.",
    )


class Entity(Identifiable):
    """Entity is a model with id and authorization."""

    authorized_public: bool | None = Field(
        default=None,
        examples=[True, False],
        description="Whether the resource is authorized to be public.",
    )
    authorized_project_id: UUID | None = Field(
        default=None,
        examples=[UUID("12345678-1234-1234-1234-123456789012")],
        description="The project ID the resource is authorized to be public.",
    )


class Activity(Identifiable):
    """Activity model."""
