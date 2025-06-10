"""Asset related schemas."""

from pathlib import Path

from entitysdk.models.asset import Asset
from entitysdk.schemas.base import Schema


class DownloadedAsset(Schema):
    """Downloaded asset."""

    asset: Asset
    output_path: Path
