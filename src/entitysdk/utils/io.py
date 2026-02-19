"""IO utilities."""

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

from entitysdk.types import StrOrPath


def write_json(data: dict, path: StrOrPath, **json_kwargs) -> None:
    """Write dictionary to file as JSON."""
    Path(path).write_text(json.dumps(data, **json_kwargs))


def load_json(path: StrOrPath) -> dict:
    """Load JSON file to dict."""
    return json.loads(Path(path).read_bytes())


def calculate_sha256_digest(path: Path) -> str:
    """Calculate the sha256 digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()


def iter_bytes_chunk(path: Path, offset: int, size: int, buffer_size: int) -> Iterator[bytes]:
    """Yield a specific chunk of bytes from a file in smaller pieces.

    Args:
        path (Path): Path to the file.
        offset (int): Byte offset to start reading from.
        size (int): Total number of bytes to read.
        buffer_size (int): Maximum number of bytes to read per iteration.

    Yields:
        bytes: Pieces of the requested file chunk.
    """
    with open(path, "rb") as f:
        f.seek(offset)

        remaining = size
        while remaining > 0:
            read_size = min(buffer_size, remaining)

            if not (data := f.read(read_size)):
                break

            yield data
            remaining -= read_size
