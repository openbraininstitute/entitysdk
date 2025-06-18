"""Asset related schemas."""

from pathlib import Path

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
