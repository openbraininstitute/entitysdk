"""Execution tracking: operations and snapshots."""

import logging
from enum import StrEnum, auto
from typing import Annotated, Any, NamedTuple
from uuid import UUID

from pydantic import BaseModel, Field

from entitysdk import models
from entitysdk.models.core import Identifiable

L = logging.getLogger(__name__)


class EntityKey(NamedTuple):
    """Unique identifier for an entity."""

    type: type[Identifiable]
    id: UUID

    def __str__(self) -> str:
        """Return the string representation as 'type::id'."""
        return f"{self.type.__name__}::{self.id}"

    @classmethod
    def from_string(cls, value: str) -> "EntityKey":
        """Parse an EntityKey from its 'type::id' string representation."""
        type_str, _, id_str = value.partition("::")
        type_class = getattr(models, type_str, None)
        if not type_class:
            raise ValueError(f"Unknown entity type: {type_str}")
        if not issubclass(type_class, Identifiable):
            raise ValueError(f"Invalid entity type: {type_str}")
        return cls(type=type_class, id=UUID(id_str))


class OperationType(StrEnum):
    """Types of operations that can be performed on entities."""

    created = auto()
    updated = auto()
    deleted = auto()
    skipped = auto()  # for ignored records
    failed = auto()  # for failed records


class SnapshotLabel(StrEnum):
    """Labels for before/after entity snapshots."""

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
        """Record an operation performed on an entity."""
        self.operations.setdefault(operation, []).append(str(entity_key))

    def record_snapshot(self, entity_key: EntityKey, label: SnapshotLabel, data: Any) -> None:
        """Record a before/after snapshot of an entity's data."""
        self.snapshots.setdefault(str(entity_key), {})[label] = data

    def log_summary(self) -> None:
        """Log a summary of all recorded operations."""
        counts = ", ".join(
            f"{len(data)} {operation}" for operation, data in self.operations.items()
        )
        L.info(f"Execution summary: {counts}")
