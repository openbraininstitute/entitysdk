"""Generic task config model."""

from typing import Any

from entitysdk.models.entity import Entity
from entitysdk.types import TaskResultType


class TaskResult(Entity):
    """Generic task config model."""

    task_result_type: TaskResultType
    data_payload: dict[str, Any] = {}  # noqa: RUF012
