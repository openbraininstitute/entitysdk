"""Utility functions."""

from json import dumps

import httpx

from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError


def make_db_api_request(
    url: str,
    *,
    method: str,
    json: dict | None = None,
    parameters: dict | None = None,
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
            params=parameters,
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
