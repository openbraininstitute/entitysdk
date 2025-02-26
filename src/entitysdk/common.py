"""Common stuff."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProjectContext:
    """Project context."""

    project_id: UUID
    virtual_lab_id: UUID
