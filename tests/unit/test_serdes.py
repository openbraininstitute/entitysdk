import pytest

from entitysdk import serdes as test_module
from entitysdk.models.core import Identifiable, Struct

from .util import MOCK_UUID


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
def test_serialize_entity(entity, expected):
    result = test_module.serialize_entity(entity)
    assert result == expected


def test_deserialization():
    pass
