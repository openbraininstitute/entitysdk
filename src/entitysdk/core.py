"""Core models."""

from typing import ClassVar

from entitysdk.base import BaseModel


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: int | None = None


class Entity(Identifiable):
    """Entity is a model with an id."""

    __route__: ClassVar[str] = "entity"
