"""Core SDK operations."""

import io
import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.config import settings
from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import (
    Asset,
    DetailedFileList,
    ExistingAssetMetadata,
    LocalAssetMetadata,
)
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.result import IteratorResult
from entitysdk.route import get_assets_endpoint, get_entity_derivations_endpoint
from entitysdk.store import LocalAssetStore
from entitysdk.types import ID, AssetLabel, DerivationType
from entitysdk.util import (
    create_intermediate_directories,
    make_db_api_request,
    stream_paginated_request,
    validate_filename_extension_consistency,
)

L = logging.getLogger(__name__)

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)


def search_entities(
    url: str,
    *,
    entity_type: type[TIdentifiable],
    query: dict | None = None,
    limit: int | None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
) -> IteratorResult[TIdentifiable]:
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
        serdes.deserialize_model(json_data, entity_type) for json_data in iterator
    )


def get_entity(
    url: str,
    *,
    entity_type: type[TIdentifiable],
    project_context: ProjectContext | None = None,
    token: str,
    options: dict | None = None,
    http_client: httpx.Client | None = None,
) -> TIdentifiable:
    """Instantiate entity with model ``entity_type`` from resource id."""
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        parameters=options,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    return serdes.deserialize_model(response.json(), entity_type)


def get_entity_derivations(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext,
    derivation_type: DerivationType,
    token: str,
    http_client: httpx.Client | None = None,
) -> IteratorResult[Entity]:
    """Get derivations for entity."""
    url = get_entity_derivations_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    params = {"derivation_type": DerivationType(derivation_type)}

    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
        parameters=params,
    )
    return IteratorResult(
        serdes.deserialize_model(json_data, Entity) for json_data in response.json()["data"]
    )


def get_entity_assets(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token: str,
    http_client: httpx.Client | None = None,
    admin: bool = False,
):
    """Get all assets of an entity."""
    url = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=None,
        admin=admin,
    )
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return IteratorResult(
        serdes.deserialize_model(json_data, Asset) for json_data in response.json()["data"]
    )


def register_entity(
    url: str,
    *,
    entity: TIdentifiable,
    project_context: ProjectContext | None,
    token: str,
    http_client: httpx.Client | None = None,
) -> TIdentifiable:
    """Register entity."""
    json_data = serdes.serialize_model(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), type(entity))


def update_entity(
    url: str,
    *,
    entity_type: type[TIdentifiable],
    attrs_or_entity: dict | Identifiable,
    project_context: ProjectContext | None,
    token: str,
    http_client: httpx.Client | None = None,
) -> TIdentifiable:
    """Update entity."""
    if isinstance(attrs_or_entity, dict):
        json_data = serdes.serialize_dict(attrs_or_entity)
    else:
        json_data = serdes.serialize_model(attrs_or_entity)

    response = make_db_api_request(
        url=url,
        method="PATCH",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    json_data = response.json()

    return serdes.deserialize_model(json_data, entity_type)


def delete_entity(
    url: str,
    *,
    entity_type: type[Identifiable],
    token: str,
    http_client: httpx.Client | None = None,
) -> None:
    """Delete entity."""
    make_db_api_request(
        url=url,
        method="DELETE",
        token=token,
        http_client=http_client,
    )


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
        data={"label": asset_metadata.label} if asset_metadata.label else None,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)


def upload_asset_directory(
    url: str,
    *,
    name: str,
    paths: dict[Path, Path],
    metadata: dict | None = None,
    label: AssetLabel,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload a group of files to a directory."""
    for concrete_path in paths.values():
        if not concrete_path.exists():
            msg = f"Path {concrete_path} does not exist"
            raise EntitySDKError(msg)

    response = make_db_api_request(
        url=url,
        method="POST",
        project_context=project_context,
        token=token,
        http_client=http_client,
        json={
            "files": [str(p) for p in paths],
            "meta": metadata,
            "label": label,
            "directory_name": name,
        },
    )

    js = response.json()

    def upload(to_upload):
        upload_client = http_client or httpx.Client()
        failed = {}
        for path, url in to_upload.items():
            with open(paths[Path(path)], "rb") as fd:
                try:
                    response = upload_client.request(
                        method="PUT",
                        url=url,
                        content=fd,
                        follow_redirects=True,
                        timeout=httpx.Timeout(
                            connect=settings.connect_timeout,
                            read=settings.read_timeout,
                            write=settings.write_timeout,
                            pool=settings.pool_timeout,
                        ),
                    )
                except httpx.HTTPError:
                    L.exception("Upload failed, will retry again")
                    failed[path] = url
                else:
                    if response.status_code != 200:
                        failed[path] = url
        return failed

    to_upload = js["files"]
    for _ in range(3):
        to_upload = upload(to_upload)
        if not to_upload:
            break

    if to_upload:
        raise EntitySDKError(f"Uploading these files failed: {to_upload}")

    return serdes.deserialize_model(js["asset"], Asset)


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
    return serdes.deserialize_model(response.json(), DetailedFileList)


def download_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Identifiable],
    asset_or_id: ID | Asset,
    output_path: Path,
    asset_path: os.PathLike | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
    local_store: LocalAssetStore | None = None,
) -> Path:
    """Download asset file to a file path.

    Args:
        api_url: The API URL to entitycore service.
        entity_id: Resource id
        entity_type: Resource type
        asset_or_id: Asset id or asset instance
        output_path: Path to save the file to.
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.
        local_store: LocalAssetStore for using a local store.

    Returns:
        Output file path.
    """
    asset_endpoint = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_or_id if isinstance(asset_or_id, ID) else asset_or_id.id,
    )

    if isinstance(asset_or_id, ID):
        asset = get_entity(
            asset_endpoint,
            entity_type=Asset,
            project_context=project_context,
            http_client=http_client,
            token=token,
        )
    else:
        asset = asset_or_id

    target_path: Path = Path(output_path)
    source_path: Path = Path(asset.full_path)
    if asset.is_directory:
        if not asset_path:
            raise EntitySDKError("Directory from directories require an `asset_path`")
        source_path /= asset_path
    else:
        if asset_path:
            raise EntitySDKError("Cannot pass `asset_path` to non-directories")

        target_path = (
            target_path / asset.path
            if target_path.is_dir()
            else validate_filename_extension_consistency(target_path, Path(asset.path).suffix)
        )

    create_intermediate_directories(target_path)

    if local_store and local_store.path_exists(source_path):
        local_store.link_path(source_path, target_path)
        return target_path

    bytes_content = download_asset_content(
        api_url=api_url,
        asset_id=asset.id,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_path=asset_path,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    target_path.write_bytes(bytes_content)
    return target_path


def download_asset_content(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Identifiable],
    asset_id: ID,
    asset_path: os.PathLike | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
    local_store: LocalAssetStore | None = None,
) -> bytes:
    """Download asset content.

    Args:
        api_url: The API URL to entitycore service.
        entity_id: Resource id
        entity_type: Resource type
        asset_id: Asset id
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.
        local_store: LocalAssetStore for using a local store.

    Returns:
        Asset content in bytes.
    """
    asset_endpoint = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )

    if local_store:
        asset = get_entity(
            asset_endpoint,
            entity_type=Asset,
            project_context=project_context,
            http_client=http_client,
            token=token,
        )
        if local_store.path_exists(asset.full_path):
            path = asset.full_path
            if asset.is_directory:
                path = f"{path}/{asset_path}"
            return local_store.read_bytes(path)

    download_endpoint = f"{asset_endpoint}/download"

    response = make_db_api_request(
        url=download_endpoint,
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
    project_context: ProjectContext | None,
    token: str,
    http_client: httpx.Client | None = None,
    hard: bool = False,
) -> Asset:
    """Delete asset."""
    response = make_db_api_request(
        url=url,
        method="DELETE",
        project_context=project_context,
        token=token,
        http_client=http_client,
        parameters={"hard": True} if hard else None,
    )
    return serdes.deserialize_model(response.json(), Asset)


def register_asset(
    url: str,
    *,
    asset_metadata: ExistingAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Register a file or directory already existing."""
    response = make_db_api_request(
        url=url,
        method="POST",
        json=asset_metadata.model_dump(),
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)
