"""Asset models."""

from io import BufferedReader, BytesIO

from pydantic import BaseModel, ConfigDict

from entitysdk.core import Identifiable


class Asset(Identifiable):
    """Asset."""

    path: str
    fullpath: str
    bucket_name: str
    is_directory: bool
    content_type: str
    size: int
    meta: dict
    status: str | None = None


class LocalAsset(BaseModel):
    """A local asset to upload."""

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    filename: str
    content_type: str
    content: BufferedReader | BytesIO | bytes | str
