import uuid
from datetime import datetime, timezone

import pytest

from entitysdk import serdes as test_module
from entitysdk.models.activity import Activity
from entitysdk.models.core import Identifiable, Struct
from entitysdk.models.entity import Entity

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


def test_deserialization():
    pass


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
    )

    data = test_module.serialize_model(activity)

    assert data["used_ids"] == [str(e1.id)]
    assert data["generated_ids"] == [str(e2.id)]
    assert data["start_time"] is not None
    assert data["end_time"] is not None

    activity = Activity(
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
    )

    data = test_module.serialize_model(activity)

    assert "used_ids" not in data
    assert "generated_ids" not in data
