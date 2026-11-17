"""Registered and unregistered model type aliases."""

from typing import Annotated, TypeVar

from pydantic import MISSING, AfterValidator

from entitysdk.models.asset import Asset
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import ID

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)
TEntity = TypeVar("TEntity", bound=Entity)
TAsset = TypeVar("TAsset", bound=Asset)


def _id_is_unset(value: TIdentifiable) -> bool:
    resource_id = getattr(value, "id", None)
    return resource_id is None or resource_id is MISSING


def ensure_id_is_none(value: TIdentifiable) -> TIdentifiable:
    """Check that id is unset (``None`` or ``MISSING``)."""
    if not _id_is_unset(value):
        msg = "Resource id must be None."
        raise ValueError(msg)
    return value


def ensure_id_is_set(value: TIdentifiable) -> TIdentifiable:
    """Check that id is set."""
    if _id_is_unset(value):
        msg = "Resource must have an id."
        raise ValueError(msg)
    return value


RegisteredEntity = Annotated[
    TEntity,
    AfterValidator(ensure_id_is_set),
]

RegisteredAssetOrId = (
    ID
    | Annotated[
        TAsset,
        AfterValidator(ensure_id_is_set),
    ]
)
