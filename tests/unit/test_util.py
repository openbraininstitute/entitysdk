from unittest.mock import Mock, patch

import httpx
import pytest

from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
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
        follow_redirects=True,
        files=None,
    )


def test_make_db_api_request_with_none_http_client__raises_request(mock_client: Mock):
    url = "http://localhost:8000/api/v1/entity/person"

    mock_client.request.side_effect = httpx.RequestError(message="Test")

    with pytest.raises(EntitySDKError, match="Request error: Test"):
        make_db_api_request(
            url=url,
            method="POST",
            json={"name": "John Doe"},
            parameters={"foo": "bar"},
            project_context=ProjectContext(
                project_id="123",
                virtual_lab_id="456",
            ),
            token="123",
            http_client=mock_client,
        )


def test_make_db_api_request_with_none_http_client__raises(mock_client: Mock):
    url = "http://localhost:8000/api/v1/entity/person"

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="404 Not Found", request=Mock(), response=Mock(status_code=404)
    )
    mock_client.request.return_value = mock_response

    with pytest.raises(EntitySDKError, match="person"):
        make_db_api_request(
            url=url,
            method="POST",
            json={"name": "John Doe"},
            parameters={"foo": "bar"},
            project_context=ProjectContext(
                project_id="123",
                virtual_lab_id="456",
            ),
            token="123",
            http_client=mock_client,
        )


@patch("entitysdk.util.httpx")
def test_make_db_api_request_with_none_http_client__client_none(mock_httpx: Mock):
    # Create a mock response with status_code 200
    mock_response = Mock(status_code=200)
    # Set up the mock chain to return our mock response
    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_httpx.Client.return_value = mock_client

    res = make_db_api_request(
        url="foo",
        method="POST",
        json={"name": "John Doe"},
        parameters={"foo": "bar"},
        project_context=ProjectContext(
            project_id="123",
            virtual_lab_id="456",
        ),
        token="123",
        http_client=None,
    )

    assert res.status_code == 200
