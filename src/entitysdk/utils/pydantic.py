"""Pydantic helpers for static/runtime field typing."""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetPydanticSchema
from pydantic_core import core_schema


def _nullable_schema(source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap a field schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(source_type))


# Shared create/read models need three states for server-owned fields:
# - ``MISSING``: unset on create → omitted from serialize
# - ``None``: JSON null on deserialize (nested/incomplete payloads)
# - ``T``: real value after fetch
#
# ``Annotated[T | MISSING, RuntimeNullableField] = MISSING`` encodes that:
# pyright treats the field as ``T`` (``MISSING`` is special-cased),
# ``RuntimeNullableField`` accepts ``None`` at runtime, and the default
# ``MISSING`` is omitted on serialize. Use ``# type: ignore[assignment]`` on
# the default. Example: ``entitysdk.models.core.Identifiable``.
#
# Prefer this over ``T | None | MISSING`` when ``None`` is not a valid domain
# value (DB/read non-null) but may still appear on the wire.
RuntimeNullableField = GetPydanticSchema(_nullable_schema)
