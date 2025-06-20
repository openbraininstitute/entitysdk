import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.simulation import download_simulation_config_content
from entitysdk.models import SimulationResult
from entitysdk.types import StrOrPath
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import load_json

L = logging.getLogger(__name__)


def stage_simulation_result(
    client: Client,
    *,
    model: SimulationResult,
    output_dir: StrOrPath,
):
    output_dir = create_dir(output_dir)
    spike_report_file = _download_spike_report_file(
        client,
        model=model,
        output_dir=output_dir,
    )
    voltage_report_files = _download_voltage_report_files(
        client,
        model=model,
        output_dir=output_dir,
    )


def _get_simulation_config(config_path: Path | None, client, model):
    if config_path:
        L.info("External simulation config %s will be used.", config_path)
        return load_json(path=config_path)

    download_simulation_config_content()


def _download_spike_report_file(client, *, model: SimulationResult, output_path: Path) -> Path:
    asset = client.select_assets(
        model,
        selection={"label": "spike_report"},
    ).one()

    path = client.download_file(
        entity_id=model.id,
        entity_type=SimulationResult,
        asset=asset,
        output_path=output_path / asset.path if output_path.is_dir() else output_path,
    )
    L.info("Spike report file downloaded at %s", path)
    return path


def _download_voltage_report_files(
    client, *, model: SimulationResult, output_dir: Path
) -> list[Path]:
    assets = client.select_assets(
        model,
        selection={"label": "voltage_report"},
    ).all()

    if not assets:
        L.info("No voltage reports found in SimulationResult {%s}", model.id)
        return {}

    files: list[Path] = [
        client.download_file(
            entity_id=model.id,
            entity_type=SimulationResult,
            asset=asset,
            output_path=output_dir / asset.path,
        )
        for asset in assets
    ]

    L.info("Downloaded voltage report files: %s", files)

    return files
