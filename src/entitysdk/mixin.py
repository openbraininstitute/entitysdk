"""Mixin classes."""

from pydantic import BaseModel

from entitysdk.models.asset import Asset


class HasAssets(BaseModel):
    """Mixin class for entities that have assets."""

    assets: list[Asset] = []
