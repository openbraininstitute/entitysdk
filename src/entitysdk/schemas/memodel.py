"""MEModel related schemas."""

from pathlib import Path

from entitysdk.schemas.base import Schema


class DownloadedMEModel(Schema):
    """Downloaded asset."""

    hoc_path: Path
    hoc_files: list[str]
    mechanisms_dir: Path
    mechanism_files: list[str]
    morphology_path: Path
