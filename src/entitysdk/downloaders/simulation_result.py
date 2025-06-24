"""Downloading functions for SimulationResult."""

import logging
from pathlib import Path
from typing import cast

from entitysdk.client import Client
from entitysdk.dependencies.entity import ensure_has_assets, ensure_has_id
from entitysdk.models import SimulationResult
from entitysdk.types import ID

L = logging.getLogger(__name__)


def download_spike_report_file(
    client: Client, *, model: SimulationResult, output_path: Path
) -> Path:
    """Download spike report file from SimulationResult entity."""
    ensure_has_id(model)
    ensure_has_assets(model)

    asset = client.select_assets(
        model,
        selection={"label": "spike_report"},
    ).one()

    path = client.download_file(
        entity_id=cast(ID, model.id),
        entity_type=SimulationResult,
        asset_id=asset,
        output_path=output_path / asset.path if output_path.is_dir() else output_path,
    )
    L.info("Spike report file downloaded at %s", path)
    return path


def download_voltage_report_files(
    client: Client, *, model: SimulationResult, output_dir: Path
) -> list[Path]:
    """Download voltage report files from SimulationResult entity."""
    ensure_has_id(model)
    ensure_has_assets(model)

    assets = client.select_assets(
        model,
        selection={"label": "voltage_report"},
    ).all()

    files: list[Path] = [
        client.download_file(
            entity_id=cast(ID, model.id),
            entity_type=SimulationResult,
            asset_id=asset,
            output_path=output_dir / asset.path,
        )
        for asset in assets
    ]

    L.info("Downloaded voltage report files: %s", files)

    return files
