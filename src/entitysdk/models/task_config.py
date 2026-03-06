"""Generic task config model."""

from typing import Annotated, Any

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.types import ID, TaskConfigType


class TaskConfig(Entity):
    """Generic task config model."""

    task_config_type: TaskConfigType
    task_config_generator_id: ID | None = None
    meta: dict[str, Any]
    inputs: Annotated[
        list[Entity] | None,
        Field(description="List of input entities."),
    ] = None
