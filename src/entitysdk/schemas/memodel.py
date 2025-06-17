"""MEModel related schemas."""

from pathlib import Path

from entitysdk.schemas.base import Schema


class DownloadedMEModel(Schema):
    """Downloaded asset."""

    hoc_path: Path
    mechanisms_dir: Path
    morphology_path: Path
