"""Pydantic helpers for static/runtime field typing."""

from types import NoneType, UnionType
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import MISSING, BaseModel, GetCoreSchemaHandler, GetPydanticSchema, ValidationError
from pydantic_core import core_schema


def _nullable_schema(source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
    """Wrap a field schema so Pydantic accepts ``None`` at runtime."""
    return core_schema.nullable_schema(handler(source_type))


# Prefer ``T = MISSING`` for create-omit when reads always send concrete values
# (e.g. Identifiable.id). Use ``RuntimeNullableField`` only when the wire may
# send JSON null while the annotation stays ``T`` (e.g. authorized_project_id
# omitted on NestedEntityBareRead / present on EntityRead).
#
# Annotate as ``T`` (not ``T | MISSING`` — pyright does not erase MISSING).
# On deserialize, non-nullable fields left as ``MISSING`` raise unless the
# field is ``T | None`` or marked ``RuntimeNullableField``.
RuntimeNullableField = GetPydanticSchema(_nullable_schema)


def _annotation_allows_none(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Annotated:
        return _annotation_allows_none(get_args(annotation)[0])
    if origin is Union or origin is UnionType:
        return any(arg is NoneType or arg is type(None) for arg in get_args(annotation))
    return annotation is NoneType or annotation is type(None)


def _field_allows_missing(field: Any) -> bool:
    if _annotation_allows_none(field.annotation):
        return True
    return any(meta is RuntimeNullableField for meta in field.metadata)


def reject_missing_non_nullable_fields(model: BaseModel) -> None:
    """Raise if top-level non-nullable fields are still ``MISSING`` after deserialize.

    Nested expansions are often partial; only the root resource is checked.
    ``T | None`` and ``RuntimeNullableField`` may remain ``MISSING`` when omitted.
    """
    missing_fields = [
        name
        for name, field in type(model).model_fields.items()
        if getattr(model, name) is MISSING and not _field_allows_missing(field)
    ]
    if not missing_fields:
        return

    raise ValidationError.from_exception_data(
        title=type(model).__name__,
        line_errors=[
            {
                "type": "missing",
                "loc": (name,),
                "input": MISSING,
            }
            for name in missing_fields
        ],
    )
