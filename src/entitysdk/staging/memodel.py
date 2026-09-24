"""Staging functions for Single-Cell."""

import logging
import re
import shutil
import tempfile
from pathlib import Path

import h5py

from entitysdk.client import Client
from entitysdk.downloaders.memodel import DownloadedMEModel, download_memodel
from entitysdk.exception import StagingError
from entitysdk.models.memodel import MEModel
from entitysdk.staging.constants import (
    DEFAULT_NODE_POPULATION_NAME,
    DEFAULT_NODE_SET_NAME,
)
from entitysdk.types import MorphologyFormat
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import write_json

L = logging.getLogger(__name__)

DEFAULT_CIRCUIT_CONFIG_FILENAME = "circuit_config.json"


def _extract_hoc_template_name(hoc_file: Path) -> str:
    """Extract the template name from a HOC file by parsing the 'begintemplate' statement.

    The SONATA model_template field requires the HOC template name (e.g. 'cADpyr_bin_4'),
    not the filename. Neurodamus uses this name to look up the template in the NEURON namespace.

    Skips lines that are inside comments (// single-line or /* */ block comments).

    Args:
        hoc_file: Path to the HOC file.

    Returns:
        The template name found in the HOC file.

    Raises:
        StagingError: If no 'begintemplate' statement is found in the HOC file.
    """
    content = hoc_file.read_text()

    # Remove block comments
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    # Remove line comments
    content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)

    match = re.search(r"\bbegintemplate\s+(\w+)", content)
    if match:
        return match.group(1)

    raise StagingError(f"Could not find 'begintemplate' statement in HOC file: {hoc_file}")


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

        mtype = memodel.mtypes[0].pref_label if memodel.mtypes else "GEN_mtype"
        etype = memodel.emodel.etypes[0].pref_label if memodel.emodel.etypes else "GEN_etype"

        if memodel.calibration_result is None:
            raise StagingError(f"MEModel {memodel.id} has no calibration result.")

        threshold_current = memodel.calibration_result.threshold_current
        holding_current = memodel.calibration_result.holding_current

        _generate_sonata_files_from_memodel(
            downloaded_memodel=downloaded_me_model,
            output_path=output_dir,
            mtype=mtype,
            etype=etype,
            threshold_current=threshold_current,
            holding_current=holding_current,
        )

    config_path = output_dir / DEFAULT_CIRCUIT_CONFIG_FILENAME

    L.info("Single-Cell %s staged at %s", memodel.id, config_path)

    return config_path


def _generate_sonata_files_from_memodel(
    downloaded_memodel: DownloadedMEModel,
    output_path: Path,
    mtype: str | None,
    etype: str | None,
    threshold_current: float,
    holding_current: float,
):
    """Generate SONATA single cell circuit structure from a downloaded MEModel folder.

    Args:
        downloaded_memodel (DownloadedMEModel): The downloaded MEModel object.
        output_path (str or Path): Path to the output 'sonata' folder.
        mtype (str | None): Cell mtype, if available.
        etype (str | None): Cell etype, if available.
        threshold_current (float): Threshold current.
        holding_current (float): Holding current.
    """
    output_path = Path(output_path)
    nodes_file = output_path / DEFAULT_NODE_POPULATION_NAME / "nodes.h5"
    node_sets_file = output_path / "node_sets.json"
    subdirs = {
        "hocs": output_path / "hocs",
        "mechanisms": output_path / "mechanisms",
        "morphologies": output_path / "morphologies",
    }
    for path in subdirs.values():
        create_dir(path)

    # Copy hoc file, renaming to match the template name inside it.
    # Neurodamus loads HOC files as: <biophysical_neuron_models_dir>/<model_template>.hoc
    # so the filename must match the begintemplate name.
    hoc_file = downloaded_memodel.hoc_path
    if not downloaded_memodel.hoc_path.exists():
        raise FileNotFoundError(f"No HOC file found {downloaded_memodel.hoc_path}")
    template_name = _extract_hoc_template_name(hoc_file)
    hoc_dst = subdirs["hocs"] / f"{template_name}.hoc"
    shutil.copy(hoc_file, hoc_dst)

    # Copy every staged morphology format. All formats share the same stem, so the node
    # property (which stores the stem, not an extension) is the same whichever we point at.
    if not downloaded_memodel.morphology_paths:
        raise FileNotFoundError("No morphology file found")
    morph_dsts = []
    for morph_src in downloaded_memodel.morphology_paths:
        if not morph_src.exists():
            raise FileNotFoundError(f"No morphology file found {morph_src}")
        morph_dst = subdirs["morphologies"] / morph_src.name
        shutil.copy(morph_src, morph_dst)
        morph_dsts.append(morph_dst)

    # Copy mechanisms
    for file in downloaded_memodel.mechanism_files:
        src_path = downloaded_memodel.mechanisms_dir / file
        if Path(src_path).exists():
            target = subdirs["mechanisms"] / file
            shutil.copy(src_path, target)

    create_nodes_file(
        hoc_file=hoc_dst,
        morph_file=morph_dsts[0],
        output_file=nodes_file,
        mtype=mtype,
        etype=etype,
        threshold_current=threshold_current,
        holding_current=holding_current,
        template_name=template_name,
    )

    morphology_dirs = {
        MorphologyFormat(morph_dst.suffix.removeprefix(".")): subdirs["morphologies"]
        for morph_dst in morph_dsts
    }
    output_file = output_path / DEFAULT_CIRCUIT_CONFIG_FILENAME
    create_circuit_config(
        output_file=output_file,
        nodes_file=nodes_file,
        node_sets_file=node_sets_file,
        morphology_dirs=morphology_dirs,
        hocs_dir=subdirs["hocs"],
    )
    create_node_sets_file(output_file=node_sets_file)

    L.debug(f"SONATA single cell circuit created at {output_path}")


def create_nodes_file(
    hoc_file: str | Path,
    morph_file: str | Path,
    output_file: Path,
    threshold_current: float,
    holding_current: float,
    template_name: str,
    *,
    mtype: str | None = None,
    etype: str | None = None,
):
    """Create a SONATA nodes.h5 file for a single cell population.

    Args:
        hoc_file (str | Path): Path to the hoc file.
        morph_file (str | Path): Path to the morphology file.
        output_file (Path): Output file path for nodes.h5.
        threshold_current (float): Threshold current value.
        holding_current (float): Holding current value.
        template_name (str): HOC template name (from begintemplate statement).
        mtype (str | None): Cell mtype, if available.
        etype (str | None): Cell etype, if available.
    """
    output_file = Path(output_file)  # ensure Path type
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_file, "w") as f:
        nodes = f.create_group("nodes")
        population = nodes.create_group(DEFAULT_NODE_POPULATION_NAME)
        population.create_dataset("node_type_id", (1,), dtype="int64")[0] = -1
        group_0 = population.create_group("0")

        # Add dynamics_params fields
        dynamics = group_0.create_group("dynamics_params")
        dynamics.create_dataset("holding_current", (1,), dtype="float32")[0] = holding_current
        dynamics.create_dataset("threshold_current", (1,), dtype="float32")[0] = threshold_current

        # Standard string properties
        group_0.create_dataset("model_template", (1,), dtype=h5py.string_dtype())[0] = (
            f"hoc:{template_name}"
        )
        group_0.create_dataset("model_type", (1,), dtype="int32")[0] = 0
        group_0.create_dataset("morph_class", (1,), dtype="int32")[0] = 0
        group_0.create_dataset("morphology", (1,), dtype=h5py.string_dtype())[0] = Path(
            morph_file
        ).stem
        if mtype is not None:
            group_0.create_dataset("mtype", (1,), dtype=h5py.string_dtype())[0] = mtype
        if etype is not None:
            group_0.create_dataset("etype", (1,), dtype=h5py.string_dtype())[0] = etype

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


# 'swc' has no entry here; it's declared via `morphologies_dir`, not `alternate_morphologies`.
_ALTERNATE_MORPHOLOGY_FORMAT_KEYS = {
    MorphologyFormat.asc: "neurolucida-asc",
    MorphologyFormat.h5: "h5v1",
}


def create_circuit_config(
    output_file: Path,
    *,
    nodes_file: Path,
    node_sets_file: Path,
    morphology_dirs: dict[MorphologyFormat, Path],
    hocs_dir: Path,
    node_population_name: str = DEFAULT_NODE_POPULATION_NAME,
):
    """Create a SONATA circuit_config.json for a single cell.

    Args:
        output_file: Circuit config file to write.
        nodes_file: Path to the SONATA nodes.h5 file.
        node_sets_file: Path to the SONATA node_sets.json file.
        morphology_dirs: Directory containing morphology files actually staged, keyed by their
            format. Each entry is declared under the matching config key, e.g. ``swc`` under
            ``morphologies_dir`` and ``asc``/``h5`` under ``alternate_morphologies``.
        hocs_dir: Directory containing HOC files.
        node_population_name: Name of the node population.
    """
    output_file = Path(output_file)
    base_dir = output_file.parent.resolve()
    nodes_path = Path(nodes_file).resolve().relative_to(base_dir).as_posix()
    node_sets_path = Path(node_sets_file).resolve().relative_to(base_dir).as_posix()
    hocs_path = Path(hocs_dir).resolve().relative_to(base_dir).as_posix()

    morphology_config: dict[str, str | dict[str, str]] = {}
    alternate_morphologies: dict[str, str] = {}
    for morphology_format, morphology_dir in morphology_dirs.items():
        morphologies_path = Path(morphology_dir).resolve().relative_to(base_dir).as_posix()
        match morphology_format:
            case MorphologyFormat.swc:
                morphology_config["morphologies_dir"] = f"$BASE_DIR/{morphologies_path}"
            case MorphologyFormat.asc | MorphologyFormat.h5:
                alternate_key = _ALTERNATE_MORPHOLOGY_FORMAT_KEYS[morphology_format]
                alternate_morphologies[alternate_key] = f"$BASE_DIR/{morphologies_path}"
            case _:  # pragma: no cover
                msg = f"Unsupported morphology format: {morphology_format}"
                raise StagingError(msg)
    if alternate_morphologies:
        morphology_config["alternate_morphologies"] = alternate_morphologies

    config = {
        "manifest": {"$BASE_DIR": "."},
        "node_sets_file": f"$BASE_DIR/{node_sets_path}",
        "networks": {
            "nodes": [
                {
                    "nodes_file": f"$BASE_DIR/{nodes_path}",
                    "populations": {
                        node_population_name: {
                            "type": "biophysical",
                            "biophysical_neuron_models_dir": f"$BASE_DIR/{hocs_path}",
                            **morphology_config,
                        }
                    },
                }
            ],
            "edges": [],
        },
    }
    write_json(data=config, path=output_file, indent=2)
    L.debug(f"Successfully created circuit_config.json at {output_file}")


def create_node_sets_file(
    output_file: Path,
    node_population_name: str = DEFAULT_NODE_POPULATION_NAME,
    node_set_name: str = DEFAULT_NODE_SET_NAME,
    node_id: int = 0,
):
    """Create a node_sets.json file for a single cell.

    Args:
        output_file: Output file path for node_sets.json.
        node_population_name: Name of the node population.
        node_set_name: Name of the node set (default: MEMODEL_CIRCUIT_STAGING_NODE_SET_NAME).
        node_id: Node ID to include (default: 0).
    """
    node_sets = {node_set_name: {"population": node_population_name, "node_id": [node_id]}}
    write_json(node_sets, output_file)
    L.debug(f"Successfully created node_sets.json at {output_file}")
