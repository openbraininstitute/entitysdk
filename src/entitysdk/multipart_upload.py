"""Multipart upload functionality for large assets."""

import logging
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import Asset, AssetWithUploadMeta, LocalAssetMetadata
from entitysdk.models.entity import Entity
from entitysdk.route import (
    multipart_upload_complete_endpoint,
    multipart_upload_complete_endpoint_directory,
    multipart_upload_initiate_endpoint,
    multipart_upload_initiate_endpoint_directory,
)
from entitysdk.schemas.asset import (
    MultipartDirectoryUploadRequest,
    MultipartDirectoryUploadResponse,
    MultipartDirectoryUploadTransferConfig,
    MultipartUploadTransferConfig,
    PartUpload,
)
from entitysdk.token_manager import TokenManager
from entitysdk.types import ID
from entitysdk.utils.execution import execute_with_retry
from entitysdk.utils.filesystem import get_filesize
from entitysdk.utils.http import make_db_api_request
from entitysdk.utils.io import calculate_sha256_digest, iter_bytes_chunk

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
STREAM_DATA_BUFFER_SIZE = 256 * 1024

S3_DEFAULT_PART_SIZE = 64 * 1024 * 1024  # 64 MiB
S3_MAX_PART_SIZE = 5 * 1024 * 1024 * 1024  # 5 GiB
S3_MAX_PARTS = 10_000


def calculate_part_size(filesize: int) -> int:
    """Calculate an appropriate S3 multipart upload part size.

    The returned size:
    - uses a default minimum of 64 MiB for efficient uploads
    - ensures the total number of parts does not exceed S3's 10,000-part limit
    - never exceeds S3's 5 GiB maximum part size

    Args:
        filesize: Total file size in bytes.

    Returns:
        Recommended multipart upload part size in bytes.

    Raises:
        ValueError: If file_size is not positive.
    """
    if filesize < 0:
        msg = "file_size must be >= 0"
        raise ValueError(msg)

    minimum_required_size = math.ceil(filesize / S3_MAX_PARTS)
    part_size = max(S3_DEFAULT_PART_SIZE, minimum_required_size)
    return min(part_size, S3_MAX_PART_SIZE)


def calculate_part_count(filesize: int) -> int:
    """Calculate the number of parts needed for a multipart upload.

    Args:
        filesize: Total file size in bytes.

    Returns:
        Number of parts needed for the upload.
    """
    if filesize == 0:
        return 1
    return math.ceil(filesize / calculate_part_size(filesize))


def multipart_upload_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
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
        http_client: HTTP client to use for uploads.
        transfer_config: Configuration for multipart upload.

    Returns:
        Asset: The file asset object as returned by the backend after completion.
    """
    asset_id, parts = _initiate_upload(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_path=asset_path,
        asset_metadata=asset_metadata,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
        preferred_part_count=transfer_config.preferred_part_count,
    )
    _upload_parts(
        parts=parts,
        http_client=http_client,
        transfer_config=transfer_config,
    )
    return _complete_upload(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_id,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )


def _initiate_upload(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext | None,
    preferred_part_count: int,
    token_manager: TokenManager,
    http_client: httpx.Client,
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
        token_manager=token_manager,
        http_client=http_client,
    ).json()

    asset = AssetWithUploadMeta.model_validate(data)
    part_size = asset.upload_meta.part_size

    parts = [
        PartUpload(
            file_path=asset_path,
            part_number=part.part_number,
            offset=(part.part_number - 1) * part_size,
            size=min(part_size, filesize - (part.part_number - 1) * part_size),
            url=part.url,
        )
        for part in asset.upload_meta.parts
    ]

    return asset.id, parts


def _upload_parts(
    parts: list[PartUpload],
    http_client: httpx.Client,
    transfer_config: MultipartUploadTransferConfig | MultipartDirectoryUploadTransferConfig,
) -> None:
    """Upload file parts either sequentially or concurrently.

    Blocks until all parts have been uploaded. Exceptions from individual
    part uploads propagate to the caller.
    """
    if transfer_config.max_concurrency > 1:
        L.info("Parts are concurrently uploaded using threads.")
        _upload_parts_threaded(
            parts=parts,
            http_client=http_client,
            max_concurrency=transfer_config.max_concurrency,
        )
    else:
        L.info("Parts are sequentially uploaded.")
        _upload_parts_sequential(
            parts=parts,
            http_client=http_client,
        )


def _upload_parts_sequential(
    *,
    parts: list[PartUpload],
    http_client: httpx.Client,
) -> None:
    """Upload multiple file parts sequentially.

    Each part is uploaded one after another by calling `_upload_part`.
    The function blocks until all parts have been uploaded.

    Args:
        parts: A list of PartUpload objects describing the parts to upload.
        http_client: An initialized httpx.Client used to perform HTTP requests.

    Raises:
        Exception: Propagates any exception raised by `_upload_part`.
    """
    for part in parts:
        _upload_part_with_retry(part=part, http_client=http_client)


def _upload_parts_threaded(
    *,
    parts: list[PartUpload],
    http_client: httpx.Client,
    max_concurrency: int,
) -> None:
    """Upload multiple file parts concurrently using a thread pool.

    Each part is uploaded by submitting `_upload_part` tasks to a
    ThreadPoolExecutor with the specified maximum concurrency. The
    function blocks until all parts have completed uploading.

    Args:
        parts: A list of PartUpload objects describing the parts to upload.
        http_client: An initialized httpx.Client used to perform HTTP requests.
        max_concurrency: Maximum number of concurrent upload threads.

    Raises:
        Exception: Propagates any exception raised by `_upload_part`.
    """

    def _task(part: PartUpload) -> None:
        _upload_part_with_retry(part, http_client)

    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        list(pool.map(_task, parts))


def _upload_part_with_retry(part: PartUpload, http_client: httpx.Client) -> None:
    """Upload a single file part to its presigned URL.

    Reads the corresponding byte range from the file and sends it using
    the provided HTTP client. Retries transient failures according to the
    configured retry policy. Raises an exception if all retry attempts fail.
    """
    try:
        execute_with_retry(
            lambda: _upload_part(
                file_path=part.file_path,
                offset=part.offset,
                size=part.size,
                url=part.url,
                http_client=http_client,
            ),
            max_retries=MAX_RETRIES,
            backoff_base=BACKOFF_BASE,
            retry_on=RETRIABLE_EXCEPTIONS,
        )
    except httpx.RequestError as e:
        msg = (
            f"Failed to upload part {part.part_number} of file {part.file_path}\n"
            f"Request exception: {e!r}"
        )
        raise EntitySDKError(msg) from e
    except httpx.HTTPStatusError as e:
        message = (
            f"Failed to upload part {part.part_number} of file {part.file_path}\n"
            f"HTTP error {e.response.status_code} for {e.request.method} {e.request.url}\n"
            f"response: {e.response.text}"
        )
        raise EntitySDKError(message) from e

    L.debug("Uploaded part %d (offset=%d, size=%d)", part.part_number, part.offset, part.size)


def _upload_part(
    file_path: Path, offset: int, size: int, url: str, http_client: httpx.Client
) -> None:
    """Upload a single part to the presigned URL.

    Raises:
        httpx.HTTPStatusError: If the PUT request fails.
        httpx.RequestError: For network-related errors.
    """
    data_iterator = iter_bytes_chunk(
        path=file_path,
        offset=offset,
        size=size,
        buffer_size=STREAM_DATA_BUFFER_SIZE,
    )
    response = http_client.put(
        url=url, content=data_iterator, timeout=TIMEOUT, headers={"Content-Length": str(size)}
    )
    response.raise_for_status()


def _complete_upload(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_id: ID,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
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
        token_manager=token_manager,
        http_client=http_client,
        project_context=project_context,
    ).json()
    return serdes.deserialize_model(data, Asset)


def multipart_upload_asset_directory(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    transfer_config: MultipartDirectoryUploadTransferConfig,
    upload_request: MultipartDirectoryUploadRequest,
    paths: dict[Path, Path],
) -> Asset:
    """Upload files in a local directory in multiple parts using presigned URLs.

    This function is similar to `multipart_upload_asset_file`, but it can be used to upload files
    in a local directory as a single directory asset.

    It requests presigned URLs from the backend, then uploads the file parts
    either sequentially or concurrently using threads according to the transfer configuration.
    Once all parts are uploaded, it finalizes the asset in the backend.

    Args:
        api_url: Base URL of the backend API to request presigned URLs.
        entity_id: ID of the entity the asset belongs to.
        entity_type: Type of the entity.
        project_context: Context of the project.
        token_manager: Object providing authentication tokens for API requests.
        http_client: HTTP client to use for uploads.
        transfer_config: Configuration for multipart upload.
        upload_request: Request parameters for the upload.
        paths: Mapping of relative paths to local file paths.

    Returns:
        Asset: The directory asset object as returned by the backend after completion.
    """
    asset_id, parts = _initiate_directory_upload(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
        upload_request=upload_request,
        paths=paths,
    )
    _upload_parts(
        parts=parts,
        http_client=http_client,
        transfer_config=transfer_config,
    )
    return _complete_upload_directory(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_id,
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    )


def _initiate_directory_upload(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
    upload_request: MultipartDirectoryUploadRequest,
    paths: dict[Path, Path],
) -> tuple[ID, list[PartUpload]]:
    """Initiate a multipart directory upload with the backend and prepare part metadata.

    Similar to `_initiate_upload` but for directories.
    """
    url = multipart_upload_initiate_endpoint_directory(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
    )
    data = make_db_api_request(
        url=url,
        method="POST",
        json=upload_request.model_dump(mode="json"),
        project_context=project_context,
        token_manager=token_manager,
        http_client=http_client,
    ).json()

    upload_response = MultipartDirectoryUploadResponse.model_validate(data)
    if len(upload_response.files) != len(paths):
        msg = (
            f"Backend returned {len(upload_response.files)} files, but {len(paths)} were expected."
        )
        raise EntitySDKError(msg)

    directory_asset = upload_response.asset
    parts = []
    for asset in upload_response.files:
        part_size = asset.upload_meta.part_size
        # strip the directory name from the returned file path and retrieve the local path
        local_path = paths[Path(asset.path).relative_to(upload_request.directory_name)]
        parts += [
            PartUpload(
                file_path=local_path,
                part_number=part.part_number,
                offset=(part.part_number - 1) * part_size,
                size=min(part_size, asset.size - (part.part_number - 1) * part_size),
                url=part.url,
            )
            for part in asset.upload_meta.parts
        ]

    return directory_asset.id, parts


def _complete_upload_directory(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_id: ID,
    project_context: ProjectContext | None,
    token_manager: TokenManager,
    http_client: httpx.Client,
) -> Asset:
    """Finalize a multipart directory upload with the backend and return the created asset.

    Similar to `_complete_upload` but for directories.
    """
    url = multipart_upload_complete_endpoint_directory(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_id,
    )
    data = make_db_api_request(
        url=url,
        method="POST",
        token_manager=token_manager,
        http_client=http_client,
        project_context=project_context,
    ).json()
    return serdes.deserialize_model(data, Asset)
