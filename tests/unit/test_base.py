from typing import ClassVar

import pytest

from entitysdk import base as test_module


class MyCustomModel(test_module.BaseModel):
    """My custom model."""

    name: str
    description: str

    __route__: ClassVar[str] = "my-custom-model"


@pytest.fixture
def model():
    return MyCustomModel(
        name="foo",
        description="bar",
    )


def test_route(model: MyCustomModel):
    assert model.route == "my-custom-model"


def test_route_raises_error_if_not_set():
    model = test_module.BaseModel()

    with pytest.raises(TypeError, match="does not have a corresponding route in entitycore"):
        _ = model.route


def test_evolve(model: MyCustomModel):
    evolved = model.evolve(name="baz")
    assert evolved.name == "baz"
    assert evolved.description == "bar"
