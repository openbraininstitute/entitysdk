"""Asset models."""

from pydantic import BaseModel, ConfigDict

from entitysdk.models.core import Identifiable


class Asset(Identifiable):
    """Asset."""

    path: str
    fullpath: str
    bucket_name: str
    is_directory: bool
    content_type: str
    size: int
    status: str | None = None
    meta: dict | None = None


class LocalAssetMetadata(BaseModel):
    """A local asset to upload."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    file_name: str
    content_type: str
    metadata: dict | None = None
