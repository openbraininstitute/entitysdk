"""Reusable Pydantic field types."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, GetPydanticSchema
from pydantic_core import core_schema

from entitysdk.types import ID

# Identifiable models use a single Pydantic class for every lifecycle stage (staging,
# registration, fetch, update). At runtime, ``id`` is often unset:
#
# - new entities built in memory before ``register_entity``
# - JSON payloads with ``"id": null`` or the field omitted
# - nested models deserialized before the server assigns an id
#
# After a successful fetch, callers rely on static checkers treating ``res.id`` as
# ``ID``, not ``ID | None`` (for example ``id_res: ID = res.id`` in client code).
#
# A plain ``id: ID | None`` annotation would be honest at runtime but would force
# every consumer to narrow or assert, even right after ``get_entity``. Conversely,
# ``id: ID = Field(default=None)`` satisfies pyright but Pydantic v2 rejects
# ``None`` values because ``ID`` is not nullable in the core schema.
#
# ``NullableId`` bridges that gap:
#
# - the annotated type stays ``ID``, so pyright reports ``.id`` as ``ID``
# - ``GetPydanticSchema`` wraps the UUID schema with ``nullable_schema``, so
#   Pydantic accepts ``None``, an explicit ``id=None``, and ``"id": null`` in JSON
# - ``Field(default=None)`` keeps the default unset for staging and registration
#
# ``Identifiable`` still uses ``id: NullableId = None  # type: ignore[assignment]``
# because the default value is ``None`` while the static field type is ``ID``; the
# ignore applies only to that default assignment, not to uses of ``.id`` afterward.
NullableId = Annotated[
    ID,
    GetPydanticSchema(lambda _source_type, handler: core_schema.nullable_schema(handler(ID))),
    Field(
        description="The primary key identifier of the resource.",
        default=None,
    ),
]
