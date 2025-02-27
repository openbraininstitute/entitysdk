"""Core models."""

from datetime import datetime

from entitysdk.models.base import BaseModel


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: int | None = None
    update_date: datetime | None = None
    creation_date: datetime | None = None


class Entity(Identifiable):
    """Entity is a model with id and authorization."""

    authorized_public: bool | None = None
    authorized_project_id: str | None = None


class Activity(Identifiable):
    """Activity model."""
