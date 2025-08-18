"""Common stuff."""

import re
import sys
from uuid import UUID

from pydantic import BaseModel

from entitysdk.exception import EntitySDKError
from entitysdk.types import DeploymentEnvironment

if sys.version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Self
else:
    from typing import Self

UUID_RE = "[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"


VLAB_URL_PATTERN = re.compile(
    r"^https:\/\/(?P<env>staging|www)\.openbraininstitute\.org"
    rf"\/app\/virtual-lab\/lab\/(?P<vlab>{UUID_RE})"
    rf"\/project\/(?P<proj>{UUID_RE})(?:\/.*)?$"
)


class ProjectContext(BaseModel):
    """Project context."""

    project_id: UUID
    virtual_lab_id: UUID
    environment: DeploymentEnvironment | None = None

    @classmethod
    def from_vlab_url(cls, url: str) -> Self:
        """Construct a ProjectContext from a virtual lab url."""
        result = VLAB_URL_PATTERN.match(url)

        if not result:
            raise EntitySDKError(f"Badly formed vlab url: {url}")

        env = {
            "www": DeploymentEnvironment.production,
            "staging": DeploymentEnvironment.staging,
        }[result.group("env")]

        vlab_id = UUID(result.group("vlab"))
        proj_id = UUID(result.group("proj"))

        return cls(project_id=proj_id, virtual_lab_id=vlab_id, environment=env)
