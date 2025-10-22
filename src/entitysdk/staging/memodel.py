"""Staging functions for Single-Cell."""

import json
import logging
import shutil
import tempfile
from pathlib import Path

import h5py

from entitysdk.client import Client
from entitysdk.downloaders.memodel import DownloadedMEModel, download_memodel
from entitysdk.exception import StagingError
from entitysdk.models.memodel import MEModel
from entitysdk.utils.filesystem import create_dir
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

        if memodel.mtypes is None:
            raise StagingError(f"MEModel {memodel.id} has no mtypes defined.")

        mtype = memodel.mtypes[0].pref_label

        if memodel.calibration_result is None:
            raise StagingError(f"MEModel {memodel.id} has no calibration result.")

        threshold_current = memodel.calibration_result.threshold_current
        holding_current = memodel.calibration_result.holding_current

        _generate_sonata_files_from_memodel(
            downloaded_memodel=downloaded_me_model,
            output_path=output_dir,
            mtype=mtype,
            threshold_current=threshold_current,
            holding_current=holding_current,
        )

    config_path = output_dir / DEFAULT_CIRCUIT_CONFIG_FILENAME

    L.info("Single-Cell %s staged at %s", memodel.id, config_path)

    return config_path


def _generate_sonata_files_from_memodel(
    downloaded_memodel: DownloadedMEModel,
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
        create_dir(path)

    # Copy hoc file
    hoc_file = downloaded_memodel.hoc_path
    if not downloaded_memodel.hoc_path.exists():
        raise FileNotFoundError(f"No HOC file found {downloaded_memodel.hoc_path}")
    hoc_dst = subdirs["hocs"] / hoc_file.name
    shutil.copy(hoc_file, hoc_dst)

    # Copy morphology file
    if not downloaded_memodel.morphology_path.exists():
        raise FileNotFoundError(f"No morphology file found {downloaded_memodel.morphology_path}")
    morph_dst = subdirs["morphologies"] / downloaded_memodel.morphology_path.name
    shutil.copy(downloaded_memodel.morphology_path, morph_dst)

    # Copy mechanisms
    for file in downloaded_memodel.mechanism_files:
        src_path = downloaded_memodel.mechanisms_dir / file
        if Path(src_path).exists():
            target = subdirs["mechanisms"] / file
            shutil.copy(src_path, target)

    create_nodes_file(
        hoc_file=str(hoc_dst),
        morph_file=str(morph_dst),
        output_file=Path(str(subdirs["network"])) / "nodes.h5",
        mtype=mtype,
        threshold_current=threshold_current,
        holding_current=holding_current,
    )

    create_circuit_config(output_path=output_path)
    create_node_sets_file(output_file=output_path / "node_sets.json")

    L.debug(f"SONATA single cell circuit created at {output_path}")


def create_nodes_file(
    hoc_file: str,
    morph_file: str,
    output_file: Path,
    mtype: str,
    threshold_current: float,
    holding_current: float,
):
    """Create a SONATA nodes.h5 file for a single cell population.

    Args:
        hoc_file (str): Path to the hoc file.
        morph_file (str): Path to the morphology file.
        output_file (Path): Output file path for nodes.h5.
        mtype (str): Cell mtype.
        threshold_current (float): Threshold current value.
        holding_current (float): Holding current value.
    """
    output_file = Path(output_file)  # ensure Path type
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_file, "w") as f:
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

    L.debug(f"Successfully created file at {output_file}")


def create_circuit_config(output_path: Path, node_population_name: str = "All"):
    """Create a SONATA circuit_config.json for a single cell.

    Args:
        output_path (str): Directory where circuit_config.json will be written.
        node_population_name (str): Name of the node population (default: 'All').
    """
    config = {
        "manifest": {"$BASE_DIR": "."},
        "node_sets_file": "$BASE_DIR/node_sets.json",
        "networks": {
            "nodes": [
                {
                    "nodes_file": "$BASE_DIR/network/nodes.h5",
                    "populations": {
                        node_population_name: {
                            "type": "biophysical",
                            "morphologies_dir": "$BASE_DIR/morphologies",
                            "biophysical_neuron_models_dir": "$BASE_DIR/hocs",
                            "alternate_morphologies": {"neurolucida-asc": "$BASE_DIR/"},
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
    output_file: Path,
    node_population_name: str = "All",
    node_set_name: str = "All",
    node_id: int = 0,
):
    """Create a node_sets.json file for a single cell.

    Args:
        output_file (Path): Output file path for node_sets.json.
        node_population_name (str): Name of the node population (default: 'All').
        node_set_name (str): Name of the node set (default: 'All').
        node_id (int): Node ID to include (default: 0).
    """
    node_sets = {node_set_name: {"population": node_population_name, "node_id": [node_id]}}
    write_json(node_sets, output_file)
    L.debug(f"Successfully created node_sets.json at {output_file}")
