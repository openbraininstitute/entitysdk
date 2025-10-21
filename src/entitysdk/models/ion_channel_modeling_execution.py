"""Ion channel modeling execution model."""

from entitysdk.models.activity import Activity
from entitysdk.types import IonChannelModelingExecutionStatus


class IonChannelModelingExecution(Activity):
    """Ion channel modeling execution model."""

    status: IonChannelModelingExecutionStatus
