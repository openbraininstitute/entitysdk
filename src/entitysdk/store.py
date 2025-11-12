"""Data mounting module."""

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

    def _mounted_path(self, path: str | Path) -> Path:
        """Return path from within the context of the data mount prefix."""
        return Path(self.prefix, path)

    def path_exists(self, path: str | Path) -> bool:
        """Return True if path exists in the data mount."""
        return self._mounted_path(path).exists()

    def link_path(self, source: str | Path, target: str | Path) -> Path:
        """Create a soft link from data mount to target."""
        Path(target).symlink_to(self._mounted_path(source))
        return Path(target)

    def read_bytes(self, path: str | Path) -> bytes:
        """Read file from data mount."""
        return self._mounted_path(path).read_bytes()
