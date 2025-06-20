"""IO utilities."""

import json
from pathlib import Path

from entitysdk.types import StrOrPath


def write_json(data: dict, path: StrOrPath, **json_kwargs) -> None:
    """Write dictionary to file as JSON."""
    Path(path).write_text(json.dumps(data, **json_kwargs))


def load_json(path: StrOrPath) -> dict:
    """Load JSON file to dict."""
    return json.loads(Path(path).read_bytes())
