"""Analysis notebook execution model."""

from entitysdk.models.analysis_notebook_environment import AnalysisNotebookEnvironment
from entitysdk.models.analysis_notebook_template import AnalysisNotebookTemplate
from entitysdk.models.execution import Execution


class AnalysisNotebookExecution(Execution):
    """Analysis notebook execution model."""

    analysis_notebook_template: AnalysisNotebookTemplate | None
    analysis_notebook_environment: AnalysisNotebookEnvironment
