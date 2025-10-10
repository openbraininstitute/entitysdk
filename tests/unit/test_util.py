import json
from unittest.mock import ANY

import httpx
import pytest

from entitysdk import util as test_module
from entitysdk.exception import EntitySDKError, ServerError


def test_make_db_api_request(httpx_mock, api_url, project_context, auth_token, request_headers):
    url = f"{api_url}/api/v1/entity/person"
    httpx_mock.add_response(
        method="POST",
        url=f"{url}?foo=bar",
        match_headers=request_headers,
        match_json={"name": "John Doe"},
    )

    with httpx.Client() as http_client:
        res = test_module.make_db_api_request(
            url=url,
            method="POST",
            json={"name": "John Doe"},
            parameters={"foo": "bar"},
            token=auth_token,
            project_context=project_context,
            http_client=http_client,
        )
        assert res.status_code == 200


def test_make_db_api_request__no_context(
    httpx_mock, api_url, auth_token, request_headers_no_context
):
    url = f"{api_url}/api/v1/entity/person"
    httpx_mock.add_response(
        method="POST",
        url=f"{url}?foo=bar",
        match_headers=request_headers_no_context,
        match_json={"name": "John Doe"},
    )

    with httpx.Client() as http_client:
        res = test_module.make_db_api_request(
            url=url,
            method="POST",
            json={"name": "John Doe"},
            parameters={"foo": "bar"},
            token=auth_token,
            project_context=None,
            http_client=http_client,
        )
        assert res.status_code == 200


def test_make_db_api_request_with_none_http_client__raises_request(
    httpx_mock, api_url, project_context, auth_token
):
    url = f"{api_url}/api/v1/entity/person"
    httpx_mock.add_exception(httpx.RequestError(message="Test"))

    # backwards compatible with EntitySDKError
    with httpx.Client() as http_client:
        with pytest.raises(EntitySDKError, match="Request error: Test"):
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json={"name": "John Doe"},
                parameters={"foo": "bar"},
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )


def test_make_db_api_request_with_none_http_client__raises(
    httpx_mock, api_url, project_context, auth_token
):
    url = f"{api_url}/api/v1/entity/person"
    json_response = {"error_code": "NOT_FOUND", "details": "lorem"}
    httpx_mock.add_response(status_code=404, json=json_response)

    # backwards compatible with EntitySDKError
    with httpx.Client() as http_client:
        with pytest.raises(EntitySDKError, match="404"):
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json={"name": "John Doe"},
                parameters={"foo": "bar"},
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

    httpx_mock.add_response(status_code=404, json=json_response)

    # but now a ServerError can also be caught
    with httpx.Client() as http_client:
        with pytest.raises(ServerError, match="404") as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json={"name": "John Doe"},
                parameters={"foo": "bar"},
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )
        error = exc_info.value
        assert error.details == {
            "request": {
                "method": "POST",
                "url": "http://mock-host:8000/api/v1/entity/person?foo=bar",
                "json": {"name": "John Doe"},
                "text": '{"name":"John Doe"}',
            },
            "response": {
                "status_code": 404,
                "json": {"error_code": "NOT_FOUND", "details": "lorem"},
                "text": '{"error_code":"NOT_FOUND","details":"lorem"}',
            },
        }


def test_make_db_api_request_with_none_http_client__client_none(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    httpx_mock.add_response(
        method="POST",
        url=f"{url}?foo=bar",
        match_headers=request_headers,
        match_json={"name": "John Doe"},
    )

    res = test_module.make_db_api_request(
        url=url,
        method="POST",
        json={"name": "John Doe"},
        parameters={"foo": "bar"},
        project_context=project_context,
        token=auth_token,
        http_client=None,
    )

    assert res.status_code == 200


@pytest.mark.parametrize("limit", [0, -1])
def test_stream_paginated_request_validate_limit(api_url, project_context, auth_token, limit):
    url = f"{api_url}/api/v1/entity/person"
    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=limit,
        project_context=project_context,
        token=auth_token,
    )
    with pytest.raises(EntitySDKError, match="limit must be either None or strictly positive."):
        next(it)


@pytest.mark.parametrize("page_size", [0, -1])
def test_stream_paginated_request_validate_page_size(
    api_url, project_context, auth_token, page_size
):
    url = f"{api_url}/api/v1/entity/person"
    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        page_size=page_size,
        project_context=project_context,
        token=auth_token,
    )
    with pytest.raises(EntitySDKError, match="page_size must be either None or strictly positive."):
        next(it)


def test_stream_paginated_request_one_item(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    httpx_mock.add_response(
        method="GET",
        url=f"{url}?page_size=2&page=1",
        match_headers=request_headers,
        json={
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "page_size": 2, "total_items": 4},
        },
    )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=1,
        project_context=project_context,
        token=auth_token,
        page_size=2,
    )
    assert [item["id"] for item in it] == [1]


def test_stream_paginated_request_two_pages(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 4},
            },
            {
                "data": [{"id": 3}, {"id": 4}],
                "pagination": {"page": 2, "page_size": 2, "total_items": 4},
            },
        ],
        start=1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page_size=2&page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=None,
        project_context=project_context,
        token=auth_token,
        page_size=2,
    )
    assert [item["id"] for item in it] == [1, 2, 3, 4]


def test_stream_paginated_request_two_pages_and_lower_limit(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 4},
            },
            {
                "data": [{"id": 3}, {"id": 4}],
                "pagination": {"page": 2, "page_size": 2, "total_items": 4},
            },
        ],
        start=1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page_size=2&page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=3,
        project_context=project_context,
        token=auth_token,
        page_size=2,
    )
    assert [item["id"] for item in it] == [1, 2, 3]


def test_stream_paginated_request_two_pages_and_higher_limit(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 4},
            },
            {
                "data": [{"id": 3}, {"id": 4}],
                "pagination": {"page": 2, "page_size": 2, "total_items": 4},
            },
        ],
        start=1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page_size=2&page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=5,
        project_context=project_context,
        token=auth_token,
        page_size=2,
    )
    assert [item["id"] for item in it] == [1, 2, 3, 4]


def test_stream_paginated_request_one_page_and_some(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 3},
            },
            {
                "data": [{"id": 3}],
                "pagination": {"page": 2, "page_size": 2, "total_items": 3},
            },
        ],
        start=1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page_size=2&page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        limit=5,
        project_context=project_context,
        token=auth_token,
        page_size=2,
    )
    assert [item["id"] for item in it] == [1, 2, 3]


def test_stream_paginated_request_one_page_exactly(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 2},
            },
        ],
        start=1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=auth_token,
    )
    assert [item["id"] for item in it] == [1, 2]


def test_stream_paginated_request_no_items(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [],
                "pagination": {"page": 1, "page_size": 2, "total_items": 0},
            },
        ],
        1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=auth_token,
    )
    assert [item["id"] for item in it] == []


def test_stream_paginated_request_with_unexpected_page(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 2, "page_size": 2, "total_items": 4},
            },
        ],
        1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page={page}",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=auth_token,
    )
    with pytest.raises(
        EntitySDKError, match="Unexpected response: payload.pagination.page=2 but it should be 1"
    ):
        next(it)


def test_stream_paginated_request_with_unexpected_page_size(
    httpx_mock, api_url, project_context, auth_token, request_headers
):
    url = f"{api_url}/api/v1/entity/person"
    for page, json_response in enumerate(
        [
            {
                "data": [{"id": 1}, {"id": 2}],
                "pagination": {"page": 1, "page_size": 2, "total_items": 2},
            },
        ],
        1,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{url}?page={page}&page_size=123",
            match_headers=request_headers,
            json=json_response,
        )

    it = test_module.stream_paginated_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=auth_token,
        page_size=123,
    )
    with pytest.raises(
        EntitySDKError,
        match="Unexpected response: payload.pagination.page_size=2 but it should be 123",
    ):
        next(it)


def test_validate_filename_extension_consistency(tmp_path):
    assert test_module.validate_filename_extension_consistency(tmp_path / "foo.txt", ".txt")
    assert test_module.validate_filename_extension_consistency(tmp_path / "foo.txt", ".TXT")


def test_create_intermediate_directories(tmp_path):
    path = tmp_path / "foo" / "bar" / "foo.txt"

    assert not path.parent.is_dir()

    test_module.create_intermediate_directories(path)

    assert path.parent.is_dir()
    assert path.parent.parent.is_dir()


def test_server_error_with_html_response(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling when server returns HTML error page instead of JSON."""
    url = f"{api_url}/api/v1/entity/person"
    html_response = """
    <!DOCTYPE html>
    <html>
    <head><title>Error 500</title></head>
    <body>
        <h1>Internal Server Error</h1>
        <p>Something went wrong on our end.</p>
    </body>
    </html>
    """

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=500,
        content=html_response,
        headers={"Content-Type": "text/html"},
    )

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 500,
                "json": None,
                "text": html_response,
            },
        }


def test_server_error_with_plain_text_response(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling when server returns plain text error message."""
    url = f"{api_url}/api/v1/entity/person"
    text_response = "Service temporarily unavailable. Please try again later."

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=503,
        content=text_response,
        headers={"Content-Type": "text/plain"},
    )

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 503,
                "json": None,
                "text": text_response,
            },
        }


def test_server_error_with_empty_response_body(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling when server returns empty response body."""
    url = f"{api_url}/api/v1/entity/person"

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=404,
        content="",
        headers={"Content-Type": "application/json"},
    )

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 404,
                "json": None,
                "text": "",
            },
        }


def test_server_error_with_malformed_json_response(
    httpx_mock, api_url, project_context, auth_token
):
    """Test ServerError handling when server returns malformed JSON."""
    url = f"{api_url}/api/v1/entity/person"
    malformed_json = '{"error": "incomplete json'

    payload = {"name": "John Doe"}

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=500,
        content=malformed_json,
        headers={"Content-Type": "application/json"},
    )

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 500,
                "json": None,
                "text": malformed_json,
            },
        }


def test_server_error_with_form_data_request(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling with form data request payload."""
    url = f"{api_url}/api/v1/entity/person"
    error_response = {"error": "Invalid form data"}

    httpx_mock.add_response(method="POST", url=url, status_code=422, json=error_response)

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                data={"name": "John Doe", "age": "30"},
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": "name=John+Doe&age=30",
                "text": "name=John+Doe&age=30",
            },
            "response": {
                "status_code": 422,
                "json": error_response,
                "text": _compact_dumps(error_response),
            },
        }


def test_server_error_with_file_upload_request(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling with file upload request."""
    url = f"{api_url}/api/v1/entity/person"
    error_response = {"error": "File upload failed", "code": "FILE_TOO_LARGE"}

    httpx_mock.add_response(method="POST", url=url, status_code=413, json=error_response)

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                files={"file": ("test.txt", b"test content", "text/plain")},
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": ANY,
                "text": ANY,
            },
            "response": {
                "status_code": 413,
                "json": error_response,
                "text": _compact_dumps(error_response),
            },
        }


def test_server_error_with_empty_json_object(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling with empty JSON object response."""
    url = f"{api_url}/api/v1/entity/person"

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=500,
        json={},  # Empty JSON object
    )

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 500,
                "json": {},
                "text": "{}",
            },
        }


def _compact_dumps(data):
    return json.dumps(data, separators=(",", ":"))


def test_server_error_with_null_json_response(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling with null JSON response."""
    url = f"{api_url}/api/v1/entity/person"

    httpx_mock.add_response(
        method="POST",
        url=url,
        status_code=500,
        json=None,  # Null JSON
    )

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 500,
                "json": None,
                "text": "",
            },
        }


def test_server_error_with_array_json_response(httpx_mock, api_url, project_context, auth_token):
    """Test ServerError handling with JSON array response."""
    url = f"{api_url}/api/v1/entity/person"
    array_error_response = [
        {"error": "First error"},
        {"error": "Second error"},
        {"error": "Third error"},
    ]

    httpx_mock.add_response(method="POST", url=url, status_code=400, json=array_error_response)

    payload = {"name": "John Doe"}

    with httpx.Client() as http_client:
        with pytest.raises(ServerError) as exc_info:
            test_module.make_db_api_request(
                url=url,
                method="POST",
                json=payload,
                project_context=project_context,
                token=auth_token,
                http_client=http_client,
            )

        assert exc_info.value.details == {
            "request": {
                "method": "POST",
                "url": url,
                "json": payload,
                "text": _compact_dumps(payload),
            },
            "response": {
                "status_code": 400,
                "json": array_error_response,
                "text": _compact_dumps(array_error_response),
            },
        }
