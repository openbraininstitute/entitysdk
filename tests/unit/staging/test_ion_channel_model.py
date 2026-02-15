import uuid

import entitysdk.staging.ion_channel_model as icm
from entitysdk import models, types
from entitysdk.models.ion_channel_model import IonChannelModel, NeuronBlock
from entitysdk.types import AssetLabel, ContentType


class DummyNeuronBlock:
    def __init__(self, range_params):
        self.range = range_params


class DummyIonChannelModelEntity:
    def __init__(self, range_params):
        self.neuron_block = DummyNeuronBlock(range_params)


def _mock_ic_asset_response(asset_id, name):
    """Mock response for ion channel model asset."""
    return {
        "id": str(asset_id),
        "path": "{name}.mod",
        "full_path": "{name}.mod",
        "is_directory": False,
        "label": AssetLabel.neuron_mechanisms,
        "content_type": ContentType.application_mod,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
        "storage_type": "aws_s3_internal",
    }


def create_http_ic_mock(ic_id, name, httpx_mock, api_url, request_headers, with_conductance=True):
    calvast_asset_id = uuid.uuid4()
    hierarchy_id = uuid.uuid4()

    ic_model = IonChannelModel(
        id=ic_id,
        name=name,
        nmodl_suffix=name,
        description=f"{name} description",
        subject=models.Subject(
            sex=types.Sex.male,
            species={"name": "foo", "taxonomy_id": "bar"},
        ),
        brain_region={
            "name": "foo",
            "annotation_value": 997,
            "acronym": "bar",
            "parent_structure_id": None,
            "hierarchy_id": str(hierarchy_id),
            "color_hex_triplet": "#FFFFFF",
        },
        is_temperature_dependent=False,
        temperature_celsius=34,
        neuron_block=NeuronBlock(range=[{f"g{name}bar": "S/cm2"}])
        if with_conductance
        else NeuronBlock(),
        assets=[_mock_ic_asset_response(calvast_asset_id, name)],
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{ic_id}",
        match_headers=request_headers,
        json=ic_model.model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{ic_id}/assets/{calvast_asset_id}",
        match_headers=request_headers,
        json=_mock_ic_asset_response(calvast_asset_id, name) | {"path": f"{name}.mod"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{ic_id}/assets/{calvast_asset_id}/download",
        match_headers=request_headers,
        content=name,
    )


def test_create_simple_soma_morphology(tmp_path):
    (tmp_path / "morphologies").mkdir(parents=True, exist_ok=True)
    output_path = tmp_path / "morphologies" / "soma.asc"
    radius = 20.0
    icm.create_simple_soma_morphology(
        output_file=output_path,
        radius=radius,
    )
    assert (output_path).exists()

    # try reading the output morphology with NEURON
    from neuron import h

    h.load_file("import3d.hoc")

    # Read ASC morphology
    imp = h.Import3d_Neurolucida3()
    imp.input(str(output_path))

    # Instantiate as a cell-like object so sections stay alive
    class Cell:
        pass

    cell = Cell()
    i3d = h.Import3d_GUI(imp, 0)
    i3d.instantiate(cell)

    diameter = cell.soma[0].diam

    assert diameter == 2 * radius


def test_find_conductance_name():
    entity1 = DummyIonChannelModelEntity(
        [
            {"gIhbar": "S/cm2"},
            {"gIh": "S/cm2"},
            {"ihcn": "mA/cm2"},
            {"BBiD": None},
        ]
    )
    assert icm.find_conductance_name(entity1) == "gIhbar"

    entity2 = DummyIonChannelModelEntity([{"decay": "ms"}, {"gamma": None}])
    assert icm.find_conductance_name(entity2) is None

    entity3 = DummyIonChannelModelEntity(
        [{"e": None}, {"gmax": "S/cm2"}, {"gion": None}, {"il": None}]
    )
    assert icm.find_conductance_name(entity3) == "gmax"

    entity4 = DummyIonChannelModelEntity(
        [
            {"gKur": "S/cm2"},
            {"ik": "mA/cm2"},
            {"ino": None},
        ]
    )
    assert icm.find_conductance_name(entity4) == "gKur"

    entity5 = DummyIonChannelModelEntity([{"gh_max": "S/cm2"}, {"g_h": None}, {"i_rec": None}])
    assert icm.find_conductance_name(entity5) == "gh_max"


def test_create_hoc_file(client, tmp_path, httpx_mock, api_url, request_headers):
    ion_channel_model_data = {
        "Ca_LVAst": {
            "id": uuid.uuid4(),
            "conductance": 0.011,
        },
        # ion channel with no conductance case
        "CaDynamics_DC0": {
            "id": uuid.uuid4(),
        },
    }
    create_http_ic_mock(
        ion_channel_model_data["Ca_LVAst"]["id"], "Ca_LVAst", httpx_mock, api_url, request_headers
    )
    create_http_ic_mock(
        ion_channel_model_data["CaDynamics_DC0"]["id"],
        "CaDynamics_DC0",
        httpx_mock,
        api_url,
        request_headers,
        with_conductance=False,
    )

    (tmp_path / "hocs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "mechanisms").mkdir(parents=True, exist_ok=True)
    hoc_dst = icm.create_hoc_file(
        client=client,
        ion_channel_model_data=ion_channel_model_data,
        subdir_mech=tmp_path / "mechanisms",
        subdir_hoc=tmp_path / "hocs",
    )
    assert hoc_dst == tmp_path / "hocs" / "cell.hoc"
    assert (tmp_path / "hocs" / "cell.hoc").exists()
    assert (tmp_path / "mechanisms" / "Ca_LVAst.mod").exists()
    with open(tmp_path / "hocs" / "cell.hoc") as f:
        hoc_content = f.read()
        assert "gCa_LVAstbar = 0.011" in hoc_content
        assert "insert Ca_LVAst" in hoc_content
        assert "insert CaDynamics_DC0" in hoc_content


def test_stage_sonata_from_config(client, tmp_path, httpx_mock, api_url, request_headers):
    ion_channel_model_data = {
        "Ca_LVAst": {
            "id": uuid.uuid4(),
            "conductance": 0.011,
        },
    }
    create_http_ic_mock(
        ion_channel_model_data["Ca_LVAst"]["id"], "Ca_LVAst", httpx_mock, api_url, request_headers
    )

    config_path = icm.stage_sonata_from_config(
        client=client,
        ion_channel_model_data=ion_channel_model_data,
        output_dir=tmp_path,
    )

    assert config_path == tmp_path / "circuit_config.json"
    assert (tmp_path / "morphologies" / "soma.asc").exists()
    assert (tmp_path / "mechanisms" / "Ca_LVAst.mod").exists()
    assert (tmp_path / "hocs" / "cell.hoc").exists()
    assert (tmp_path / "network" / "nodes.h5").exists()
    assert (tmp_path / "circuit_config.json").exists()
    assert (tmp_path / "node_sets.json").exists()
