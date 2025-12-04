"""Ion channel modeling execution model."""

from entitysdk.models.execution import Execution
from entitysdk.types import IonChannelModelingExecutionStatus


class IonChannelModelingExecution(Execution):
    """Ion channel modeling execution model."""

    status: IonChannelModelingExecutionStatus
