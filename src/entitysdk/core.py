"""Core models."""

from entitysdk.base import BaseModel


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: int | None = None


class Entity(Identifiable):
    """Entity is a model with an id."""


class Activity(Identifiable):
    """Activity model."""
