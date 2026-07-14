"""Reusable Pydantic field types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import Field, GetCoreSchemaHandler
from pydantic_core import core_schema

from entitysdk.types import ID


@dataclass(frozen=True)
class _NullableId:
    """Pydantic metadata: validate as UUID when set, otherwise accept ``None``."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.nullable_schema(handler(ID))


NullableId = Annotated[
    ID,
    _NullableId,
    Field(
        description="The primary key identifier of the resource.",
        default=None,
    ),
]
