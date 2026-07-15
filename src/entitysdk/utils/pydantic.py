"""Pydantic related functionality."""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetPydanticSchema
from pydantic_core import core_schema


def _nullable_schema(source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap a field schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(source_type))


# Pydantic metadata that keeps the annotated static type while allowing ``None`` when
# validating or serializing. Pair it with ``Field(default=None)`` on the model field;
# see ``entitysdk.models.core.Identifiable`` for usage on optional metadata fields.
RuntimeNullableField = GetPydanticSchema(_nullable_schema)
