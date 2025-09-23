"""Base model."""

import sys

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict

if sys.version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Self
else:
    from typing import Self


class BaseModel(PydanticBaseModel):
    """Base model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
        extra="ignore",
        serialize_by_alias=True,
    )

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_copy(update=model_attributes, deep=True)
