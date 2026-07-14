"""Registered and unregistered model type aliases."""

from typing import TYPE_CHECKING, Annotated, TypeVar

from pydantic import AfterValidator

from entitysdk.types import ID

if TYPE_CHECKING:
    from entitysdk.models.asset import Asset
    from entitysdk.models.core import Identifiable
    from entitysdk.models.entity import Entity

    TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)
    TEntity = TypeVar("TEntity", bound=Entity)
    TAsset = TypeVar("TAsset", bound=Asset)
else:
    TIdentifiable = TypeVar("TIdentifiable")
    TEntity = TypeVar("TEntity")
    TAsset = TypeVar("TAsset")


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


UnregisteredIdentifiable = Annotated[
    TIdentifiable,
    AfterValidator(ensure_id_is_none),
]
RegisteredIdentifiable = Annotated[
    TIdentifiable,
    AfterValidator(ensure_id_is_set),
]
UnregisteredEntity = Annotated[
    TEntity,
    AfterValidator(ensure_id_is_none),
]
RegisteredEntity = Annotated[
    TEntity,
    AfterValidator(ensure_id_is_set),
]
UnregisteredAsset = Annotated[
    TAsset,
    AfterValidator(ensure_id_is_none),
]
RegisteredAsset = Annotated[
    TAsset,
    AfterValidator(ensure_id_is_set),
]

RegisteredAssetOrId = ID | RegisteredAsset
