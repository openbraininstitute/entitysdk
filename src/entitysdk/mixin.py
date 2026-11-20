"""Mixin classes."""

from typing import Annotated

from pydantic import BaseModel, Field

from entitysdk.models.asset import Asset


class HasAssets(BaseModel):
    """Mixin class for entities that have assets."""

    assets: list[Asset] = []


class NameDescriptionMixin(BaseModel):
    """Non-nullable name and description (entitycore NameDescriptionMixin)."""

    name: Annotated[
        str,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ]
