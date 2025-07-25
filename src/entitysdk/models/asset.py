"""Asset models."""

import datetime
import pathlib
from typing import Annotated

from pydantic import ConfigDict, Field

from entitysdk.models.base import BaseModel
from entitysdk.models.core import Identifiable
from entitysdk.types import ID, AssetLabel, AssetStatus, ContentType, StorageType


class Asset(Identifiable):
    """Asset."""

    id: ID

    path: Annotated[
        str,
        Field(
            description="The relative path of the asset.",
        ),
    ]
    full_path: Annotated[
        str,
        Field(
            description="The full s3 path of the asset.",
        ),
    ]
    is_directory: Annotated[
        bool,
        Field(
            description="Whether the asset is a directory.",
        ),
    ]
    content_type: Annotated[
        ContentType,
        Field(
            examples=["image/png", "application/json"],
            description="The content type of the asset.",
        ),
    ]
    size: Annotated[
        int,
        Field(
            examples=[1000],
            description="The size of the asset in bytes.",
        ),
    ]
    sha256_digest: Annotated[
        str | None,
        Field(
            description="The sha256 digest of the file content.",
        ),
    ] = None
    status: Annotated[
        AssetStatus | None,
        Field(
            examples=["created", "deleted"],
            description="The status of the asset.",
        ),
    ] = None
    meta: Annotated[
        dict,
        Field(description="Asset json metadata."),
    ] = {}
    label: Annotated[AssetLabel, Field(description="Asset label.")]


class LocalAssetMetadata(BaseModel):
    """A local asset to upload."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    file_name: Annotated[
        str,
        Field(
            examples=["image.png"],
            description="The name of the file.",
        ),
    ]
    content_type: Annotated[
        ContentType,
        Field(
            examples=["image/png"],
            description="The content type of the asset.",
        ),
    ]
    metadata: Annotated[
        dict | None,
        Field(
            description="The metadata of the asset.",
        ),
    ] = None
    label: Annotated[AssetLabel, Field(description="Mandatory asset label.")]


class ExistingAssetMetadata(BaseModel):
    """An existing asset to register."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    path: Annotated[
        str,
        Field(
            examples=["image.png"],
            description="The name of the file or directory, without leading components.",
        ),
    ]
    full_path: Annotated[
        str,
        Field(
            examples=["path/to/image.png"],
            description="The full remote path of the file or directory, without the bucket.",
        ),
    ]
    storage_type: Annotated[
        StorageType,
        Field(
            examples=["aws_s3_open"],
            description="Storage where the asset is located.",
        ),
    ]
    is_directory: Annotated[
        bool,
        Field(
            description="Whether the asset is a directory.",
        ),
    ]
    content_type: Annotated[
        ContentType,
        Field(
            examples=["image/png"],
            description="The content type of the asset.",
        ),
    ]
    label: Annotated[
        AssetLabel,
        Field(
            examples=["morphology"],
            description="Mandatory asset label.",
        ),
    ]


class DetailedFile(BaseModel):
    """File stored in a directory."""

    name: Annotated[
        str,
        Field(
            examples=["some_file_name.txt"],
            description="The name of the file.",
        ),
    ]
    size: Annotated[
        int,
        Field(
            examples=["314159"],
            description="Size of the file in bytes",
        ),
    ]
    last_modified: Annotated[
        datetime.datetime,
        Field(
            description="Date file was last modified",
        ),
    ]


class DetailedFileList(BaseModel):
    """List of files in a directory."""

    files: Annotated[
        dict[pathlib.Path, DetailedFile],
        Field(
            description="Mapping of paths to detailed information on file",
        ),
    ]
