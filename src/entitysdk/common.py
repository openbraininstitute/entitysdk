"""Common stuff."""

import re
from uuid import UUID

from pydantic import BaseModel

from entitysdk.exception import EntitySDKError
from entitysdk.types import DeploymentEnvironment

UUID_RE = "[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"


VLAB_URL_PATTERN = re.compile(
    r"^https:\/\/(?P<env>staging|www)\.openbraininstitute\.org"
    rf"\/app\/virtual-lab\/(?P<vlab>{UUID_RE})"
    rf"\/(?P<proj>{UUID_RE})(?:\/.*)?$"
)


class ProjectContext(BaseModel):
    """Project context."""

    project_id: UUID
    # entitycore can deduce the vlab id from the project id
    # therefore it is not mandatory
    virtual_lab_id: UUID | None = None


def parse_vlab_url(url: str) -> tuple[ProjectContext, DeploymentEnvironment]:
    """Build and return ProjectContext and DeploymentEnvironment from a virtual lab url."""
    result = VLAB_URL_PATTERN.match(url)

    if not result:
        raise EntitySDKError(f"Badly formed vlab url: {url}")

    env = {
        "www": DeploymentEnvironment.production,
        "staging": DeploymentEnvironment.staging,
    }[result.group("env")]

    vlab_id = UUID(result.group("vlab"))
    proj_id = UUID(result.group("proj"))

    return ProjectContext(project_id=proj_id, virtual_lab_id=vlab_id), env
