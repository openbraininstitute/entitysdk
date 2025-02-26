from unittest.mock import Mock

import pytest

from entitysdk.client import Client
from entitysdk.common import ProjectContext


@pytest.fixture(scope="session")
def api_url():
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def project_context():
    return ProjectContext(
        project_id="103d7868-147e-4f07-af0d-71d8568f575c",
        virtual_lab_id="103d7868-147e-4f07-af0d-71d8568f575c",
    )


@pytest.fixture
def client(project_context, api_url):
    return Client(api_url=api_url, project_context=project_context, http_client=Mock())
