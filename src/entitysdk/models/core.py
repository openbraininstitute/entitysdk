"""Core models."""

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


class Entity(Identifiable):
    """Entity is a model with an id."""


class Activity(Identifiable):
    """Activity model."""
