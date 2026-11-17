"""Pydantic helpers for static/runtime field typing."""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetPydanticSchema
from pydantic_core import core_schema


def _nullable_schema(source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap a field schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(source_type))


# Shared create/read models need three states for server-owned fields:
# - ``MISSING``: unset on create → omitted from serialize
# - ``None``: JSON null on deserialize (via this helper)
# - ``T``: real value after fetch
#
# Annotate as ``T`` (not ``T | MISSING`` — pyright does not erase MISSING from
# unions). Default to ``MISSING`` with ``# type: ignore[assignment]``.
# ``RuntimeNullableField`` accepts wire ``null``. Example: Identifiable.id.
RuntimeNullableField = GetPydanticSchema(_nullable_schema)
