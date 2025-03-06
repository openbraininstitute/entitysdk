"""Base model."""

from typing import Self

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        extra="ignore",
    )

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_copy(update=model_attributes, deep=True)
