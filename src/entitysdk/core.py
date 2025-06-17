"""Core SDK operations."""

import io
import os
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.models.asset import Asset, DetailedFileList, LocalAssetMetadata
from entitysdk.models.core import Identifiable
from entitysdk.result import IteratorResult
from entitysdk.util import make_db_api_request, stream_paginated_request

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)


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
    entity_type: type[TIdentifiable],
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> TIdentifiable:
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


def upload_asset_directory(
    url: str,
    *,
    directory_path: Path,
    metadata: dict | None = None,
    label: str | None = None,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload directory to an existing entity's endpoint from a directory path."""
    files = []
    for path in directory_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):  # skip hidden
            continue
        files.append(str(path.relative_to(directory_path)))

    response = make_db_api_request(
        url=url,
        method="POST",
        project_context=project_context,
        token=token,
        http_client=http_client,
        json={"files": files, "meta": metadata, "label": label},
    )

    js = response.json()

    def upload(to_upload):
        failed = {}
        for path, url in to_upload.items():
            with open(directory_path / path, "rb") as fd:
                response = http_client.request(
                    method="PUT", url=url, content=fd, follow_redirects=True
                )
            if response.status_code != 200:
                failed[path] = url
        return failed

    to_upload = js["files"]
    for _ in range(3):
        to_upload = upload(to_upload)
        if not to_upload:
            break

    if to_upload:
        raise Exception(f"Uploading these files failed: {to_upload}", to_upload)

    return serdes.deserialize_entity(js["asset"], Asset)


def list_directory(
    url: str,
    *,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> DetailedFileList:
    """List all files within an asset directory."""
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), DetailedFileList)


def download_asset_file(
    url: str,
    *,
    output_path: Path,
    asset_path: os.PathLike | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> Path:
    """Download asset file to a file path.

    Args:
        url: URL of the asset.
        output_path: Path to save the file to.
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        Output file path.
    """
    bytes_content = download_asset_content(
        url=url,
        asset_path=asset_path,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    output_path.write_bytes(bytes_content)
    return output_path


def download_asset_content(
    url: str,
    *,
    asset_path: os.PathLike | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> bytes:
    """Download asset content.

    Args:
        url: URL of the asset.
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        Asset content in bytes.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        parameters={"asset_path": str(asset_path)} if asset_path else {},
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
