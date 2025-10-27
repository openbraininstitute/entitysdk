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
from entitysdk.models import Circuit, MEModel, Simulation
from entitysdk.models.entity import Entity
from entitysdk.staging.circuit import stage_circuit
from entitysdk.staging.memodel import stage_sonata_from_memodel
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
        entity = client.get_entity(entity_id=model.entity_id, entity_type=Entity)
        L.info(entity.type)
        str_to_class_type = {
            "MEModel": MEModel,
            "Circuit": Circuit,
        }

        entity = client.get_entity(entity_id=model.entity_id, entity_type=str_to_class_type[entity.type])  # type: ignore[arg-type, var-annotated]
        if entity is None:
            raise StagingError(f"Could not resolve entity {model.entity_id} as {model.type}.")

        if isinstance(entity, MEModel):
            L.info(
                "Staging single-cell SONATA circuit from MEModel %s",
                entity.id,
            )

            node_set_name = simulation_config.get("node_set", "All")
            node_sets_file = output_dir / "node_sets.json"
            write_json(
                {node_set_name: {"population": "All", "node_id": [0]}},
                node_sets_file,
            )

            circuit_config_path = stage_sonata_from_memodel(
                client,
                memodel=entity,
                output_dir=create_dir(output_dir / DEFAULT_CIRCUIT_DIR),
            )
        elif isinstance(entity, Circuit):
            L.info(
                "Staging SONATA circuit from Circuit %s",
                entity.id,
            )
            node_sets_file = download_node_sets_file(
                client,
                model=model,
                output_path=output_dir / DEFAULT_NODE_SETS_FILENAME,
            )
            circuit_config_path = stage_circuit(
                client,
                model=entity,
                output_dir=create_dir(output_dir / DEFAULT_CIRCUIT_DIR),
            )
        else:
            raise StagingError(
                f"Simulation {model.id} references unsupported entity type: {type(entity).__name__}"
            )
    else:
        node_sets_file = download_node_sets_file(
            client,
            model=model,
            output_path=output_dir / DEFAULT_NODE_SETS_FILENAME,
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
    write_json(data=transformed_simulation_config, path=output_simulation_config_file)

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
