"""Reusable Pydantic field types."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, GetPydanticSchema
from pydantic_core import core_schema

from entitysdk.types import ID

NullableId = Annotated[
    ID,
    GetPydanticSchema(lambda _source_type, handler: core_schema.nullable_schema(handler(ID))),
    Field(
        description="The primary key identifier of the resource.",
        default=None,
    ),
]
