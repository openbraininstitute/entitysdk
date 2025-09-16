"""Staging functions for Single-Cell."""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

import h5py

from entitysdk.client import Client
from entitysdk.downloaders.memodel import download_memodel, DownloadedMEModel
from entitysdk.models.memodel import MEModel
from entitysdk.exception import StagingError
from entitysdk.utils.io import write_json

L = logging.getLogger(__name__)

DEFAULT_CIRCUIT_CONFIG_FILENAME = "circuit_config.json"


def stage_sonata_from_memodel(
    client: Client,
    memodel: MEModel,
    output_dir: Path = Path("."),
) -> Path:
    """Stages a SONATA single-cell circuit from an MEModel entity.

    Downloads the MEModel and converts it into SONATA circuit format.

    Returns:
        Path to generated circuit_config.json (inside SONATA folder).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:

        downloaded_me_model = download_memodel(client, memodel=memodel, output_dir=tmp_dir)
        mtype = memodel.mtypes[0].pref_label if memodel.mtypes else ""

        if memodel.calibration_result is None:
            raise StagingError(f"MEModel {memodel.id} has no calibration result.")

        threshold_current = memodel.calibration_result.threshold_current
        holding_current = memodel.calibration_result.holding_current

        generate_sonata_files_from_memodel(
            downloaded_memodel=downloaded_me_model,
            output_path=output_dir,
            mtype=mtype,
            threshold_current=threshold_current,
            holding_current=holding_current,
        )

    config_path = output_dir / DEFAULT_CIRCUIT_CONFIG_FILENAME
    if not config_path.exists():
        raise FileNotFoundError(f"Expected circuit config not found at: {config_path}")

    L.info("Single-Cell %s staged at %s", memodel.id, config_path)

    return config_path


def generate_sonata_files_from_memodel(
    downloaded_memodel: DownloadedMEModel, # Was memodel_path
    output_path: Path,
    mtype: str,
    threshold_current: float,
    holding_current: float,
):
    """Generate SONATA single cell circuit structure from a downloaded MEModel folder.

    Args:
        downloaded_memodel (DownloadedMEModel): The downloaded MEModel object.
        output_path (str or Path): Path to the output 'sonata' folder.
        mtype (str): Cell mtype.
        threshold_current (float): Threshold current.
        holding_current (float): Holding current.
    """
    subdirs = {
        "hocs": output_path / "hocs",
        "mechanisms": output_path / "mechanisms",
        "morphologies": output_path / "morphologies",
        "network": output_path / "network",
    }
    for path in subdirs.values():
        path.mkdir(parents=True, exist_ok=True)

    # Copy hoc file
    hoc_file = next(downloaded_memodel.hoc_path.glob("*.hoc"), None)
    if not hoc_file:
        raise FileNotFoundError(f"No .hoc files found in {downloaded_memodel.hoc_path}")
    hoc_dst = subdirs["hocs"] / hoc_file.name
    if hoc_file.resolve() != hoc_dst.resolve():
        shutil.copy(hoc_file, hoc_dst)

    # Copy morphology file
    morph_file = next(downloaded_memodel.morphology_path.glob("*.asc"), None)
    if not morph_file:
        raise FileNotFoundError(f"No .asc morphology file found in {downloaded_memodel.morphology_path}")
    morph_dst = subdirs["morphologies"] / morph_file.name
    if morph_file.resolve() != morph_dst.resolve():
        shutil.copy(morph_file, morph_dst)

    # Copy mechanisms
    for file in (downloaded_memodel.mechanisms_path).iterdir():
        if file.is_file():
            target = subdirs["mechanisms"] / file.name
            if file.resolve() != target.resolve():
                shutil.copy(file, target)

    create_nodes_file(
        hoc_file=str(hoc_dst),
        morph_file=str(morph_dst),
        output_path=Path(str(subdirs["network"])),
        mtype=mtype,
        threshold_current=threshold_current,
        holding_current=holding_current,
    )

    create_circuit_config(output_path=output_path)
    create_node_sets_file(output_path=output_path)

    L.debug(f"SONATA single cell circuit created at {output_path}")


def create_nodes_file(
    hoc_file: str,
    morph_file: str,
    output_path: Path,
    mtype: str,
    threshold_current: float,
    holding_current: float,
):
    """Create a SONATA nodes.h5 file for a single cell population.

    Args:
        hoc_file (str): Path to the hoc file.
        morph_file (str): Path to the morphology file.
        output_path (str): Directory where nodes.h5 will be written.
        mtype (str): Cell mtype.
        threshold_current (float): Threshold current value.
        holding_current (float): Holding current value.
    """
    os.makedirs(output_path, exist_ok=True)
    nodes_h5_path = output_path / "nodes.h5"

    with h5py.File(nodes_h5_path, "w") as f:
        nodes = f.create_group("nodes")
        population = nodes.create_group("All")
        population.create_dataset("node_type_id", (1,), dtype="int64")[0] = -1
        group_0 = population.create_group("0")

        # Add dynamics_params fields
        dynamics = group_0.create_group("dynamics_params")
        dynamics.create_dataset("holding_current", (1,), dtype="float32")[0] = holding_current
        dynamics.create_dataset("threshold_current", (1,), dtype="float32")[0] = threshold_current

        # Standard string properties
        group_0.create_dataset("model_template", (1,), dtype=h5py.string_dtype())[0] = (
            f"hoc:{Path(hoc_file).stem}"
        )
        group_0.create_dataset("model_type", (1,), dtype="int32")[0] = 0
        group_0.create_dataset("morph_class", (1,), dtype="int32")[0] = 0
        group_0.create_dataset("morphology", (1,), dtype=h5py.string_dtype())[0] = (
            f"morphologies/{Path(morph_file).stem}"
        )
        group_0.create_dataset("mtype", (1,), dtype=h5py.string_dtype())[0] = mtype

        # Coordinates and rotation
        for name in [
            "x",
            "y",
            "z",
            "rotation_angle_xaxis",
            "rotation_angle_yaxis",
            "rotation_angle_zaxis",
        ]:
            group_0.create_dataset(name, (1,), dtype="float32")[0] = 0.0

        # Quaternion orientation
        orientation = {
            "orientation_w": 1.0,
            "orientation_x": 0.0,
            "orientation_y": 0.0,
            "orientation_z": 0.0,
        }
        for name, value in orientation.items():
            group_0.create_dataset(name, (1,), dtype="float64")[0] = value

        # Optional fields
        group_0.create_dataset("morphology_producer", (1,), dtype=h5py.string_dtype())[0] = (
            "biologic"
        )

    L.debug(f"Successfully created nodes.h5 file at {nodes_h5_path}")


def create_circuit_config(output_path: Path, node_population_name: str = "All"):
    """Create a SONATA circuit_config.json for a single cell.

    Args:
        output_path (str): Directory where circuit_config.json will be written.
        node_population_name (str): Name of the node population (default: 'All').
    """
    config = {
        "manifest": {"$BASE_DIR": ".", "$COMPONENT_DIR": ".", "$NETWORK_DIR": "$BASE_DIR/network"},
        "components": {
            "morphologies_dir": "$COMPONENT_DIR/morphologies",
            "biophysical_neuron_models_dir": "$COMPONENT_DIR/hocs",
        },
        "node_sets_file": "$BASE_DIR/node_sets.json",
        "networks": {
            "nodes": [
                {
                    "nodes_file": "$NETWORK_DIR/nodes.h5",
                    "populations": {
                        node_population_name: {
                            "type": "biophysical",
                            "morphologies_dir": "$COMPONENT_DIR/",
                            "alternate_morphologies": {"neurolucida-asc": "$COMPONENT_DIR/"},
                        }
                    },
                }
            ],
            "edges": [],
        },
    }
    config_path = output_path / "circuit_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    L.debug(f"Successfully created circuit_config.json at {config_path}")


def create_node_sets_file(
    output_path: Path,
    node_population_name: str = "All",
    node_set_name: str = "All",
    node_id: int = 0,
):
    """Create a node_sets.json file for a single cell.

    Args:
        output_path (str): Directory where node_sets.json will be written.
        node_population_name (str): Name of the node population (default: 'All').
        node_set_name (str): Name of the node set (default: 'All').
        node_id (int): Node ID to include (default: 0).
    """
    node_sets = {node_set_name: {"population": node_population_name, "node_id": [node_id]}}
    node_sets_path = output_path / "node_sets.json"
    write_json(node_sets, node_sets_path)
    L.debug(f"Successfully created node_sets.json at {node_sets_path}")
