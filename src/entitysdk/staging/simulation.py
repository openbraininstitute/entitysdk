"""Staging functions for Simulation."""

import logging
from copy import deepcopy
from pathlib import Path

from entitysdk.client import Client
from entitysdk.downloaders.simulation import (
    download_node_sets_file,
    download_simulation_config_content,
    download_spike_replay_files,
)
from entitysdk.exception import StagingError
from entitysdk.models import Circuit, Simulation
from entitysdk.staging.circuit import stage_circuit
from entitysdk.types import StrOrPath
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import write_json

L = logging.getLogger(__name__)

DEFAULT_NODE_SETS_FILENAME = "node_sets.json"
DEFAULT_SIMULATION_CONFIG_FILENAME = "simulation_config.json"
DEFAULT_CIRCUIT_DIR = "circuit"


def stage_simulation(
    client: Client,
    *,
    model: Simulation,
    output_dir: StrOrPath,
    circuit_config_path: Path | None = None,
    override_results_dir: Path | None = None,
) -> Path:
    """Stage a simulation entity into output_dir.

    Args:
        client: The client to use to stage the simulation.
        model: The simulation entity to stage.
        output_dir: The directory to stage the simulation into.
        circuit_config_path: The path to the circuit config file.
            If not provided, the circuit will be staged from metadata.
        override_results_dir: Directory to update the simulation config section to point to.

    Returns:
        The path to the staged simulation config file.
    """
    output_dir = create_dir(output_dir).resolve()

    simulation_config: dict = download_simulation_config_content(client, model=model)
    node_sets_file: Path = download_node_sets_file(
        client,
        model=model,
        output_path=output_dir / DEFAULT_NODE_SETS_FILENAME,
    )
    spike_paths: list[Path] = download_spike_replay_files(
        client,
        model=model,
        output_dir=output_dir,
    )
    if circuit_config_path is None:
        L.info(
            "Circuit config path was not provided. Circuit is going to be staged from metadata. "
            "Circuit id to be staged: %s"
        )
        circuit_config_path = stage_circuit(
            client,
            model=client.get_entity(
                entity_id=model.entity_id,
                entity_type=Circuit,
            ),
            output_dir=create_dir(output_dir / DEFAULT_CIRCUIT_DIR),
        )

    transformed_simulation_config: dict = _transform_simulation_config(
        simulation_config=simulation_config,
        circuit_config_path=circuit_config_path,
        node_sets_path=node_sets_file,
        spike_paths=spike_paths,
        output_dir=output_dir,
        override_results_dir=override_results_dir,
    )

    output_simulation_config_file = output_dir / DEFAULT_SIMULATION_CONFIG_FILENAME

    write_json(
        data=transformed_simulation_config,
        path=output_simulation_config_file,
    )

    L.info("Staged Simulation %s at %s", model.id, output_dir)

    return output_simulation_config_file


def _transform_simulation_config(
    simulation_config: dict,
    circuit_config_path: Path,
    node_sets_path: Path,
    spike_paths: list[Path],
    output_dir: Path,
    override_results_dir: Path | None,
) -> dict:
    return simulation_config | {
        "network": str(circuit_config_path),
        "node_sets_file": str(node_sets_path.relative_to(output_dir)),
        "inputs": _transform_inputs(simulation_config["inputs"], spike_paths),
        "output": _transform_output(simulation_config["output"], override_results_dir),
    }


def _transform_inputs(inputs: dict, spike_paths: list[Path]) -> dict:
    expected_spike_filenames = {p.name for p in spike_paths}

    transformed_inputs = deepcopy(inputs)
    for values in transformed_inputs.values():
        if values["input_type"] == "spikes":
            path = Path(values["spike_file"]).name

            if path not in expected_spike_filenames:
                raise StagingError(
                    f"Spike file name in config is not present in spike asset file names.\n"
                    f"Config file name: {path}\n"
                    f"Asset file names: {expected_spike_filenames}"
                )

            values["spike_file"] = str(path)
            L.debug("Spike file %s -> %s", values["spike_file"], path)

    return transformed_inputs


def _transform_output(output: dict, override_results_dir: StrOrPath | None) -> dict:
    if override_results_dir is None:
        return output

    path = Path(override_results_dir)

    return {
        "output_dir": str(path),
        "spikes_file": str(path / "spikes.h5"),
    }
