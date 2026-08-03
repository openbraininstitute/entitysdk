"""Tests for Identifiable runtime-nullable metadata fields."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from entitysdk.models.core import PlatformUser
from entitysdk.models.entity import Entity

from ..util import MOCK_UUID


@pytest.mark.parametrize(
    ("field_name", "payload", "expected"),
    [
        ("id", None, None),
        ("creation_date", None, None),
        ("update_date", None, None),
        ("created_by", None, None),
        ("updated_by", None, None),
    ],
)
def test_identifiable_accepts_explicit_none(field_name, payload, expected):
    entity = Entity(name="entity", **{field_name: payload})
    assert getattr(entity, field_name) is expected


@pytest.mark.parametrize(
    "field_name",
    ["id", "creation_date", "update_date", "created_by", "updated_by"],
)
def test_identifiable_accepts_json_null(field_name):
    entity = Entity.model_validate_json(
        f'{{"name": "entity", "{field_name}": null}}',
    )
    assert getattr(entity, field_name) is None


def test_identifiable_defaults_metadata_fields_to_none():
    entity = Entity(name="entity")
    assert entity.id is None
    assert entity.creation_date is None
    assert entity.update_date is None
    assert entity.created_by is None
    assert entity.updated_by is None


def test_identifiable_accepts_populated_metadata_fields():
    created = datetime(2025, 1, 1)
    updated = datetime(2025, 6, 1)
    platform_user = PlatformUser(
        id=MOCK_UUID,
        pref_label="Jane Doe",
        creation_date=created,
        update_date=updated,
    )
    entity = Entity(
        id=MOCK_UUID,
        name="entity",
        creation_date=created,
        update_date=updated,
        created_by=platform_user,
        updated_by=platform_user,
    )
    assert entity.id == MOCK_UUID
    assert entity.creation_date == created
    assert entity.update_date == updated
    assert entity.created_by is platform_user
    assert entity.updated_by is platform_user


def test_identifiable_accepts_nested_platform_user_from_json():
    entity = Entity.model_validate(
        {
            "name": "entity",
            "created_by": {
                "id": str(MOCK_UUID),
                "pref_label": "Jane Doe",
                "creation_date": "2025-01-01T00:00:00",
                "update_date": "2025-01-01T00:00:00",
            },
        }
    )
    assert isinstance(entity.created_by, PlatformUser)
    assert entity.created_by.pref_label == "Jane Doe"


def test_identifiable_rejects_invalid_metadata_values():
    with pytest.raises(ValidationError):
        Entity(name="entity", id="not-a-uuid")

    with pytest.raises(ValidationError):
        Entity(name="entity", creation_date="not-a-datetime")

    with pytest.raises(ValidationError):
        Entity(name="entity", created_by="not-a-person")
