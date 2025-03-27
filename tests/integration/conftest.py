import os

import pytest

from entitysdk.client import Client
from entitysdk.common import ProjectContext


@pytest.fixture(scope="session")
def api_url():
    return os.environ["DB_API_URL"]


@pytest.fixture(scope="session")
def token():
    return os.getenv("ACCESS_TOKEN", "mock-token")


@pytest.fixture(scope="session")
def project_context():
    return ProjectContext(
        virtual_lab_id="a98b7abc-fc46-4700-9e3d-37137812c730",
        project_id="0dbced5f-cc3d-488a-8c7f-cfb8ea039dc6",
    )


@pytest.fixture(scope="session")
def client(project_context, api_url, token):
    class MockTokenManager:
        def get_token(self):
            return token

    return Client(api_url=api_url, token_manager=MockTokenManager())
