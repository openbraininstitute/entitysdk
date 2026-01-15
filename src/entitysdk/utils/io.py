"""IO utilities."""

import hashlib
import io
import json
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
        for chunk in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()
