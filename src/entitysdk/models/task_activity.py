"""Generic task activity model."""

from entitysdk.models.execution import Execution
from entitysdk.types import TaskActivityType


class TaskActivity(Execution):
    """Generic task activity model."""

    task_activity_type: TaskActivityType
