"""Base model."""

from typing import ClassVar, Self

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Entity model."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
    )

    __route__: ClassVar[str | None] = None

    @property
    def route(self) -> str:
        """Return the route corresponding to this type."""
        if self.__route__ is None:
            raise TypeError(
                f"Entity type {type(self)} does not have a corresponding route in entitycore."
            )
        return self.__route__

    def evolve(self, **model_attributes) -> Self:
        """Evolve a copy of the model with new attributes."""
        return self.model_validate({**self.model_dump(), **model_attributes})
