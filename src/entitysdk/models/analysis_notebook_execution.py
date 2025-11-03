"""Analysis notebook execution model."""

from entitysdk.models.activity import Activity
from entitysdk.models.analysis_notebook_environment import AnalysisNotebookEnvironment
from entitysdk.models.analysis_notebook_template import AnalysisNotebookTemplate


class AnalysisNotebookExecution(Activity):
    """Analysis notebook execution model."""

    analysis_notebook_template: AnalysisNotebookTemplate | None
    analysis_notebook_environment: AnalysisNotebookEnvironment
