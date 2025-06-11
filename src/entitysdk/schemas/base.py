"""Base schema model."""

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    """Base model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        extra="forbid",
    )
