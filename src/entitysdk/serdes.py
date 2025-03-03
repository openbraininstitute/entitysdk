"""Serialization and deserialization of entities."""

from pydantic import TypeAdapter

from entitysdk.models.base import BaseModel

SERIALIZATION_EXCLUDE_KEYS = {
    "assets",
    "creation_date",
    "id",
    "update_date",
}


def deserialize_entity(json_data: dict, entity_type: type[BaseModel]):
    """Deserialize json into entity."""
    return entity_type.model_validate(json_data)


def serialize_entity(entity: BaseModel) -> dict:
    """Serialize entity into json."""
    data = entity.model_dump(
        mode="json",
        exclude=SERIALIZATION_EXCLUDE_KEYS,
        exclude_none=True,
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
