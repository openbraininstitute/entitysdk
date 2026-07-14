"""Reusable Pydantic field types."""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetPydanticSchema
from pydantic_core import core_schema

from entitysdk.types import ID


def _nullable_id_schema(_source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap the ``ID`` schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(ID))


# Pydantic metadata that keeps the static type as ``ID`` while allowing ``None`` when
# validating or serializing. Pair it with ``Field(default=None)`` on the model field;
# see ``entitysdk.models.core.Identifiable`` for how ``Identifiable.id`` uses this.
RuntimeNullableField = GetPydanticSchema(_nullable_id_schema)
