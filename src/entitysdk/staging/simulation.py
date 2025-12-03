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
from entitysdk.staging.constants import (
    DEFAULT_NODE_POPULATION_NAME,
    DEFAULT_NODE_SET_NAME,
)
from entitysdk.staging.memodel import stage_sonata_from_memodel
from entitysdk.types import EntityType, StrOrPath
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
        base_entity = client.get_entity(entity_id=model.entity_id, entity_type=Entity)
        match base_entity.type:
            case EntityType.memodel:
                memodel = client.get_entity(entity_id=model.entity_id, entity_type=MEModel)
                L.info(
                    "Staging single-cell SONATA circuit from MEModel %s",
                    memodel.id,
                )
                node_sets_file = _stage_single_cell_node_sets_file(
                    node_set_name=simulation_config.get("node_set", DEFAULT_NODE_SET_NAME),
                    output_path=output_dir / DEFAULT_NODE_SETS_FILENAME,
                )
                circuit_config_path = stage_sonata_from_memodel(
                    client,
                    memodel=memodel,
                    output_dir=create_dir(output_dir / DEFAULT_CIRCUIT_DIR),
                )
            case EntityType.circuit:
                circuit = client.get_entity(entity_id=model.entity_id, entity_type=Circuit)
                L.info(
                    "Staging SONATA circuit from Circuit %s",
                    circuit.id,
                )
                node_sets_file = download_node_sets_file(
                    client,
                    model=model,
                    output_path=output_dir / DEFAULT_NODE_SETS_FILENAME,
                )
                circuit_config_path = stage_circuit(
                    client,
                    model=circuit,
                    output_dir=create_dir(output_dir / DEFAULT_CIRCUIT_DIR),
                )
            case _:
                raise StagingError(
                    f"Simulation {model.id} references unsupported type {base_entity.type}"
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


def _stage_single_cell_node_sets_file(
    node_set_name: str,
    output_path: Path,
) -> Path | None:
    write_json(
        {
            node_set_name: {
                "population": DEFAULT_NODE_POPULATION_NAME,
                "node_id": [0],
            }
        },
        output_path,
    )
    return output_path


def _transform_simulation_config(
    simulation_config: dict,
    circuit_config_path: Path,
    node_sets_path: Path | None,
    spike_paths: list[Path],
    output_dir: Path,
    override_results_dir: Path | None,
) -> dict:
    ret = simulation_config | {
        "network": str(circuit_config_path),
        "output": _transform_output(
            simulation_config.get("output", {}),
            override_results_dir,
        ),
    }

    if spike_paths and "inputs" not in simulation_config:
        raise StagingError("Simulation has spikes, but no `inputs` defined")

    ret["inputs"] = _transform_inputs(simulation_config.get("inputs", {}), spike_paths)

    if node_sets_path is not None:
        ret["node_sets_file"] = str(node_sets_path.relative_to(output_dir))

    return ret


def _transform_inputs(inputs: dict, spike_paths: list[Path]) -> dict:
    expected_spike_filenames = {p.name for p in spike_paths}

    transformed_inputs = deepcopy(inputs)
    for values in transformed_inputs.values():
        if values["input_type"] != "spikes":
            continue

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

    output["output_dir"] = str(path)
    output["spikes_file"] = str(path / "spikes.h5")

    return output
