"""Multipart upload functionality for large assets."""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.entity import Entity
from entitysdk.route import (
    multipart_upload_complete_endpoint,
    multipart_upload_initiate_endpoint,
)
from entitysdk.schemas.asset import MultipartUploadTransferConfig, PartUpload
from entitysdk.token_manager import TokenManager
from entitysdk.types import ID
from entitysdk.util import make_db_api_request
from entitysdk.utils.execution import execute_with_retry
from entitysdk.utils.filesystem import get_filesize
from entitysdk.utils.io import calculate_sha256_digest, load_bytes_chunk

L = logging.getLogger(__name__)


MAX_RETRIES = 3
BACKOFF_BASE = 0.25
TIMEOUT = httpx.Timeout(connect=5.0, read=120.0, write=120.0, pool=10.0)
DEFAULT_THREAD_COUNT = 10
RETRIABLE_EXCEPTIONS = (
    httpx.ConnectError,  # network down, DNS failure, etc.
    httpx.ReadTimeout,  # server took too long to respond
    httpx.WriteTimeout,  # slow upload
    httpx.RemoteProtocolError,  # low-level network glitch
)


def multipart_upload_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token_manager: TokenManager,
    http_client: httpx.Client | None = None,
    transfer_config: MultipartUploadTransferConfig,
) -> Asset:
    """Upload a local asset file in multiple parts to the storage service using presigned URLs.

    The function requests presigned URLs from the backend, then uploads the file parts
    either sequentially or concurrently using threads according to the transfer configuration.
    Once all parts are uploaded, it finalizes the asset in the backend.

    Args:
        api_url: Base URL of the backend API to request presigned URLs.
        entity_id: ID of the entity the asset belongs to.
        entity_type: Type of the entity.
        asset_path: Path to the local asset file to upload.
        asset_metadata: Metadata associated with the asset.
        project_context: Context of the project.
        token_manager: Object providing authentication tokens for API requests.
        http_client (httpx.Client | None): Optional HTTP client to use for uploads.
        transfer_config (MultipartUploadTransferConfig): Configuration for multipart upload.

    Returns:
        Asset: The asset object as returned by the backend after completion.
    """
    if http_client is None:
        http_client = httpx.Client()

    asset_id, parts = _initiate_upload(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_path=asset_path,
        asset_metadata=asset_metadata,
        project_context=project_context,
        token=token_manager.get_token(),
        http_client=http_client,
        preferred_part_count=transfer_config.preferred_part_count,
    )
    _upload_parts(
        parts=parts,
        file_path=asset_path,
        http_client=http_client,
        transfer_config=transfer_config,
    )
    return _complete_upload(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_id,
        project_context=project_context,
        token=token_manager.get_token(),
        http_client=http_client,
    )


def _initiate_upload(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    preferred_part_count: int,
    token: str,
    http_client: httpx.Client | None,
) -> tuple[ID, list[PartUpload]]:
    """Initiate a multipart upload with the backend and prepare part metadata.

    Sends a request to obtain presigned upload URLs and part configuration
    for the given file. Computes the file size and SHA-256 digest locally
    and includes them in the initiation request.

    Returns:
        tuple[ID, list[PartUpload]]:
            - The created asset ID.
            - A list of PartUpload objects describing each part’s
              number, byte offset, size, and presigned URL.

    Raises:
        Exception: Propagates any exception raised during the API request
        or local file inspection.
    """
    url = multipart_upload_initiate_endpoint(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    filesize = get_filesize(asset_path)
    data = make_db_api_request(
        url=url,
        method="POST",
        json={
            "filename": asset_metadata.file_name,
            "filesize": filesize,
            "sha256_digest": calculate_sha256_digest(asset_path),
            "content_type": asset_metadata.content_type,
            "label": asset_metadata.label,
            "preferred_part_count": preferred_part_count,
        },
        project_context=project_context,
        token=token,
        http_client=http_client,
    ).json()

    upload_meta = data["upload_meta"]
    part_size = upload_meta["part_size"]

    parts = [
        PartUpload(
            part_number=part["part_number"],
            offset=(part["part_number"] - 1) * part_size,
            size=min(part_size, filesize - (part["part_number"] - 1) * part_size),
            url=part["url"],
        )
        for part in upload_meta["parts"]
    ]

    return ID(data["id"]), parts


def _upload_parts(
    parts: list[PartUpload],
    file_path: Path,
    http_client: httpx.Client,
    transfer_config: MultipartUploadTransferConfig,
) -> None:
    """Upload file parts either sequentially or concurrently.

    Blocks until all parts have been uploaded. Exceptions from individual
    part uploads propagate to the caller.
    """
    if transfer_config.use_threads:
        L.info("Parts are concurrently uploaded using threads.")
        _upload_parts_threaded(
            parts=parts,
            file_path=file_path,
            http_client=http_client,
            max_concurrency=transfer_config.max_concurrency,
        )
    else:
        L.info("Parts are sequentially uploaded.")
        _upload_parts_sequential(
            parts=parts,
            file_path=file_path,
            http_client=http_client,
        )


def _upload_parts_sequential(
    *,
    file_path: Path,
    parts: list[PartUpload],
    http_client: httpx.Client,
) -> None:
    """Upload multiple file parts sequentially.

    Each part is uploaded one after another by calling `_upload_part`.
    The function blocks until all parts have been uploaded.

    Args:
        file_path: Path to the source file being uploaded.
        parts: A list of PartUpload objects describing the parts to upload.
        http_client: An initialized httpx.Client used to perform HTTP requests.

    Raises:
        Exception: Propagates any exception raised by `_upload_part`.
    """
    for part in parts:
        _upload_part(file_path=file_path, part=part, http_client=http_client)


def _upload_parts_threaded(
    *,
    file_path: Path,
    parts: list[PartUpload],
    http_client: httpx.Client,
    max_concurrency: int,
) -> None:
    """Upload multiple file parts concurrently using a thread pool.

    Each part is uploaded by submitting `_upload_part` tasks to a
    ThreadPoolExecutor with the specified maximum concurrency. The
    function blocks until all parts have completed uploading.

    Args:
        file_path: Path to the source file being uploaded.
        parts: A list of PartUpload objects describing the parts to upload.
        http_client: An initialized httpx.Client used to perform HTTP requests.
        max_concurrency: Maximum number of concurrent upload threads.

    Raises:
        Exception: Propagates any exception raised by `_upload_part`.
    """

    def _task(part: PartUpload) -> None:
        _upload_part(file_path, part, http_client)

    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        list(pool.map(_task, parts))


def _upload_part(file_path: Path, part: PartUpload, http_client: httpx.Client) -> None:
    """Upload a single file part to its presigned URL.

    Reads the corresponding byte range from the file and sends it using
    the provided HTTP client. Retries transient failures according to the
    configured retry policy. Raises an exception if all retry attempts fail.
    """
    data = load_bytes_chunk(file_path, part.offset, part.size)
    execute_with_retry(
        lambda: _send_part(data=data, url=part.url, http_client=http_client),
        max_retries=MAX_RETRIES,
        backoff_base=BACKOFF_BASE,
        retry_on=RETRIABLE_EXCEPTIONS,
    )
    L.debug("Uploaded part %d (offset=%d, size=%d)", part.part_number, part.offset, part.size)


def _send_part(data: bytes, url: str, http_client: httpx.Client) -> None:
    """Upload a single part to the presigned URL.

    Raises:
        httpx.HTTPStatusError: If the PUT request fails.
        httpx.RequestError: For network-related errors.
    """
    response = http_client.put(url, content=data, timeout=TIMEOUT, headers={})
    response.raise_for_status()


def _complete_upload(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_id: ID,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None,
) -> Asset:
    """Finalize a multipart upload with the backend and return the created asset.

    Sends a completion request to the API for the given asset ID after all
    parts have been successfully uploaded. The backend assembles the parts
    and returns the resulting Asset representation.

    Raises:
        Exception: Propagates any exception raised during the API request.

    Returns:
        Asset: The finalized asset as returned by the backend.
    """
    url = multipart_upload_complete_endpoint(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_id,
    )
    data = make_db_api_request(
        url=url,
        method="POST",
        token=token,
        http_client=http_client,
        project_context=project_context,
    ).json()
    return serdes.deserialize_model(data, Asset)
