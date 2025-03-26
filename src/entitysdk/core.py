"""Core SDK operations."""

import io
from collections.abc import Iterator
from pathlib import Path

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.core import Identifiable
from entitysdk.result import IteratorResult
from entitysdk.util import make_db_api_request, stream_paginated_request


def search_entities(
    url: str,
    *,
    entity_type: type[Identifiable],
    query: dict | None = None,
    limit: int | None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> IteratorResult[Identifiable]:
    """Search for entities.

    Args:
        url: URL of the resource.
        entity_type: Type of the entity.
        query: Query parameters
        limit: Limit of the number of entities to yield or None.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        List of entities.
    """
    iterator: Iterator[dict] = stream_paginated_request(
        url=url,
        method="GET",
        parameters=query,
        limit=limit,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return IteratorResult(
        serdes.deserialize_entity(json_data, entity_type) for json_data in iterator
    )


def get_entity(
    url: str,
    *,
    entity_type: type[Identifiable],
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Instantiate entity with model ``entity_type`` from resource id."""
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    return serdes.deserialize_entity(response.json(), entity_type)


def get_entity_assets(
    url: str,
    *,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> list[Asset]:
    """Get entity assets.

    Args:
        url: URL of the resource.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        List of assets.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return [serdes.deserialize_entity(asset, Asset) for asset in response.json()["data"]]


def register_entity(
    url: str,
    *,
    entity: Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Register entity."""
    json_data = serdes.serialize_entity(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), type(entity))


def update_entity(
    url: str,
    *,
    entity_type: type[Identifiable],
    attrs_or_entity: dict | Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Update entity."""
    if isinstance(attrs_or_entity, dict):
        json_data = serdes.serialize_dict(attrs_or_entity)
    else:
        json_data = serdes.serialize_entity(attrs_or_entity)

    response = make_db_api_request(
        url=url,
        method="PATCH",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    json_data = response.json()

    return serdes.deserialize_entity(json_data, entity_type)


def upload_asset_file(
    url: str,
    *,
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file path."""
    with open(asset_path, "rb") as file_content:
        return upload_asset_content(
            url=url,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token=token,
            http_client=http_client,
        )


def upload_asset_content(
    url: str,
    *,
    asset_content: io.BufferedIOBase,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file-like object."""
    files = {
        "file": (
            asset_metadata.file_name,
            asset_content,
            asset_metadata.content_type,
        )
    }
    response = make_db_api_request(
        url=url,
        method="POST",
        files=files,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), Asset)


def download_asset_file(
    url: str,
    *,
    output_path: Path,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> None:
    """Download asset file to a file path.

    Args:
        url: URL of the asset.
        output_path: Path to save the file to.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.
    """
    bytes_content = download_asset_content(
        url=url,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    output_path.write_bytes(bytes_content)


def download_asset_content(
    url: str,
    *,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> bytes:
    """Download asset content.

    Args:
        url: URL of the asset.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        Asset content in bytes.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return response.content


def delete_asset(
    url: str,
    *,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Delete asset."""
    response = make_db_api_request(
        url=url,
        method="DELETE",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), Asset)
