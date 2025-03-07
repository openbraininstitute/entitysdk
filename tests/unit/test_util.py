from unittest.mock import Mock, patch

import httpx
import pytest

from entitysdk import util as test_module
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError


@pytest.fixture
def mock_client():
    return Mock()


def test_make_db_api_request(mock_client: Mock):
    url = "http://localhost:8000/api/v1/entity/person"

    test_module.make_db_api_request(
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
        test_module.make_db_api_request(
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
        test_module.make_db_api_request(
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

    res = test_module.make_db_api_request(
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


def test_stream_paginated_request(mock_client: Mock, project_context: ProjectContext):
    request_count = 0

    def mock_request(*args, **kwargs):
        nonlocal request_count

        # Simulate the end of the pagination
        if request_count == 2:
            return Mock(json=lambda: {"data": []})

        request_count += 1
        return Mock(json=lambda: {"data": [{"id": 1}, {"id": 2}]})

    mock_client.request = mock_request

    request_count = 0

    with pytest.raises(EntitySDKError, match="Limit must be None or strictly positive."):
        test_module.stream_paginated_request(
            url="foo",
            method="POST",
            limit=0,
            project_context=project_context,
            token="123",
            http_client=mock_client,
        )

    request_count = 0

    with pytest.raises(EntitySDKError, match="Limit must be None or strictly positive."):
        test_module.stream_paginated_request(
            url="foo",
            method="POST",
            limit=-1,
            project_context=project_context,
            token="123",
            http_client=mock_client,
        )

    res = test_module.stream_paginated_request(
        url="foo",
        method="POST",
        limit=1,
        project_context=project_context,
        token="123",
        http_client=mock_client,
    )
    assert len(list(res)) == 1

    request_count = 0

    res = test_module.stream_paginated_request(
        url="foo",
        method="POST",
        limit=None,
        project_context=project_context,
        token="123",
        http_client=mock_client,
    )
    assert len(list(res)) == 4

    request_count = 0

    res = test_module.stream_paginated_request(
        url="foo",
        method="POST",
        limit=3,
        project_context=project_context,
        token="123",
        http_client=mock_client,
    )
    assert len(list(res)) == 3

    request_count = 0

    res = test_module.stream_paginated_request(
        url="foo",
        method="POST",
        limit=5,
        project_context=project_context,
        token="123",
        http_client=mock_client,
        page_size=2,
    )
    assert len(list(res)) == 4
