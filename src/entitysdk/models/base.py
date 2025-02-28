"""Base model."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Entity model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        extra="forbid",
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

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_copy(update=model_attributes, deep=True)
