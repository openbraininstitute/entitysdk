"""Base model."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Entity model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        extra="forbid",
    )

    update_date: datetime | None = None
    creation_date: datetime | None = None

    authorized_public: bool | None = None
    authorized_project_id: str | None = None

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_copy(update=model_attributes, deep=True)
