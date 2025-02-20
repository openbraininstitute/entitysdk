"""Base model."""

from typing import Self

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Entity model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
    )

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_validate({**self.model_dump(), **model_attributes})
