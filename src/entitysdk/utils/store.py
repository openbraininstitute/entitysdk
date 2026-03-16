"""Local asset store module."""

import shutil
from pathlib import Path

from pydantic import BaseModel, DirectoryPath


class LocalAssetStore(BaseModel):
    """Class for locally stored asset data."""

    prefix: DirectoryPath

    def _local_path(self, path: Path) -> Path:
        """Return path from within the store."""
        return self.prefix / path

    def path_exists(self, path: Path) -> bool:
        """Return True if path exists in the store."""
        return self._local_path(path).exists()

    def link_path(self, path: Path, target_path: Path) -> Path:
        """Create a soft link from store to target path."""
        store_path = self._local_path(path)
        target_path.symlink_to(store_path)
        return target_path

    def copy_path(self, path: Path, target_path: Path) -> Path:
        """Copy file from store to target path."""
        store_path = self._local_path(path)
        shutil.copyfile(store_path, target_path)
        return target_path

    def read_bytes(self, path: Path) -> bytes:
        """Read file from local store."""
        return self._local_path(path).read_bytes()
