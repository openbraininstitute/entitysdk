"""Asset related schemas."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, model_validator

from entitysdk.models.asset import Asset, AssetWithUploadMeta
from entitysdk.schemas.base import Schema
from entitysdk.types import AssetLabel, ContentType


class DownloadedAssetFile(Schema):
    """Downloaded asset file."""

    asset: Asset
    path: Path


class DownloadedAssetContent(Schema):
    """Downloaded asset content."""

    asset: Asset
    content: bytes


class MultipartUploadTransferConfig(Schema):
    """Configuration for multipart uploads (file)."""

    threshold: Annotated[
        int, Field(description="Minimum size (in bytes) for multipart upload.")
    ] = 20 * 1024**2
    max_concurrency: Annotated[
        int, Field(description="Maximum number of threads for uploading parts.")
    ] = 10
    preferred_part_count: Annotated[
        int, Field(description="Preferred number of parts for the upload.")
    ] = 100


class MultipartDirectoryUploadTransferConfig(Schema):
    """Configuration for multipart uploads (directory)."""

    max_concurrency: Annotated[
        int, Field(description="Maximum number of threads for uploading parts.")
    ] = 10


class PartUpload(Schema):
    """Multipart upload part."""

    file_path: Annotated[Path, Field(description="Path to the source file being uploaded")]
    part_number: Annotated[int, Field(description="Number of the part")]
    offset: Annotated[int, Field(description="Offset in bytes in the file to upload")]
    size: Annotated[int, Field(description="Size in bytes of the part being uploaded")]
    url: Annotated[str, Field(description="Presigned url for uploading")]


class MultipartDirectoryFileRequest(Schema):
    """Multipart upload request for files in a directory."""

    filename: Annotated[
        str,
        Field(description="File name to be uploaded, relative to the base directory."),
    ]
    filesize: Annotated[
        int,
        Field(description="File size to be uploaded in bytes.", ge=0),
    ]
    sha256_digest: str | None = None
    content_type: Annotated[
        ContentType | None,
        Field(
            description=(
                "Content type of file. "
                "If not provided it will be deduced from the file's extension."
            )
        ),
    ] = None
    preferred_part_count: Annotated[
        int,
        Field(description="Hint of desired part count."),
    ]


class MultipartDirectoryUploadRequest(Schema):
    """Request schema for initiating a multipart directory upload."""

    directory_name: Annotated[
        str,
        Field(
            description="Name of the directory to be uploaded. Nested directories are not allowed.",
        ),
    ]
    files: Annotated[
        list[MultipartDirectoryFileRequest],
        Field(
            description="List of files to be uploaded inside the directory.",
            min_length=1,
        ),
    ]
    meta: dict | None = None
    label: AssetLabel

    @model_validator(mode="after")
    def verify_children(self):
        """Verify the validity of the children."""
        unique_filenames = {file.filename for file in self.files}
        if len(unique_filenames) != len(self.files):
            msg = "Filenames must be unique within the directory."
            raise ValueError(msg)
        return self


class MultipartDirectoryUploadResponse(Schema):
    """Response schema after initiating a multipart directory upload."""

    asset: Asset
    files: list[AssetWithUploadMeta]
