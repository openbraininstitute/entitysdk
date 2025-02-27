from typing import ClassVar

import pytest

from entitysdk.models import base as test_module


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


def test_evolve(model: MyCustomModel):
    evolved = model.evolve(name="baz")
    assert evolved.name == "baz"
    assert evolved.description == "bar"
