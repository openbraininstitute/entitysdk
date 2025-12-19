"""Staging functions for Single-Cell."""
# See run_sonata_single_cell.py for running the output.

import logging
from pathlib import Path

from entitysdk import Client
from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.models.ion_channel_model import IonChannelModel
from entitysdk.utils.filesystem import create_dir
from entitysdk.staging.memodel import create_nodes_file, create_circuit_config, create_node_sets_file


L = logging.getLogger(__name__)

DEFAULT_CIRCUIT_CONFIG_FILENAME = "circuit_config.json"

HOC_TEMPLATE = """
{{load_file("stdrun.hoc")}}
{{load_file("import3d.hoc")}}

begintemplate single_comp_cell
  public init, morphology, getCell, getCCell, setCCell, gid
  public channel_seed, channel_seed_set
  public clear
  public soma
  create soma[1]
  public CellRef
  objref this, CellRef

  public all, somatic
  objref all, somatic


obfunc getCell(){{
        return this
}}

obfunc getCCell(){{
	return CellRef
}}
proc setCCell(){{
       CellRef = $o1
}}

//-----------------------------------------------------------------------------------------------

/*!
 * When clearing the model, the circular reference between Cells and CCells must be broken so the
 * entity watching reference counts can work.
 */
proc clear() {{ localobj nil
    CellRef = nil
}}


proc init(/* args: morphology_dir, morphology_name */) {{
  all = new SectionList()
  somatic = new SectionList()

  //For compatibility with BBP CCells
  CellRef = this

  forall delete_section()

  gid = $1

  if(numarg() >= 3) {{
    load_morphology($s2, $s3)
  }} else {{
    load_morphology($s2, "soma.asc")
  }}

  indexSections()
  insertChannel()
  biophys()

  // Initialize channel_seed_set to avoid accidents
  channel_seed_set = 0
  // Initialize random number generators
  re_init_rng()
}}

/*!
 * Assign section indices to the section voltage value.  This will be useful later for serializing
 * the sections into an array.  Note, that once the simulation begins, the voltage values will revert to actual data again.
 *
 * @param $o1 Import3d_GUI object
 */
proc indexSections() {{ local index
    access soma {{
        v(0.0001) = 0
    }}
}}

proc load_morphology(/* morphology_dir, morphology_name */) {{localobj morph, import, sf, extension, commands, pyobj
  strdef morph_path
  sprint(morph_path, "%s/%s", $s1, $s2)
  sf = new StringFunctions()
  extension = new String()
  sscanf(morph_path, "%s", extension.s)

  morph = new Import3d_Neurolucida3()
  morph.quiet = 1
  morph.input(morph_path)

  import = new Import3d_GUI(morph, 0)
  import.instantiate(this)
}}

proc insertChannel() {{
  forsec this.somatic {{
    {insert_channel}
  }}
}}

proc biophys() {{
  forsec CellRef.somatic {{
    {biophys}
  }}
}}

proc re_init_rng() {{localobj sf
    strdef full_str, name

    sf = new StringFunctions()

    if(numarg() == 1) {{
        // We received a third seed
        channel_seed = $1
        channel_seed_set = 1
    }} else {{
        channel_seed_set = 0
    }}
}}

endtemplate single_comp_cell
"""

# -- staging / creating sonata file functions -- #
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


def create_hoc_file(client, ion_channel_model_data, subdir_mech, subdir_hoc) -> Path:
    """Create a hoc file for a single compartment cell with specified ion channel models.
    
    Args:
        client (Client): Entity SDK client.
        ion_channel_model_data (dict): Dictionary with ion channel model IDs
            and conductance values.
        subdir_mech (Path): Path to the mechanisms directory.
        subdir_hoc (Path): Path to the hoc directory.
    """
    bpo_mechs = []
    bpo_parameters = {}
    for icm_dict in ion_channel_model_data.values():
        # download mod files
        icm_entity = client.get_entity(entity_type=IonChannelModel, entity_id=icm_dict["id"])
        download_ion_channel_mechanism(client, icm_entity, subdir_mech)

        # get data for hoc file
        bpo_mechs.append(icm_entity.nmodl_suffix)
        if "conductance" in icm_dict:
            conductance_name = find_conductance_name(icm_entity)
            bpo_parameters[conductance_name] = icm_dict["conductance"]

    # write hoc file
    hoc_dst = subdir_hoc / "cell.hoc"
    with open(hoc_dst, "w") as hoc_file:
        hoc_file.write(HOC_TEMPLATE.format(
            insert_channel="\n    ".join([f"insert {mech}" for mech in bpo_mechs]),
            biophys="\n    ".join(
                [
                    f"{param} = {value}"
                    for param, value in bpo_parameters.items()
                ]
            ),
        ))

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
