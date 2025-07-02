"""Staging functions for SimulationResult."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.simulation_result import (
    download_spike_report_file,
    download_voltage_report_files,
)
from entitysdk.models import Simulation, SimulationResult
from entitysdk.staging.simulation import stage_simulation
from entitysdk.types import StrOrPath
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import load_json

L = logging.getLogger(__name__)


DEFAULT_REPORTS_DIR_NAME = "output"
DEFAULT_SPIKE_FILE_NAME = "output/spikes.h5"
DEFAULT_SIMULATION_CONFIG_FILENAME = "simulation_config.json"


def stage_simulation_result(
    client: Client,
    *,
    model: SimulationResult,
    output_dir: StrOrPath,
    simulation_config_file: StrOrPath | None = None,
) -> Path:
    """Stage a SimulationResult entity."""
    output_dir: Path = create_dir(output_dir)

    if simulation_config_file is None:
        L.info(
            "Simulation will be staged from simulation result's simulation_id %s",
            model.simulation_id,
        )
        simulation_config_file = stage_simulation(
            client,
            model=client.get_entity(entity_id=model.simulation_id, entity_type=Simulation),
            output_dir=output_dir,
        )
    else:
        L.info(
            "External simulation config provided at %s. Outputs will be staged relative to it.",
            simulation_config_file,
        )

    config: dict = load_json(simulation_config_file)
    reports_dir, spikes_file = _get_output_paths(config, Path(simulation_config_file).parent)
    create_dir(reports_dir)

    download_spike_report_file(
        client,
        model=model,
        output_path=spikes_file,
    )
    download_voltage_report_files(
        client,
        model=model,
        output_dir=reports_dir,
    )

    return Path(simulation_config_file)


def _get_output_paths(config: dict, output_dir: Path) -> tuple[Path, Path]:
    reports_dir = output_dir / config["output"]["output_dir"]
    spikes_file = reports_dir / config["output"]["spikes_file"]
    return reports_dir, spikes_file
