"""Utility functions."""

import sys
from collections.abc import Iterator
from json import dumps

import httpx

from entitysdk.common import ProjectContext
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.models.response import ListResponse
from entitysdk.types import DeploymentEnvironment


def make_db_api_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    parameters: dict | None = None,
    files: dict | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    """Make a request to entitycore api."""
    if http_client is None:
        http_client = httpx.Client()

    headers = {"Authorization": f"Bearer {token}"}

    if project_context:
        headers["project-id"] = str(project_context.project_id)
        headers["virtual-lab-id"] = str(project_context.virtual_lab_id)

    try:
        response = http_client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            files=files,
            params=parameters,
            follow_redirects=True,
        )
    except httpx.RequestError as e:
        raise EntitySDKError(f"Request error: {e}") from e

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        message = (
            f"HTTP error {response.status_code} for {method} {url}\n"
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
    http_client: httpx.Client | None = None,
    page_size: int | None = None,
    limit: int | None = None,
    token: str,
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
        token: The token to use.

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
            token=token,
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


def build_api_url(environment: DeploymentEnvironment) -> str:
    """Return API url for the respective deployment environment."""
    return {
        DeploymentEnvironment.staging: settings.staging_api_url,
        DeploymentEnvironment.production: settings.production_api_url,
    }[environment]
