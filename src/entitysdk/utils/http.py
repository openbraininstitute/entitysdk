"""Utility functions."""

import sys
from collections.abc import Iterator
from json import dumps

import httpx2

from entitysdk.common import ProjectContext
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.models.response import ListResponse
from entitysdk.token_manager import TokenManager

# httpx2 is imported only in this module. Other code should use these aliases so we can
# swap or upgrade the HTTP client library in one place without touching the rest of the codebase.
HTTPClient = httpx2.Client
HTTPTimeout = httpx2.Timeout
ConnectError = httpx2.ConnectError
ReadTimeout = httpx2.ReadTimeout
RemoteProtocolError = httpx2.RemoteProtocolError
RequestError = httpx2.RequestError
HTTPStatusError = httpx2.HTTPStatusError
WriteTimeout = httpx2.WriteTimeout


def make_db_api_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    data: dict | None = None,
    parameters: dict | None = None,
    files: dict | None = None,
    project_context: ProjectContext | None = None,
    token_manager: TokenManager,
    http_client: HTTPClient,
) -> httpx2.Response:
    """Make a request to entitycore api."""
    token = token_manager.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    if project_context:
        headers["project-id"] = str(project_context.project_id)

        # entitycore can deduce the vlab id from the project id
        # therefore it is not mandatory
        if vlab_id := project_context.virtual_lab_id:
            headers["virtual-lab-id"] = str(vlab_id)

    try:
        response = http_client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            files=files,
            data=data,
            params=parameters,
            follow_redirects=True,
            timeout=HTTPTimeout(
                connect=settings.connect_timeout,
                read=settings.read_timeout,
                write=settings.write_timeout,
                pool=settings.pool_timeout,
            ),
        )
    except RequestError as e:
        raise EntitySDKError(f"Request error: {e}") from e

    try:
        response.raise_for_status()
    except HTTPStatusError as e:
        message = (
            f"HTTP error {response.status_code} for {method} {url}\n"
            f"data       : {data}\n"
            f"json       : {dumps(json, indent=2)}\n"
            f"params     : {parameters}\n"
            f"response   : {response.text}"
        )
        raise EntitySDKError(message) from e
    return response


def stream_paginated_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    parameters: dict | None = None,
    project_context: ProjectContext | None = None,
    http_client: HTTPClient,
    page_size: int | None = None,
    limit: int | None = None,
    token_manager: TokenManager,
) -> Iterator[dict]:
    """Paginate a request to entitycore api.

    Args:
        url: The url to request.
        method: The method to use.
        json: The json to send.
        parameters: The parameters to send.
        project_context: The project context.
        http_client: The http client to use.
        page_size: The page size to use, or None to use server default.
        limit: Limit the number of entities to return. Default is None.
        token_manager: The token_manager to issue tokens.

    Returns:
        An iterator of dicts.
    """
    if limit is not None and limit <= 0:
        raise EntitySDKError("limit must be either None or strictly positive.")
    if page_size is not None and page_size <= 0:
        raise EntitySDKError("page_size must be either None or strictly positive.")

    page = 1
    number_of_items = 0
    limit = limit or sys.maxsize
    parameters = parameters or {}
    if page_size := page_size or settings.page_size:
        parameters = parameters | {"page_size": page_size}
    while True:
        response = make_db_api_request(
            url=url,
            method=method,
            json=json,
            parameters=parameters | {"page": page},
            project_context=project_context,
            token_manager=token_manager,
            http_client=http_client,
        )
        payload = ListResponse.model_validate_json(response.text)
        if payload.pagination.page != page:
            raise EntitySDKError(
                f"Unexpected response: {payload.pagination.page=} but it should be {page}"
            )
        if page_size and payload.pagination.page_size != page_size:
            raise EntitySDKError(
                f"Unexpected response: {payload.pagination.page_size=} but it should be {page_size}"
            )
        if not payload.data:
            return
        limit = min(payload.pagination.total_items, limit)
        for data in payload.data:
            yield data
            number_of_items += 1
            if number_of_items >= limit:
                return
        page += 1


def stream_response(
    *,
    url: str,
    method: str,
    headers: dict[str, str] | None = None,
    parameters: dict | None = None,
    http_client: HTTPClient,
) -> Iterator[bytes]:
    """Stream an HTTP response body.

    Args:
        url: The URL to request.
        method: HTTP method.
        headers: Optional request headers.
        parameters: Optional query parameters.
        http_client: HTTP client to use.

    Returns:
        An iterator over response bytes chunks.
    """
    try:
        with http_client.stream(
            method,
            url=url,
            headers=headers,
            params=parameters,
            follow_redirects=True,
            timeout=HTTPTimeout(
                connect=settings.connect_timeout,
                read=settings.read_timeout,
                write=settings.write_timeout,
                pool=settings.pool_timeout,
            ),
        ) as response:
            response.raise_for_status()
            yield from response.iter_bytes(chunk_size=settings.download_stream_data_buffer_size)
    except RequestError as e:
        raise EntitySDKError(f"Request error: {e}") from e
    except HTTPStatusError as e:
        raise EntitySDKError(f"HTTP error {e.response.status_code} for {method} {url}") from e
