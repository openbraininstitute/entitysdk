"""Utility functions for filesystem operations."""

from pathlib import Path

from entitysdk.types import StrOrPath


def create_dir(path: StrOrPath) -> Path:
    """Create directory and parents if it doesn't already exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_filesize(path: StrOrPath) -> int:
    """Return filesize."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")

    if not path.is_file():
        raise IsADirectoryError(f"Path {path} is not a file.")

    return path.stat().st_size
