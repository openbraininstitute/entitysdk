import uuid

import pytest

from entitysdk.models.asset import Asset
from entitysdk.models.entity import Entity
from entitysdk.models.types import (
    ensure_id_is_none,
    ensure_id_is_set,
)
from entitysdk.types import AssetLabel, ContentType, StorageType
from tests.unit.util import MOCK_UUID


def _asset(*, asset_id: uuid.UUID | None = MOCK_UUID) -> Asset:
    return Asset(
        id=asset_id,
        path="path/to/asset",
        full_path="full/path/to/asset",
        storage_type=StorageType.aws_s3_internal,
        label=AssetLabel.morphology,
        is_directory=False,
        content_type=ContentType.text_plain,
        size=1,
    )


def test_ensure_id_is_none_accepts_entity_without_id():
    entity = Entity(name="entity")
    assert ensure_id_is_none(entity) is entity


def test_ensure_id_is_none_rejects_entity_with_id():
    entity = Entity(id=MOCK_UUID, name="entity")
    with pytest.raises(ValueError, match="Resource id must be None"):
        ensure_id_is_none(entity)


def test_ensure_id_is_none_accepts_asset_without_id():
    asset = _asset(asset_id=None)
    assert ensure_id_is_none(asset) is asset


def test_ensure_id_is_set_accepts_entity_with_id():
    entity = Entity(id=MOCK_UUID, name="entity")
    assert ensure_id_is_set(entity) is entity


def test_ensure_id_is_set_rejects_entity_without_id():
    entity = Entity(name="entity")
    with pytest.raises(ValueError, match="Resource must have an id"):
        ensure_id_is_set(entity)


def test_ensure_id_is_set_accepts_asset_with_id():
    asset = _asset()
    assert ensure_id_is_set(asset) is asset


def test_ensure_id_is_set_rejects_asset_without_id():
    asset = _asset(asset_id=None)
    with pytest.raises(ValueError, match="Resource must have an id"):
        ensure_id_is_set(asset)
