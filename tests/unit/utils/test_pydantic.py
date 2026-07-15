"""Tests for pydantic helpers."""

from typing import Annotated

import pytest
from pydantic import Field, ValidationError

from entitysdk.models.base import BaseModel
from entitysdk.utils.pydantic import RuntimeNullableField


class _RuntimeNullableModel(BaseModel):
    value: Annotated[int, RuntimeNullableField, Field(description="nullable int")] = None  # type: ignore[assignment]


def test_runtime_nullable_field_accepts_none():
    model = _RuntimeNullableModel(value=None)

    assert model.value is None


def test_runtime_nullable_field_accepts_json_null():
    model = _RuntimeNullableModel.model_validate_json('{"value": null}')

    assert model.value is None


def test_runtime_nullable_field_accepts_value():
    model = _RuntimeNullableModel(value=42)

    assert model.value == 42


def test_runtime_nullable_field_rejects_invalid_value():
    with pytest.raises(ValidationError):
        _RuntimeNullableModel(value="not-an-int")
