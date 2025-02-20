"""Common stuff."""

from dataclasses import dataclass


@dataclass
class ProjectContext:
    """Project context."""

    project_id: str
    virtual_lab_id: str
