"""Registered and unregistered model type aliases."""

from typing import Annotated, TypeVar

from pydantic import AfterValidator

from entitysdk.models.asset import Asset
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import ID

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)
TEntity = TypeVar("TEntity", bound=Entity)
TAsset = TypeVar("TAsset", bound=Asset)


def ensure_id_is_none(value: TIdentifiable) -> TIdentifiable:
    """Check that id is None."""
    if getattr(value, "id", None) is not None:
        msg = "Resource id must be None."
        raise ValueError(msg)
    return value


def ensure_id_is_set(value: TIdentifiable) -> TIdentifiable:
    """Check that id is set."""
    if getattr(value, "id", None) is None:
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
