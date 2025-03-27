import uuid

import pytest

from entitysdk.client import Client
from entitysdk.common import ProjectContext


@pytest.fixture(scope="session")
def api_url():
    return "http://mock-host:8000"


@pytest.fixture(scope="session")
def project_context():
    return ProjectContext(
        project_id=uuid.UUID("103d7868-147e-4f07-af0d-71d8568f575c"),
        virtual_lab_id=uuid.UUID("103d7868-147e-4f07-af0d-71d8568f575c"),
    )


@pytest.fixture(scope="session")
def auth_token():
    return "mock-token"


@pytest.fixture(scope="session")
def request_headers(project_context, auth_token):
    return {
        "project-id": str(project_context.project_id),
        "virtual-lab-id": str(project_context.virtual_lab_id),
        "Authorization": f"Bearer {auth_token}",
    }


@pytest.fixture(scope="session")
def request_headers_no_context(auth_token):
    return {
        "Authorization": f"Bearer {auth_token}",
    }


@pytest.fixture
def client(project_context, api_url):
    return Client(api_url=api_url, project_context=project_context)


@pytest.fixture
def random_uuid():
    return uuid.uuid4()
