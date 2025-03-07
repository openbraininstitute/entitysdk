from datetime import datetime

from entitysdk.mixin import HasAssets
from entitysdk.models.core import Activity


class WorkflowExecution(HasAssets, Activity):
    module: str
    task: str
    configFileName: str
    status: str
    startedAtTime: datetime
    endedAtTime: datetime | None = None
