"""Execution module."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.activity import Activity
from entitysdk.types import ID, ExecutorType


class Execution(Activity):
    """Execution activity."""

    executor: Annotated[
        ExecutorType | None, Field(description="Executor type that created this activity.")
    ] = None
    execution_id: Annotated[
        ID | None,
        Field("Execution Id"),
    ] = None
