from entitysdk.mixin import HasAssets
from entitysdk.core import Activity


class WorkflowExecution(HasAssets, Activity):

    module: str
    task: str
    configFileName: str
    status: str
    startedAtTime: datetime
    endedAtTime: datetime | None = None
