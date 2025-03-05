"""Utility functions."""

from collections.abc import Iterator
from json import dumps

import httpx

from entitysdk.common import ProjectContext
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError


def make_db_api_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    parameters: dict | None = None,
    files: dict | None = None,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    """Make a request to entitycore api."""
    if http_client is None:
        http_client = httpx.Client()

    try:
        response = http_client.request(
            method=method,
            url=url,
            headers={
                "project-id": str(project_context.project_id),
                "virtual-lab-id": str(project_context.virtual_lab_id),
                "Authorization": f"Bearer {token}",
            },
            json=json,
            files=files,
            params=parameters,
            follow_redirects=True,
        )
    except httpx.RequestError as e:
        raise EntitySDKError(f"Request error: {e}") from e

    try:
        response.raise_for_status()
    except httpx.HTTPError as e:
        message = (
            f"{method} {url}\n"
            f"json : {dumps(json, indent=2)}\n"
            f"params : {parameters}\n"
            f"response : {response.text}"
        )
        raise EntitySDKError(message) from e
    return response


def stream_paginated_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    parameters: dict | None = None,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
    page_size: int = settings.page_size,
    limit: int,
) -> Iterator[dict]:
    """Paginate a request to entitycore api.

    Args:
        url: The url to request.
        method: The method to use.
        json: The json to send.
        parameters: The parameters to send.
        project_context: The project context.
        token: The token to use.
        http_client: The http client to use.
        page_size: The page size to use.
        limit: Limit the number of entities to return. Zero means no limit.

    Returns:
        An iterator of dicts.
    """
    page = 1
    number_of_items = 0
    base_parameters = (parameters or {}) | {"page_size": page_size}
    while True:
        response = make_db_api_request(
            url=url,
            method=method,
            json=json,
            parameters=base_parameters | {"page": page},
            project_context=project_context,
            token=token,
            http_client=http_client,
        )
        json_data = response.json()["data"]

        if not json_data:
            return

        for data in json_data:
            yield data
            number_of_items += 1

            if limit > 0 and number_of_items == limit:
                return

        page += 1
