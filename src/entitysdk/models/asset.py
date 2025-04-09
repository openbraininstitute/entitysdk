"""Asset models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from entitysdk.models.core import Identifiable


class Asset(Identifiable):
    """Asset."""

    path: Annotated[
        str,
        Field(
            description="The path of the asset.",
        ),
    ]
    full_path: Annotated[
        str,
        Field(
            description="The full path of the asset.",
        ),
    ]
    is_directory: Annotated[
        bool,
        Field(
            description="Whether the asset is a directory.",
        ),
    ]
    content_type: Annotated[
        str,
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
        str | None,
        Field(
            examples=["created", "deleted"],
            description="The status of the asset.",
        ),
    ] = None
    meta: Annotated[
        dict | None,
        Field(description="Asset json metadata."),
    ] = None


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
        str,
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
