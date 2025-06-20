import logging
from copy import deepcopy
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.simulation import (
    download_node_sets_file,
    download_simulation_config_content,
)
from entitysdk.models import Simulation
from entitysdk.types import StrOrPath
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import write_json

L = logging.getLogger(__name__)

DEFAULT_NODE_SETS_FILENAME = "node_sets.json"
DEFAULT_SIMULATION_CONFIG_FILENAME = "simulation_config.json"


def stage_simulation(
    client: Client,
    *,
    model: Simulation,
    output_dir: StrOrPath,
    circuit_config_path: Path | None = None,
):
    """Stage a simulation entity into output_dir."""
    output_dir = create_dir(output_dir).resolve()

    simulation_config: dict = download_simulation_config_content(client, model=model)
    node_sets_file: Path = download_node_sets_file(
        client, model=model, output_path=output_dir / DEFAULT_NODE_SETS_FILENAME
    )
    spike_paths: list[Path] = _download_spike_replay_files(
        client, model=model, output_dir=output_dir
    )

    transformed_simulation_config: dict = _transform_simulation_config(
        simulation_config=simulation_config,
        circuit_config_path=circuit_config_path,
        node_sets_path=node_sets_file,
        spike_paths=spike_paths,
        output_dir=output_dir,
    )

    write_json(
        data=transformed_simulation_config,
        path=output_dir / DEFAULT_SIMULATION_CONFIG_FILENAME,
    )


def _transform_simulation_config(
    simulation_config: dict,
    circuit_config_path: Path,
    node_sets_path: Path,
    spike_paths: list[Path],
    output_dir: Path,
) -> dict:
    return simulation_config | {
        "network": str(circuit_config_path),
        "node_sets_file": str(node_sets_path.relative_to(output_dir)),
        "inputs": _transform_inputs(simulation_config["inputs"], spike_paths),
    }


def _transform_inputs(inputs, spike_paths):
    expected_spike_filenames = {p.name for p in spike_paths}

    transformed_inputs = deepcopy(inputs)
    for values in transformed_inputs.values():
        if values["input_type"] == "spikes":
            path = Path(values["spike_file"]).name

            if path not in expected_spike_filenames:
                raise

            values["spike_file"] = str(path)
            L.debug("Spike file %s -> %s", values["spike_file"], path)

    return transformed_inputs
