"""Multipart upload functionality for large assets."""

import logging
from pathlib import Path
from time import sleep

import httpx

from entitysdk import serdes
from entitysdk.common import ProjectContext
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.entity import Entity
from entitysdk.route import (
    multipart_upload_complete_endpoint,
    multipart_upload_initiate_endpoint,
)
from entitysdk.types import ID
from entitysdk.util import make_db_api_request
from entitysdk.utils.io import calculate_sha256_digest

L = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 0.25
TIMEOUT = (5, 60)


def multipart_upload_asset_file(
    *,
    api_url: str,
    entity_id: ID,
    entity_type: type[Entity],
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload file using multipart delegation to s3."""
    url_initiate = multipart_upload_initiate_endpoint(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
    )

    filesize = asset_path.stat().st_size

    initiate_response = make_db_api_request(
        url=url_initiate,
        method="POST",
        json={
            "filename": asset_metadata.file_name,
            "filesize": filesize,
            "sha256_digest": calculate_sha256_digest(asset_path),
            "content_type": asset_metadata.content_type,
            "label": asset_metadata.label,
        },
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    asset_data = initiate_response.json()
    upload_meta = asset_data["upload_meta"]

    part_size = upload_meta["part_size"]

    for part in upload_meta["parts"]:
        part_number = part["part_number"]
        offset = (part_number - 1) * part_size
        size = min(part_size, filesize - offset)
        _upload_part(
            file_path=asset_path,
            offset=offset,
            size=size,
            presigned_url=part["url"],
            part_number=part_number,
            http_client=http_client,
        )

    url_complete = multipart_upload_complete_endpoint(
        api_url=api_url,
        entity_id=entity_id,
        entity_type=entity_type,
        asset_id=asset_data["id"],
    )

    complete_response = make_db_api_request(
        url=url_complete,
        method="POST",
        token=token,
        http_client=http_client,
        project_context=project_context,
    )

    return serdes.deserialize_model(complete_response.json(), Asset)


def _upload_part(
    file_path: Path,
    offset: int,
    size: int,
    presigned_url: str,
    part_number: int,
    http_client: httpx.Client | None,
) -> None:
    """Upload a single part of a multipart upload with retry logic."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(file_path, "rb") as f:
                f.seek(offset)
                data = f.read(size)

            http_client.put(
                presigned_url,
                data=data,
                timeout=TIMEOUT,
                headers={},
            ).raise_for_status()

            return  # success

        except Exception as exc:
            if attempt >= MAX_RETRIES:
                raise RuntimeError(
                    f"Part {part_number} failed after {MAX_RETRIES} attempts"
                ) from exc

            sleep_time = BACKOFF_BASE * (2 ** (attempt - 1))
            sleep(sleep_time)
