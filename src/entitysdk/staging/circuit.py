"""Staging functions for Circuit."""

import logging
from pathlib import Path
from typing import cast

from entitysdk.client import Client
from entitysdk.dependencies.entity import ensure_has_assets, ensure_has_id
from entitysdk.models import Circuit
from entitysdk.types import ID

L = logging.getLogger(__name__)


def stage_circuit(
    client: Client, *, model: Circuit, output_dir: Path, max_concurrent: int = 1
) -> Path:
    """Stage a Circuit directory into output_dir."""
    ensure_has_id(model)
    ensure_has_assets(model)

    asset = client.select_assets(
        model,
        selection={
            "content_type": "application/vnd.directory",
            "is_directory": True,
            "label": "sonata_circuit",
        },
    ).one()

    paths = client.download_directory(
        entity_id=cast(ID, model.id),
        entity_type=Circuit,
        asset_id=asset,
        output_path=output_dir,
        ignore_directory_name=True,
        max_concurrent=max_concurrent,
    )

    L.debug("Downloaded circuit %s paths: %s", model.id, paths)

    circuit_config_path = output_dir / "circuit_config.json"
    assert circuit_config_path in paths

    L.info("Circuit %s staged at %s", model.id, circuit_config_path)

    return circuit_config_path
