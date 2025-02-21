"""Utility functions."""

import httpx

from entitysdk.common import ProjectContext


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

    response = http_client.request(
        method=method,
        url=url,
        headers={
            "project-id": project_context.project_id,
            "virtual-lab-id": project_context.virtual_lab_id,
            "Authorization": f"Bearer {token}",
        },
        json=json,
        params=parameters,
    )

    return response
