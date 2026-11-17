"""Mixin classes."""

from typing import Annotated

from pydantic import MISSING, BaseModel, Field

from entitysdk.models.asset import Asset


class HasAssets(BaseModel):
    """Mixin class for entities that have assets."""

    assets: list[Asset] = []


class NameDescriptionMixin(BaseModel):
    """Non-nullable name and description (entitycore NameDescriptionMixin).

    Defaults to ``MISSING`` so unset fields are omitted on serialize; deserialize
    requires them when present on the concrete model.
    """

    name: Annotated[
        str,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ] = MISSING  # type: ignore[assignment]
    description: Annotated[
        str,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ] = MISSING  # type: ignore[assignment]
