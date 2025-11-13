"""Local asset store module."""

from dataclasses import dataclass
from pathlib import Path

from entitysdk.exception import EntitySDKError


@dataclass
class LocalAssetStore:
    """Class for locally stored asset data."""

    prefix: Path

    def __post_init__(self):
        """Post init."""
        if not Path(self.prefix).exists():
            raise EntitySDKError(f"Mount prefix path '{self.prefix}' does not exist")

    def _local_path(self, path: str | Path) -> Path:
        """Return path from within the store."""
        return Path(self.prefix, path)

    def path_exists(self, path: str | Path) -> bool:
        """Return True if path exists in the store."""
        return self._local_path(path).exists()

    def link_path(self, source: str | Path, target: str | Path) -> Path:
        """Create a soft link from source to target."""
        Path(target).symlink_to(self._local_path(source))
        return Path(target)

    def read_bytes(self, path: str | Path) -> bytes:
        """Read file from local store."""
        return self._local_path(path).read_bytes()
