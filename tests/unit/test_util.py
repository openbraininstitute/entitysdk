from unittest.mock import Mock

import pytest

from entitysdk.common import ProjectContext
from entitysdk.util import make_db_api_request


@pytest.fixture
def mock_client():
    return Mock()


def test_make_db_api_request(mock_client: Mock):
    url = "http://localhost:8000/api/v1/entity/person"

    make_db_api_request(
        url=url,
        method="POST",
        json={"name": "John Doe"},
        parameters={"foo": "bar"},
        token="123",
        project_context=ProjectContext(
            project_id="123",
            virtual_lab_id="456",
        ),
        http_client=mock_client,
    )

    mock_client.request.assert_called_once_with(
        method="POST",
        url=url,
        headers={"project-id": "123", "virtual-lab-id": "456", "Authorization": "Bearer 123"},
        json={"name": "John Doe"},
        params={"foo": "bar"},
    )
