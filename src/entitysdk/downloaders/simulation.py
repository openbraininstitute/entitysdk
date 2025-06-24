"""Downloading functions for Simulation."""

import json
import logging
from pathlib import Path
from typing import cast

from entitysdk.client import Client
from entitysdk.dependencies.entity import ensure_has_assets, ensure_has_id
from entitysdk.models import Simulation
from entitysdk.types import ID

L = logging.getLogger(__name__)


def download_simulation_config_content(client: Client, *, model: Simulation) -> dict:
    """Download the the simulation config json into a dictionary."""
    ensure_has_id(model)
    ensure_has_assets(model)

    asset = client.select_assets(
        model,
        selection={"label": "sonata_simulation_config"},
    ).one()

    json_content: bytes = client.download_content(
        entity_id=cast(ID, model.id),
        entity_type=Simulation,
        asset_id=asset.id,
    )

    return json.loads(json_content)


def download_node_sets_file(client: Client, *, model: Simulation, output_path: Path) -> Path:
    """Download the node sets file from simulation's assets."""
    ensure_has_id(model)
    ensure_has_assets(model)

    asset = client.select_assets(
        model,
        selection={"label": "custom_node_sets"},
    ).one()

    path = client.download_file(
        entity_id=cast(ID, model.id),
        entity_type=Simulation,
        asset_id=asset,
        output_path=output_path,
    )

    L.info("Node sets file downloaded at %s", path)

    return path


def download_spike_replay_files(
    client: Client, *, model: Simulation, output_dir: Path
) -> list[Path]:
    """Download the spike replay files from simualtion's assets."""
    ensure_has_id(model)
    ensure_has_assets(model)

    assets = client.select_assets(model, selection={"label": "replay_spikes"}).all()

    spike_files: list[Path] = [
        client.download_file(
            entity_id=cast(ID, model.id),
            entity_type=Simulation,
            asset_id=asset,
            output_path=output_dir / asset.path,
        )
        for asset in assets
    ]

    L.info("Downloaded %d spike replay files: %s", len(spike_files), spike_files)

    return spike_files
