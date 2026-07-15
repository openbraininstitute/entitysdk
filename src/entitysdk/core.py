"""Core SDK operations."""

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import (
    Asset,
    DetailedFileList,
    ExistingAssetMetadata,
    LocalAssetMetadata,
)
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.multipart_upload import (
    calculate_part_count,
    multipart_upload_asset_directory,
    multipart_upload_asset_file,
)
from entitysdk.result import IteratorResult
from entitysdk.route import (
    get_assets_endpoint,
    get_entities_endpoint,
    get_entity_derivations_endpoint,
    get_version_endpoint,
)
from entitysdk.schemas.asset import (
    MultipartDirectoryFileRequest,
    MultipartDirectoryUploadRequest,
    MultipartDirectoryUploadTransferConfig,
    MultipartUploadTransferConfig,
)
from entitysdk.schemas.version import APIVersion
from entitysdk.token_manager import TokenManager
from entitysdk.types import (
    ID,
    AssetLabel,
    BytesOrStream,
    DerivationType,
    FetchContentStrategy,
    FetchFileStrategy,
)
from entitysdk.utils.asset import resolve_asset_path
from entitysdk.utils.filesystem import (
    create_dir,
    get_filesize,
    validate_filename_extension_consistency,
)
from entitysdk.utils.http import make_db_api_request, stream_paginated_request, stream_response
from entitysdk.utils.io import calculate_sha256_digest
from entitysdk.utils.store import LocalAssetStore

L = logging.getLogger(__name__)

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)


def get_api_version(
    *,
    api_url: str,
    token_manager: TokenManager,
    http_client: httpx.Client,
) -> APIVersion:
    """Return the entitycore version."""
    url = get_version_endpoint(api_url=api_url)
    response = make_db_api_request(
        url=url,
        method="GET",
        token_manager=token_manager,
        http_client=http_client,
    )
    return APIVersion.model_validate(response.json())


def search_entities(
    *,
    api_url: str,
    entity_type: type[TIdentifiable],
    query: dict | None = None,
    limit: int | None,
    project_context: ProjectContext | None = None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> IteratorResult[TIdentifiable]:
    """Search for entities.

    Args:
        api_url: the api url to entitycore service.
        entity_type: Type of the entity.
        query: Query parameters
        limit: Limit of the number of entities to yield or None.
        project_context: Project context.
        token_manager: Token manager to issue tokens.
        http_client: HTTP client.
        admin: Use admin endpoint if True

    Returns:
        List of entities.
    """
    url = get_entities_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        admin=admin,
    )
    iterator: Iterator[dict] = stream_paginated_request(
        url=url,
        method="GET",
        parameters=query,
        limit=limit,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return IteratorResult(
        serdes.deserialize_model(json_data, entity_type) for json_data in iterator
    )


def get_entity(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[TIdentifiable],
    project_context: ProjectContext | None = None,
    token_manager: TokenManager,
    options: dict | None = None,
    http_client: httpx.Client,
    admin: bool,
) -> TIdentifiable:
    """Instantiate entity with model ``entity_type`` from resource id."""
    url = get_entities_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        admin=admin,
    )
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        parameters=options,
        project_context=project_context,
        token_manager=token_manager,
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
    token_manager: TokenManager,
    http_client: httpx.Client,
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
        token_manager=token_manager,
        http_client=http_client,
        parameters=params,
    )
    return IteratorResult(
        serdes.deserialize_model(json_data, Entity) for json_data in response.json()["data"]
    )


def get_entity_asset(
    *,
    api_url: str,
    entity_id: ID,
    asset_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool = False,
) -> Asset:
    """Get an entity's asset metadata."""
    url = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
        admin=admin,
    )
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)


def get_entity_assets(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
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
        token_manager=token_manager,
        http_client=http_client,
    )
    return IteratorResult(
        serdes.deserialize_model(json_data, Asset) for json_data in response.json()["data"]
    )


def register_entity(
    *,
    api_url: str,
    entity: TIdentifiable,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
) -> TIdentifiable:
    """Register entity."""
    url = get_entities_endpoint(api_url=api_url, entity_type=type(entity))

    json_data = serdes.serialize_model(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), type(entity))


def update_entity(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[TIdentifiable],
    attrs_or_entity: dict | Identifiable,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> TIdentifiable:
    """Update entity."""
    if isinstance(attrs_or_entity, dict):
        json_data = serdes.serialize_dict(attrs_or_entity)
    else:
        json_data = serdes.serialize_model(attrs_or_entity)

    url = get_entities_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        admin=admin,
    )

    response = make_db_api_request(
        url=url,
        method="PATCH",
        json=json_data,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )

    json_data = response.json()

    return serdes.deserialize_model(json_data, entity_type)


def delete_entity(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Identifiable],
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> None:
    """Delete entity."""
    url = get_entities_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        admin=admin,
    )
    make_db_api_request(
        url=url,
        method="DELETE",
        token_manager=token_manager,
        http_client=http_client,
    )


def upload_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    transfer_config: MultipartUploadTransferConfig | None = None,
    admin: bool,
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
    with open(asset_path, "rb") as file_content:
        return upload_asset_content(
            api_url=api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token_manager=token_manager,
            http_client=http_client,
            admin=admin,
        )


def upload_asset_content(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_content: BytesOrStream,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file-like object."""
    files = {
        "file": (
            asset_metadata.file_name,
            asset_content,
            asset_metadata.content_type,
        )
    }
    url = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=None,
        admin=admin,
    )
    response = make_db_api_request(
        url=url,
        method="POST",
        files=files,
        data={"label": asset_metadata.label} if asset_metadata.label else None,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)


def upload_asset_directory(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    name: str,
    paths: dict[Path, Path],
    metadata: dict | None = None,
    label: AssetLabel,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    transfer_config: MultipartDirectoryUploadTransferConfig | None = None,
) -> Asset:
    """Upload a group of files to a directory using multipart-upload."""
    transfer_config = transfer_config or MultipartDirectoryUploadTransferConfig()

    files = []
    for relative_path, local_path in paths.items():
        filesize = get_filesize(local_path)
        files.append(
            MultipartDirectoryFileRequest(
                filename=str(relative_path),
                filesize=filesize,
                sha256_digest=calculate_sha256_digest(local_path),
                preferred_part_count=calculate_part_count(filesize),
            )
        )

    upload_request = MultipartDirectoryUploadRequest(
        directory_name=name,
        label=label,
        meta=metadata,
        files=files,
    )

    return multipart_upload_asset_directory(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        project_context=project_context,
        http_client=http_client,
        token_manager=token_manager,
        transfer_config=transfer_config,
        upload_request=upload_request,
        paths=paths,
    )


def list_directory(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_id: ID,
    token_manager: TokenManager,
    project_context: ProjectContext | None = None,
    http_client: httpx.Client,
) -> DetailedFileList:
    """List all files within an asset directory."""
    url = (
        get_assets_endpoint(
            api_url=api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
        + "/list"
    )
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), DetailedFileList)


def fetch_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_or_id: ID | Asset,
    output_path: Path,
    asset_path: Path | None = None,
    project_context: ProjectContext | None = None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    local_store: LocalAssetStore | None = None,
    strategy: FetchFileStrategy,
    admin: bool,
) -> Path:
    """Fetch asset file."""
    if isinstance(asset_or_id, ID):
        asset = get_entity_asset(
            api_url=api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_or_id,
            project_context=project_context,
            http_client=http_client,
            token_manager=token_manager,
            admin=admin,
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
            api_url=api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset.id,
            target_path=target_path,
            token_manager=token_manager,
            project_context=project_context,
            http_client=http_client,
            asset_path=asset_path,
            admin=admin,
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
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_id: ID,
    target_path: Path,
    token_manager: TokenManager,
    project_context: ProjectContext | None = None,
    http_client: httpx.Client,
    asset_path: Path | None = None,
    admin: bool,
) -> Path:
    """Download an asset from the entitycore download endpoint to a local file.

    Streams the HTTP response body to ``target_path`` without loading the full
    payload into memory.

    Args:
        api_url: the api url to entitycore service.
        entity_id: Resource id
        entity_type: Resource type
        asset_id: Asset id
        target_path: Local path to write the downloaded bytes.
        token_manager: Authorization access token manager.
        project_context: Optional project context for ``project-id`` / ``virtual-lab-id`` headers.
        http_client: HTTP client used for the streaming request.
        asset_path: For directory assets, path within the directory to the file.
        admin: Whether to use admin endpoints.

    Returns:
        ``target_path`` after the download completes.
    """
    asset_endpoint = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
        admin=admin,
    )
    token = token_manager.get_token()
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
    entity_type: type[Entity],
    asset_or_id: ID | Asset,
    asset_path: Path | None = None,
    project_context: ProjectContext | None = None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    local_store: LocalAssetStore | None = None,
    strategy: FetchContentStrategy,
    admin: bool,
) -> bytes:
    """Fetch asset content.

    Args:
        api_url: the api url to entitycore service.
        entity_id: Resource id
        entity_type: Resource type
        asset_or_id: Asset id
        asset_path: for asset directories, the path within the directory to the file
        project_context: Project context.
        token_manager: Authorization access token manager.
        http_client: HTTP client.
        local_store: LocalAssetStore for using a local store.
        strategy: Output strategy to fetch the asset content.
        admin: Whether to use admin endpoints.

    Returns:
        Asset content in bytes.
    """
    asset_id = asset_or_id.id if isinstance(asset_or_id, Asset) else asset_or_id

    def try_read_from_store() -> bytes | None:

        if local_store is None:
            return None

        if isinstance(asset_or_id, ID):
            asset = get_entity_asset(
                api_url=api_url,
                entity_id=entity_id,
                entity_type=entity_type,
                asset_id=asset_id,
                project_context=project_context,
                http_client=http_client,
                token_manager=token_manager,
                admin=admin,
            )
        else:
            asset = asset_or_id

        source_path: Path = resolve_asset_path(asset, directory_file=asset_path)

        if local_store.path_exists(source_path):
            return local_store.read_bytes(source_path)

        return None

    def download_content():
        asset_endpoint = get_assets_endpoint(
            api_url=api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            admin=admin,
        )
        return make_db_api_request(
            url=f"{asset_endpoint}/download",
            method="GET",
            parameters={"asset_path": str(asset_path)} if asset_path else {},
            project_context=project_context,
            token_manager=token_manager,
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
    *,
    api_url: str,
    entity_id: ID,
    asset_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> Asset:
    """Delete asset."""
    url = get_assets_endpoint(
        api_url=api_url,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
        admin=admin,
    )
    response = make_db_api_request(
        url=url,
        method="DELETE",
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)


def register_asset(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_metadata: ExistingAssetMetadata,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    admin: bool,
) -> Asset:
    """Register a file or directory already existing."""
    url = (
        get_assets_endpoint(
            api_url=api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=None,
            admin=admin,
        )
        + "/register"
    )
    response = make_db_api_request(
        url=url,
        method="POST",
        json=asset_metadata.model_dump(),
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )
    return serdes.deserialize_model(response.json(), Asset)
