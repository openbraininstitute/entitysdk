"""Asset related schemas."""

from pathlib import Path
from typing import Annotated

from pydantic import Field

from entitysdk.models.asset import Asset
from entitysdk.schemas.base import Schema


class DownloadedAssetFile(Schema):
    """Downloaded asset file."""

    asset: Asset
    path: Path


class DownloadedAssetContent(Schema):
    """Downloaded asset content."""

    asset: Asset
    content: bytes


class MultipartUploadTransferConfig(Schema):
    """Configuration for multipart uploads."""

    threshold: Annotated[
        int, Field(description="Minimum size (in bytes) for multipart upload.")
    ] = 20 * 1024**2
    max_concurrency: Annotated[
        int, Field(description="Maximum number of threads for uploading parts.")
    ] = 10
    preferred_part_count: Annotated[
        int, Field(description="Preferred number of parts for the upload.")
    ] = 100


class PartUpload(Schema):
    """Multipart upload part."""

    part_number: int
    offset: int
    size: int
    url: str
