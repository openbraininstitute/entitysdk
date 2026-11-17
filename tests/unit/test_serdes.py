import uuid
from datetime import datetime, timezone

import pytest
from pydantic import MISSING, ValidationError

from entitysdk import serdes as test_module
from entitysdk.models.activity import Activity
from entitysdk.models.core import Identifiable, Struct
from entitysdk.models.entity import Entity
from entitysdk.models.validation_result import ValidationResult

from .util import MOCK_UUID

UTC = timezone.utc


class E1(Struct):
    a: str
    b: int


class E2(Identifiable):
    a: str
    b: int


class E3(Identifiable):
    a: E1
    b: E2


@pytest.mark.parametrize(
    "entity, expected",
    [
        (
            E1(a="foo", b=1),
            {"a": "foo", "b": 1},
        ),
        (
            E2(id=MOCK_UUID, a="foo", b=1),
            {"a": "foo", "b": 1},
        ),
        (
            E3(
                id=MOCK_UUID,
                a=E1(a="foo", b=1),
                b=E2(id=MOCK_UUID, a="foo", b=1),
            ),
            {
                "a": {"a": "foo", "b": 1},
                "b_id": str(MOCK_UUID),
            },
        ),
    ],
)
def test_serialize_model(entity, expected):
    result = test_module.serialize_model(entity)
    assert result == expected


def test_serialize_model_omits_missing_optional_fields():
    entity = Entity(name="entity")
    data = test_module.serialize_model(entity)

    assert data == {
        "name": "entity",
        "authorized_public": False,
        "lifecycle_status": "active",
    }
    assert entity.description is MISSING


def test_serialize_model_includes_explicit_none_for_nullable_fields():
    # legacy_id is nullable in entitycore; name/description are not.
    entity = Entity(name="entity", legacy_id=None)
    data = test_module.serialize_model(entity)

    assert data["legacy_id"] is None
    assert "description" not in data


def test_entity_rejects_null_name_and_description():
    with pytest.raises(ValidationError):
        Entity(name=None)
    with pytest.raises(ValidationError):
        Entity(name="entity", description=None)


def test_serialize_validation_result_omits_unset_description():
    result = ValidationResult(
        name="scores",
        passed=True,
        validated_entity_id=MOCK_UUID,
    )
    data = test_module.serialize_model(result)

    assert "description" not in data
    assert data["name"] == "scores"


def test_deserialization():
    pass


def test_serialize_excludes_server_assigned_fields():
    activity = Activity.model_validate(
        {
            "status": "done",
            "type": "validation",
            "authorized_project_id": str(MOCK_UUID),
            "start_time": datetime.now(UTC).isoformat(),
        }
    )
    assert activity.type == "validation"
    assert activity.authorized_project_id == MOCK_UUID
    data = test_module.serialize_model(activity)
    assert "type" not in data
    assert "authorized_project_id" not in data

    entity = Entity.model_validate(
        {"name": "entity", "type": "subject", "authorized_project_id": str(MOCK_UUID)}
    )
    assert entity.type == "subject"
    assert entity.authorized_project_id == MOCK_UUID
    data = test_module.serialize_model(entity)
    assert "type" not in data
    assert "authorized_project_id" not in data


def test_serialize_activity():
    e1 = Entity(
        id=uuid.uuid4(),
        name="foo",
        description="foo",
    )
    e2 = Entity(
        id=uuid.uuid4(),
        name="bar",
        description="bar",
    )
    activity = Activity(
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        used=[e1],
        generated=[e2],
        status="running",
    )

    data = test_module.serialize_model(activity)

    assert data["used_ids"] == [str(e1.id)]
    assert data["generated_ids"] == [str(e2.id)]
    assert data["start_time"] is not None
    assert data["end_time"] is not None

    activity = Activity(
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
        status="running",
    )

    data = test_module.serialize_model(activity)

    assert "used_ids" not in data
    assert "generated_ids" not in data
