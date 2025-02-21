"""Serialization and deserialization of entities."""

from entitysdk.base import BaseModel


def deserialize_entity(json_data: dict, model_cls: BaseModel):
    """Deserialize json into entity."""
    return model_cls.model_validate(json_data)


def serialize_entity(entity: BaseModel) -> dict:
    """Serialize entity into json."""
    return entity.model_dump(mode="json", exclude_none=True)
