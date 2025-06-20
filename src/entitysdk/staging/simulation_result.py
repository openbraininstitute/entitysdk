"""Staging functions for SimulationResult."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.simulation_result import (
    download_spike_report_file,
    download_voltage_report_files,
)
from entitysdk.models import SimulationResult
from entitysdk.types import StrOrPath
from entitysdk.utils.filesystem import create_dir

L = logging.getLogger(__name__)


def stage_simulation_result(
    client: Client,
    *,
    model: SimulationResult,
    output_dir: StrOrPath,
):
    """Stage a SimulationResult entity."""
    output_dir: Path = create_dir(output_dir)
    download_spike_report_file(
        client,
        model=model,
        output_path=output_dir / "spikes.h5",
    )
    download_voltage_report_files(
        client,
        model=model,
        output_dir=output_dir,
    )
