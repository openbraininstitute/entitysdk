import uuid

import pytest

from entitysdk.client import Client
from entitysdk.common import ProjectContext
from tests.unit.util import PROJECT_ID, VIRTUAL_LAB_ID


@pytest.fixture(scope="session")
def api_url():
    return "http://mock-host:8000"


@pytest.fixture(scope="session")
def project_context():
    return ProjectContext(
        project_id=PROJECT_ID,
        virtual_lab_id=VIRTUAL_LAB_ID,
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
def client(project_context, api_url, auth_token):
    return Client(api_url=api_url, project_context=project_context, token_manager=auth_token)


@pytest.fixture
def random_uuid():
    return uuid.uuid4()
