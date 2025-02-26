from unittest.mock import Mock

import pytest

from entitysdk.client import Client
from entitysdk.common import ProjectContext


@pytest.fixture
def project_context():
    return ProjectContext(
        project_id="103d7868-147e-4f07-af0d-71d8568f575c",
        virtual_lab_id="103d7868-147e-4f07-af0d-71d8568f575c",
    )


@pytest.fixture
def client(project_context):
    return Client(
        api_url="http://localhost:8000", project_context=project_context, http_client=Mock()
    )
