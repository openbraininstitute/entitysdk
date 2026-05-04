"""Core SDK operations."""

import io
import logging
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
from entitysdk.multipart_upload import multipart_upload_asset_file
from entitysdk.result import IteratorResult
from entitysdk.route import (
    get_assets_endpoint,
    get_entity_derivations_endpoint,
)
from entitysdk.schemas.asset import MultipartUploadTransferConfig
from entitysdk.token_manager import TokenManager
from entitysdk.types import ID, AssetLabel, DerivationType, FetchContentStrategy, FetchFileStrategy
from entitysdk.utils.asset import resolve_asset_path
from entitysdk.utils.filesystem import (
    create_dir,
    get_filesize,
    validate_filename_extension_consistency,
)
from entitysdk.utils.http import make_db_api_request, stream_paginated_request, stream_response
from entitysdk.utils.store import LocalAssetStore

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
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token_manager: TokenManager,
    http_client: httpx.Client | None = None,
    transfer_config: MultipartUploadTransferConfig | None = None,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file path."""
    if transfer_config and get_filesize(asset_path) > transfer_config.threshold:
        L.info("File is being uploaded using multipart upload")
        return multipart_upload_asset_file(
            api_url=api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_path=asset_path,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token_manager=token_manager,
            transfer_config=transfer_config,
            http_client=http_client,
        )

    url = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=None,
    )

    with open(asset_path, "rb") as file_content:
        return upload_asset_content(
            url=url,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token=token_manager.get_token(),
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
    token: str,
    project_context: ProjectContext | None = None,
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


def fetch_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Identifiable],
    asset_or_id: ID | Asset,
    output_path: Path,
    asset_path: Path | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
    local_store: LocalAssetStore | None = None,
    strategy: FetchFileStrategy,
) -> Path:
    """Fetch asset file."""
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

    source_path = resolve_asset_path(asset, directory_file=asset_path)
    target_path = Path(output_path)

    if not asset.is_directory:
        target_path = (
            target_path / asset.path
            if target_path.is_dir()
            else validate_filename_extension_consistency(target_path, Path(asset.path).suffix)
        )

    create_dir(target_path.parent)

    def download_file():
        return download_asset_file(
            asset_endpoint=asset_endpoint,
            target_path=target_path,
            token=token,
            project_context=project_context,
            http_client=http_client,
            asset_path=asset_path,
        )

    def try_copy_path() -> Path | None:
        if local_store is None:
            return None

        if local_store.path_exists(source_path):
            return local_store.copy_path(path=source_path, target_path=target_path)

        return None

    def try_link_path() -> Path | None:
        if local_store is None:
            return None

        if local_store.path_exists(source_path):
            return local_store.link_path(path=source_path, target_path=target_path)

        return None

    match strategy:
        case FetchFileStrategy.copy_only:
            if path := try_copy_path():
                return path
            raise EntitySDKError("copy strategy failed: Asset path not found in store")
        case FetchFileStrategy.copy_or_download:
            if path := try_copy_path():
                return path
            return download_file()
        case FetchFileStrategy.link_only:
            if path := try_link_path():
                return path
            raise EntitySDKError("link strategy failed: Asset path not found in store")
        case FetchFileStrategy.link_or_download:
            if path := try_link_path():
                return path
            return download_file()
        case FetchFileStrategy.download_only:
            return download_file()
        case _:
            raise EntitySDKError(f"{strategy} strategy failed: Unsupported strategy")


def download_asset_file(
    *,
    asset_endpoint: str,
    target_path: Path,
    token: str,
    project_context: ProjectContext | None = None,
    http_client: httpx.Client,
    asset_path: Path | None = None,
) -> Path:
    """Download an asset from the entitycore download endpoint to a local file.

    Streams the HTTP response body to ``target_path`` without loading the full
    payload into memory.

    Args:
        asset_endpoint: Base URL of the asset resource (``.../download`` is appended).
        target_path: Local path to write the downloaded bytes.
        token: Authorization access token.
        project_context: Optional project context for ``project-id`` / ``virtual-lab-id`` headers.
        http_client: HTTP client used for the streaming request.
        asset_path: For directory assets, path within the directory to the file.

    Returns:
        ``target_path`` after the download completes.
    """
    headers = {"Authorization": f"Bearer {token}"}
    if project_context:
        headers["project-id"] = str(project_context.project_id)
        if vlab_id := project_context.virtual_lab_id:
            headers["virtual-lab-id"] = str(vlab_id)

    parameters = {"asset_path": str(asset_path)} if asset_path else {}
    with target_path.open("wb") as f:
        for chunk in stream_response(
            url=f"{asset_endpoint}/download",
            method="GET",
            headers=headers,
            parameters=parameters,
            http_client=http_client,
        ):
            if chunk:
                f.write(chunk)
    return target_path


def fetch_asset_content(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Identifiable],
    asset_or_id: ID | Asset,
    asset_path: Path | None = None,
    project_context: ProjectContext | None = None,
    token: str,
    http_client: httpx.Client | None = None,
    local_store: LocalAssetStore | None = None,
    strategy: FetchContentStrategy,
) -> bytes:
    """Fetch asset content.

    Args:
        api_url: The API URL to entitycore service.
        entity_id: Resource id
        entity_type: Resource type
        asset_or_id: Asset id
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.
        local_store: LocalAssetStore for using a local store.
        strategy: Output strategy to fetch the asset content.

    Returns:
        Asset content in bytes.
    """
    asset_id = asset_or_id.id if isinstance(asset_or_id, Asset) else asset_or_id

    asset_endpoint = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
    )

    def try_read_from_store() -> bytes | None:

        if local_store is None:
            return None

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

        source_path: Path = resolve_asset_path(asset, directory_file=asset_path)

        if local_store.path_exists(source_path):
            return local_store.read_bytes(source_path)

        return None

    def download_content():
        return make_db_api_request(
            url=f"{asset_endpoint}/download",
            method="GET",
            parameters={"asset_path": str(asset_path)} if asset_path else {},
            project_context=project_context,
            token=token,
            http_client=http_client,
        ).content

    match strategy:
        case FetchContentStrategy.local_only:
            if content := try_read_from_store():
                return content
            raise EntitySDKError("copy strategy failed: No asset path found in store.")
        case FetchContentStrategy.local_or_download:
            if content := try_read_from_store():
                return content
            return download_content()
        case FetchContentStrategy.download_only:
            return download_content()
        case _:
            raise EntitySDKError(f"{strategy} failed: Unsupported strategy")


def delete_asset(
    url: str,
    *,
    project_context: ProjectContext | None,
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
