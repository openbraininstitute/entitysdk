"""Skeletonization execution model."""

from entitysdk.models.activity import Activity
from entitysdk.types import SkeletonizationExecutionStatus


class SkeletonizationExecution(Activity):
    """Skeletonization execution model."""

    status: SkeletonizationExecutionStatus
