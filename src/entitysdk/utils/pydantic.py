"""Pydantic helpers for static/runtime field typing."""

from typing import Any

from pydantic import GetCoreSchemaHandler, GetPydanticSchema
from pydantic_core import core_schema


def _nullable_schema(source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap a field schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(source_type))


# Entity models share one class across staging, registration, and fetch. Metadata
# fields are often unset (``None``, omitted, or JSON ``null``), but after
# ``get_entity`` callers want checkers to treat them as ``T``, not ``T | None``.
#
# ``Annotated[T, RuntimeNullableField]`` bridges that gap:
# pyright keeps ``T``, while ``RuntimeNullableField`` wraps the schema with
# ``nullable_schema`` so Pydantic accepts ``None``. Use ``= None`` with
# ``# type: ignore[assignment]`` on the default only. Example:
# ``entitysdk.models.core.Identifiable``.
RuntimeNullableField = GetPydanticSchema(_nullable_schema)
