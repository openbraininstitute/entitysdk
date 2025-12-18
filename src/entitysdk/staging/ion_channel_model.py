"""Staging functions for Ion Channel Models."""

import logging
from pathlib import Path

from bluepyemodel.export_emodel.export_emodel import _write_hoc_file
import bluepyopt.ephys as ephys

from entitysdk import Client
from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.models.ion_channel_model import IonChannelModel
from entitysdk.staging.memodel import create_nodes_file, create_circuit_config, create_node_sets_file
from entitysdk.utils.filesystem import create_dir


L = logging.getLogger(__name__)

DEFAULT_CIRCUIT_CONFIG_FILENAME = "circuit_config.json"


def create_simple_soma_morphology(output_file: Path, radius: float = 10.0):
    """Create a simple soma morphology file in ASC format.

    Args:
        output_file (Path): Path to the output morphology file.
        radius (float): Radius of the soma in microns.
    """

    lines = [
        "(\"CellBody\"\n",
        "  (Color Red)\n",
        "  (CellBody)\n",
        f"  ( {-radius} {-radius} 0 {radius} )\n",
        f"  ( { radius} {-radius} 0 {radius} )\n",
        f"  ( { radius} { radius} 0 {radius} )\n",
        f"  ( {-radius} { radius} 0 {radius} )\n",
        ")\n",
    ]

    with open(output_file, "w") as f:
        f.writelines(lines)


def find_conductance_name(entity):
    """Find the conductance parameter name in an IonChannelModel entity.
    
    Args:
        entity (IonChannelModel): The ion channel model entity.
    """
    conductance_keywords = ("bar", "gmax", "_max", "max", "gKur")
    
    for param in entity.neuron_block.range:
        for key in param:
            if any(keyword in key for keyword in conductance_keywords):
                return key
    return None


def create_hoc_file(client, ion_channel_model_data, morph_dst, subdir_mech, subdir_hoc) -> Path:
    """Create a hoc file for a single compartment cell with specified ion channel models.
    
    Args:
        client (Client): Entity SDK client.
        ion_channel_model_data (dict): Dictionary with ion channel model IDs
            and conductance values.
        morph_dst (Path): Path to the morphology file.
        subdir_mech (Path): Path to the mechanisms directory.
        subdir_hoc (Path): Path to the hoc directory.
    """
    morph = ephys.morphologies.NrnFileMorphology(morph_dst)
    somatic_loc = ephys.locations.NrnSeclistLocation('somatic', seclist_name='somatic')

    # Copy mechanisms
    icm_paths = []
    bpo_mechs = []
    bpo_parameters = []
    for icm_dict in ion_channel_model_data.values():
        # download mod files
        icm_entity = client.get_entity(entity_type=IonChannelModel, entity_id=icm_dict["id"])
        mod_path = download_ion_channel_mechanism(client, icm_entity, subdir_mech)
        icm_paths.append(mod_path)

        # create bpo mechanisms
        bpo_mech = ephys.mechanisms.NrnMODMechanism(
            name=icm_entity.name,
            mod_path=mod_path,
            suffix=icm_entity.nmodl_suffix,
            locations=[somatic_loc],
        )
        bpo_mechs.append(bpo_mech)

        if "conductance" in icm_dict:
            conductance_name = find_conductance_name(icm_entity)
            # create parameters with conductance set
            param = ephys.parameters.NrnSectionParameter(
                name=conductance_name,
                param_name=conductance_name,
                value=icm_dict["conductance"],
                locations=[somatic_loc],
                frozen=True,
            )
            bpo_parameters.append(param)

    # Create hoc file
    # create bpo cell model, then use bpem's _write_hoc_file.
    class EmptyEModel:
        parameters={}

    empty_emodel = EmptyEModel()
    cell = ephys.models.CellModel(
        name='single_comp_cell',
        morph=morph,
        mechs=bpo_mechs,
        params=bpo_parameters,
    )
    hoc_dst = subdir_hoc / "cell.hoc"
    _write_hoc_file(
        cell,
        empty_emodel,
        hoc_dst,
    )

    return hoc_dst


def stage_sonata_from_config(
    client: Client,
    ion_channel_model_data: dict,
    output_dir: Path,
    radius: float = 10.0,
    mtype: str = "",
    threshold_current: float = 0.0,
    holding_current: float = 0.0,
):
    """Generate SONATA single cell circuit structure from a IonChannelModelSimulationConfig.

    Args:
        client (Client): Entity SDK client.
        ion_channel_model_data (dict): Dictionary with ion channel model IDs
            and conductance values.
        output_dir (str or Path): Path to the output 'sonata' folder.
        radius (float): Radius of the soma in microns.
        mtype (str): Cell mtype.
        threshold_current (float): Threshold current.
        holding_current (float): Holding current.
    """
    subdirs = {
        "hocs": output_dir / "hocs",
        "mechanisms": output_dir / "mechanisms",
        "morphologies": output_dir / "morphologies",
        "network": output_dir / "network",
    }
    for path in subdirs.values():
        create_dir(path)

    # Create morphology file
    morph_dst = subdirs["morphologies"] / "soma.asc"
    create_simple_soma_morphology(output_file=morph_dst, radius=radius)

    # create BPO cell model
    hoc_dst = create_hoc_file(
        client,
        ion_channel_model_data,
        morph_dst,
        subdirs["mechanisms"],
        subdirs["hocs"],
    )

    create_nodes_file(
        hoc_file=str(hoc_dst),
        morph_file=str(morph_dst),
        output_file=Path(str(subdirs["network"])) / "nodes.h5",
        mtype=mtype,
        threshold_current=threshold_current,
        holding_current=holding_current,
    )

    create_circuit_config(output_path=output_dir)
    create_node_sets_file(output_file=output_dir / "node_sets.json")

    L.debug(f"SONATA single cell circuit created at {output_dir}")

    config_path = output_dir / DEFAULT_CIRCUIT_CONFIG_FILENAME

    L.info("Circuit for ion channel model simulation staged at %s", config_path)

    return config_path
