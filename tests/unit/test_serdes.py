import uuid
from datetime import datetime, timezone

import pytest
from pydantic import MISSING, ValidationError

from entitysdk import serdes as test_module
from entitysdk.models.activity import Activity
from entitysdk.models.core import Identifiable, Struct
from entitysdk.models.entity import Entity
from entitysdk.models.subject import Subject
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


def test_serialize_model_omits_missing_name_description():
    subject = Subject(name="subject", sex="male", species={"name": "mouse", "taxonomy_id": "10090"})
    data = test_module.serialize_model(subject)

    assert data["name"] == "subject"
    assert "description" not in data
    assert subject.description is MISSING


def test_serialize_model_includes_explicit_none_for_nullable_fields():
    entity = Entity(legacy_id=None)
    data = test_module.serialize_model(entity)

    assert data["legacy_id"] is None


def test_name_description_mixin_rejects_null():
    with pytest.raises(ValidationError):
        Subject(name=None, sex="male", species={"name": "mouse", "taxonomy_id": "10090"})
    with pytest.raises(ValidationError):
        Subject(
            name="subject",
            description=None,
            sex="male",
            species={"name": "mouse", "taxonomy_id": "10090"},
        )


def test_serialize_validation_result_has_no_description_field():
    result = ValidationResult(
        name="scores",
        passed=True,
        validated_entity_id=MOCK_UUID,
    )
    data = test_module.serialize_model(result)

    assert "description" not in data
    assert data["name"] == "scores"


def test_deserialize_rejects_omitted_non_nullable_fields():
    with pytest.raises(ValidationError) as exc_info:
        test_module.deserialize_model({"name": "entity"}, Entity)

    assert "type" in str(exc_info.value)


def test_deserialize_name_description_requires_fields():
    with pytest.raises(ValidationError) as exc_info:
        test_module.deserialize_model(
            {
                "id": str(MOCK_UUID),
                "type": "subject",
                "sex": "male",
                "species": {"name": "mouse", "taxonomy_id": "10090"},
                "assets": [],
            },
            Subject,
        )

    assert "name" in str(exc_info.value)
    assert "description" in str(exc_info.value)


def test_deserialize_allows_omitted_runtime_nullable_fields_on_entity():
    entity = test_module.deserialize_model(
        {
            "id": str(MOCK_UUID),
            "type": "circuit",
            "assets": [],
        },
        Entity,
    )

    assert "name" not in Entity.model_fields
    assert "description" not in Entity.model_fields
    assert entity.authorized_project_id is MISSING
    assert entity.contributions is MISSING
    assert entity.type == "circuit"


def test_local_construct_still_allows_missing_non_nullable_fields():
    subject = Subject(name="subject", sex="male", species={"name": "mouse", "taxonomy_id": "10090"})
    assert subject.description is MISSING
    assert subject.type is MISSING


def test_serialize_excludes_server_assigned_fields():
    activity = Activity.model_validate(
        {
            "status": "done",
            "type": "validation",
            "authorized_project_id": str(MOCK_UUID),
            "start_time": datetime.now(UTC).isoformat(),
            "used": [],
            "generated": [],
        }
    )
    assert activity.type == "validation"
    assert activity.authorized_project_id == MOCK_UUID
    data = test_module.serialize_model(activity)
    assert "type" not in data
    assert "authorized_project_id" not in data

    entity = Entity.model_validate({"type": "subject", "authorized_project_id": str(MOCK_UUID)})
    assert entity.type == "subject"
    assert entity.authorized_project_id == MOCK_UUID
    data = test_module.serialize_model(entity)
    assert "type" not in data
    assert "authorized_project_id" not in data


def test_serialize_activity():
    e1 = Entity(id=uuid.uuid4())
    e2 = Entity(id=uuid.uuid4())
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
