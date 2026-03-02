"""Generic task config model."""

from typing import Annotated

from pydantic import Field, field_serializer

from entitysdk.models.entity import Entity
from entitysdk.types import ID, TaskConfigType


class TaskConfig(Entity):
    """Generic task config model."""

    task_config_type: TaskConfigType
    task_config_generator_id: ID | None = None
    scan_parameters: dict
    inputs: Annotated[
        list[Entity] | None,
        Field(description="List input entities."),
    ] = None

    @field_serializer("inputs")
    def serialize_inputs(self, value: list[Entity] | None) -> list[dict] | None:
        """Serialize to IDs for API requests."""
        if value is None:
            return None
        if any(model.id is None for model in value):
            raise ValueError("All input instances must have an ID for serialization")
        return [{"id": model.id} for model in value]
