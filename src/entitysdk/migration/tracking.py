"""Execution tracking: operations and snapshots."""

import logging
from enum import StrEnum, auto
from typing import Annotated, Any, NamedTuple
from uuid import UUID

from pydantic import BaseModel, Field

L = logging.getLogger(__name__)


class EntityKey(NamedTuple):
    """Unique identifier for an entity."""

    type: str
    id: UUID

    def __str__(self) -> str:
        return f"{self.type}::{self.id}"

    @classmethod
    def from_string(cls, value: str) -> "EntityKey":
        type_, _, id_ = value.partition("::")
        return cls(type=type_, id=UUID(id_))


class OperationType(StrEnum):
    created = auto()
    updated = auto()
    deleted = auto()
    skipped = auto()


class SnapshotLabel(StrEnum):
    before = auto()
    after = auto()


class ExecutionSummary(BaseModel):
    """Track operations performed during script execution."""

    operations: Annotated[
        dict[OperationType, list[str]],
        Field(description="Entity keys grouped by operation type."),
    ] = {op: [] for op in OperationType}
    snapshots: Annotated[
        dict[str, dict[SnapshotLabel, dict]],
        Field(description="Before/after attribute values keyed by entity key."),
    ] = {}

    def record_operation(self, entity_key: EntityKey, operation: OperationType) -> None:
        self.operations.setdefault(operation, []).append(str(entity_key))

    def record_snapshot(self, entity_key: EntityKey, label: SnapshotLabel, data: Any) -> None:
        self.snapshots.setdefault(str(entity_key), {})[label] = data

    def log_summary(self) -> None:
        counts = ", ".join(
            f"{len(data)} {operation}" for operation, data in self.operations.items()
        )
        L.info(f"Execution summary: {counts}")
