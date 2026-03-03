"""Generic task config model."""

from typing import Annotated

from pydantic import Field, SerializationInfo, field_serializer

from entitysdk.models.entity import Entity
from entitysdk.types import ID, SerializeWhen, TaskConfigType


class TaskConfig(Entity):
    """Generic task config model."""

    task_config_type: TaskConfigType
    task_config_generator_id: ID | None = None
    scan_parameters: dict
    inputs: Annotated[
        list[Entity] | None,
        Field(description="List input entities."),
    ] = None

    @field_serializer("inputs", when_used="unless-none")
    def serialize_inputs(
        self, value: list[Entity], info: SerializationInfo
    ) -> list[dict] | list[Entity]:
        """Serialize to IDs for API requests."""
        if any(model.id is None for model in value):
            raise ValueError("All input instances must have an ID for serialization")
        if info.context and info.context.get("when") in {
            SerializeWhen.create,
            SerializeWhen.update,
        }:
            return [{"id": model.id} for model in value]
        # use the default serialization by default
        return value
