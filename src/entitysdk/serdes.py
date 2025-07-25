"""Serialization and deserialization of entities."""

from typing import TypeVar

from pydantic import TypeAdapter

from entitysdk.models.activity import Activity
from entitysdk.models.base import BaseModel

SERIALIZATION_EXCLUDE_KEYS = {
    "assets",
    "creation_date",
    "id",
    "update_date",
}

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def deserialize_model(json_data: dict, entity_type: type[TBaseModel]) -> TBaseModel:
    """Deserialize json into entity."""
    return entity_type.model_validate(json_data)


def serialize_model(model: BaseModel) -> dict:
    """Serialize entity into json."""
    if isinstance(model, Activity):
        return _serialize_activity(model)

    data = model.model_dump(
        mode="json",
        exclude=SERIALIZATION_EXCLUDE_KEYS,
        exclude_none=False,
    )
    processed = _convert_identifiables_to_ids(data)
    return processed


def serialize_dict(data: dict) -> dict:
    """Serialize a model dictionary into json."""
    processed = _convert_identifiables_to_ids(data)
    json_data = TypeAdapter(dict).dump_python(processed, mode="json")
    return json_data


def _convert_identifiables_to_ids(data: dict) -> dict:
    result = {}

    for key, value in data.items():
        if isinstance(value, dict):
            if "id" in value:
                new_key = f"{key}_id"
                result[new_key] = value["id"]
            else:
                result[key] = _convert_identifiables_to_ids(value)

        else:
            result[key] = value

    return result


def _serialize_activity(model: Activity) -> dict:
    data = model.model_dump(
        mode="json",
        exclude=SERIALIZATION_EXCLUDE_KEYS,
        exclude_none=False,
    )

    if used := data.pop("used"):
        data["used_ids"] = [u["id"] for u in used]

    if generated := data.pop("generated"):
        data["generated_ids"] = [g["id"] for g in generated]

    data = _convert_identifiables_to_ids(data)
    return data
