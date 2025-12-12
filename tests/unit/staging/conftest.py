import json
import uuid
from pathlib import Path

import pytest

from entitysdk import types
from entitysdk.models import (
    Asset,
    CellMorphology,
    Circuit,
    EModel,
    ETypeClass,
    MEModel,
    MEModelCalibrationResult,
    MTypeClass,
    Simulation,
    SimulationResult,
    Species,
    Subject,
)
from entitysdk.models.brain_region import BrainRegion

DATA_DIR = Path(__file__).parent / "data"


def _download_url(api_url, route, entity_id, asset_id):
    return f"{api_url}/{route}/{entity_id}/assets/{asset_id}/download"


@pytest.fixture
def species():
    return Species(
        name="fake-species",
        taxonomy_id="foo",
    )


@pytest.fixture
def subject(species):
    return Subject(
        sex=types.Sex.male,
        species=species,
    )


@pytest.fixture
def brain_region():
    return BrainRegion(
        name="my-region",
        annotation_value=1,
        acronym="region",
        hierarchy_id=uuid.uuid4(),
        color_hex_triplet="foo",
        parent_structure_id=None,
    )


@pytest.fixture
def mtype():
    return MTypeClass(
        pref_label="L5_TPC",
        definition="L5 tufted pyramidal cell",
    )


@pytest.fixture
def etype():
    return ETypeClass(pref_label="foo", definition="Foo etype.")


@pytest.fixture
def circuit(subject, brain_region):
    return Circuit(
        id=uuid.uuid4(),
        subject=subject,
        number_neurons=5,
        number_synapses=10,
        number_connections=None,
        scale="microcircuit",
        build_category="em_reconstruction",
        brain_region=brain_region,
        assets=[
            Asset(
                id=uuid.uuid4(),
                content_type="application/vnd.directory",
                label="sonata_circuit",
                size=0,
                path="circuit",
                full_path="/circuit",
                is_directory=True,
                storage_type=types.StorageType.aws_s3_internal,
            )
        ],
    )


@pytest.fixture
def circuit_files():
    circuit_dir = DATA_DIR / "circuit"
    return {
        str(path.relative_to(circuit_dir)): path
        for path in Path(circuit_dir).rglob("*")
        if path.is_file()
    }


@pytest.fixture
def circuit_httpx_mocks(api_url, circuit, httpx_mock, circuit_files):
    """Mocks required to stage a Circuit directory."""
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/circuit/{circuit.id}",
        json=circuit.model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/circuit/{circuit.id}/assets/{circuit.assets[0].id}/list",
        json={
            "files": {
                asset_path: {
                    "name": Path(asset_path).name,
                    "size": 0,
                    "last_modified": "2025-01-01T00:00:00Z",
                }
                for asset_path in circuit_files
            }
        },
    )
    for asset_path in circuit_files:
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/circuit/{circuit.id}/assets/{circuit.assets[0].id}/download?asset_path={asset_path}",
            content=circuit_files[asset_path].read_bytes(),
        )


@pytest.fixture
def simulation_config():
    return json.loads(Path(DATA_DIR / "simulation_config.json").read_bytes())


@pytest.fixture
def node_sets():
    return json.loads(Path(DATA_DIR / "node_sets.json").read_bytes())


@pytest.fixture
def spike_replays():
    return Path(DATA_DIR, "spike_replays.h5").read_bytes()


@pytest.fixture
def simulation(circuit):
    return Simulation(
        id=uuid.uuid4(),
        name="my-simulation",
        description="my-description",
        entity_id=circuit.id,
        simulation_campaign_id=uuid.uuid4(),
        scan_parameters={},
        assets=[
            Asset(
                id=uuid.uuid4(),
                content_type="application/json",
                label="sonata_simulation_config",
                path="foo.json",
                full_path="/foo.json",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/json",
                label="custom_node_sets",
                path="bar.json",
                full_path="/bar.json",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="replay_spikes",
                path="PoissonInputStimulus_spikes_1.h5",
                full_path="/PoissonInputStimulus_spikes_1.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="replay_spikes",
                path="PoissonInputStimulus_spikes_2.h5",
                full_path="/PoissonInputStimulus_spikes_2.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
        ],
    )


@pytest.fixture
def simulation_httpx_mocks(
    httpx_mock, simulation, node_sets, api_url, simulation_config, spike_replays
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation.id}/assets/{simulation.assets[0].id}/download",
        json=simulation_config,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation.id}/assets/{simulation.assets[1].id}/download",
        json=node_sets,
        is_optional=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation.id}/assets/{simulation.assets[2].id}/download",
        content=spike_replays,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation.id}/assets/{simulation.assets[3].id}/download",
        content=spike_replays,
    )


@pytest.fixture
def voltage_report_1():
    return Path(DATA_DIR, "SomaVoltRec 1.h5").read_bytes()


@pytest.fixture
def voltage_report_2():
    return Path(DATA_DIR, "SomaVoltRec 2.h5").read_bytes()


@pytest.fixture
def spike_report():
    return Path(DATA_DIR, "spikes.h5").read_bytes()


@pytest.fixture
def simulation_result(simulation):
    return SimulationResult(
        id=uuid.uuid4(),
        name="my-sim-result",
        description="my-sim-result-description",
        simulation_id=simulation.id,
        assets=[
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="voltage_report",
                path="SomaVoltRec 1.h5",
                full_path="/soma_voltage1.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="voltage_report",
                path="SomaVoltRec 2.h5",
                full_path="/soma_voltage2.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="spike_report",
                path="out.h5",
                full_path="/out.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
        ],
    )


@pytest.fixture
def simulation_result_httpx_mocks(
    api_url,
    simulation_result,
    voltage_report_1,
    voltage_report_2,
    spike_report,
    httpx_mock,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation-result/{simulation_result.id}/assets/{simulation_result.assets[0].id}/download",
        content=voltage_report_1,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation-result/{simulation_result.id}/assets/{simulation_result.assets[1].id}/download",
        content=voltage_report_2,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation-result/{simulation_result.id}/assets/{simulation_result.assets[2].id}/download",
        content=spike_report,
    )


@pytest.fixture
def cell_morphology(brain_region, subject, mtype):
    return CellMorphology(
        name="cell-morphology",
        description="cell-morphology-description",
        brain_region=brain_region,
        subject=subject,
        mtypes=[mtype],
        assets=[
            Asset(
                id=uuid.uuid4(),
                content_type="application/swc",
                label="morphology",
                path="morph.swc",
                full_path="/morph.swc",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/asc",
                label="morphology",
                path="morph.asc",
                full_path="/morph.asc",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="morphology",
                path="morph.h5",
                full_path="/morph.h5",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
        ],
    )


@pytest.fixture
def cell_morphology_httpx_mocks(
    api_url,
    httpx_mock,
    cell_morphology,
):
    route = "cell-morphology"
    entity_id = cell_morphology.id
    assets = cell_morphology.assets

    httpx_mock.add_response(
        method="GET",
        url=_download_url(api_url, route, entity_id, assets[0].id),
        content=Path(DATA_DIR, "morph.swc").read_bytes(),
    )
    httpx_mock.add_response(
        method="GET",
        url=_download_url(api_url, route, entity_id, assets[1].id),
        content=Path(DATA_DIR, "morph.asc").read_bytes(),
    )
    httpx_mock.add_response(
        method="GET",
        url=_download_url(api_url, route, entity_id, assets[2].id),
        content=Path(DATA_DIR, "morph.h5").read_bytes(),
    )


@pytest.fixture
def emodel(brain_region, etype, species):
    return EModel(
        id=uuid.uuid4(),
        name="emodel",
        description="emodel-description",
        species=species,
        brain_region=brain_region,
        iteration="1",
        score=100,
        seed=0,
        etypes=[etype],
        assets=[
            Asset(
                id=uuid.uuid4(),
                size=0,
                content_type="application/json",
                label="emodel_optimization_output",
                path="emodel_optimization_output.json",
                full_path="/emodel_optimization_output.json",
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
            Asset(
                id=uuid.uuid4(),
                size=0,
                content_type="application/hoc",
                label="neuron_hoc",
                path="neuron_hoc.hoc",
                full_path="/neuron_hoc.hoc",
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            ),
        ],
    )


@pytest.fixture
def emodel_httpx_mocks(
    api_url,
    emodel,
    httpx_mock,
):
    route = "emodel"
    entity_id = emodel.id
    assets = emodel.assets

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel.id}",
        json=emodel.model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=_download_url(api_url, route, entity_id, assets[0].id),
        content=Path(DATA_DIR, "emodel_optimization_output.json").read_bytes(),
        is_optional=True,
    )
    httpx_mock.add_response(
        method="GET",
        url=_download_url(api_url, route, entity_id, assets[1].id),
        content=Path(DATA_DIR, "neuron_hoc.hoc").read_bytes(),
        is_optional=True,
    )


@pytest.fixture
def memodel(brain_region, mtype, species, cell_morphology, emodel):
    memodel_id = uuid.uuid4()
    calibration_result = MEModelCalibrationResult(
        holding_current=-0.016,
        threshold_current=0.1,
        rin=0.1,
        calibrated_entity_id=memodel_id,
    )
    return MEModel(
        id=memodel_id,
        name="my-memodel",
        description="my-memodel-description",
        validation_status="done",
        species=species,
        morphology=cell_morphology,
        emodel=emodel,
        brain_region=brain_region,
        calibration_result=calibration_result,
        mtypes=[mtype],
    )
