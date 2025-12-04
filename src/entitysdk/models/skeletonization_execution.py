"""Skeletonization execution model."""

from entitysdk.models.execution import Execution
from entitysdk.types import SkeletonizationExecutionStatus


class SkeletonizationExecution(Execution):
    """Skeletonization execution model."""

    status: SkeletonizationExecutionStatus
