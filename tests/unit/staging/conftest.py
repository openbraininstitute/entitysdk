import json
import uuid
from pathlib import Path

import pytest

from entitysdk.models import Asset, Simulation, SimulationResult

DATA_DIR = Path(__file__).parent / "data"


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
def simulation():
    return Simulation(
        id=uuid.uuid4(),
        name="my-simulation",
        description="my-description",
        entity_id=uuid.uuid4(),
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
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/json",
                label="custom_node_sets",
                path="bar.json",
                full_path="/bar.json",
                size=0,
                is_directory=False,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="spike_replays",
                path="PoissonInputStimulus_spikes_1.h5",
                full_path="/PoissonInputStimulus_spikes_1.h5",
                size=0,
                is_directory=False,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="spike_replays",
                path="PoissonInputStimulus_spikes_2.h5",
                full_path="/PoissonInputStimulus_spikes_2.h5",
                size=0,
                is_directory=False,
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
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="voltage_report",
                path="SomaVoltRec 2.h5",
                full_path="/soma_voltage2.h5",
                size=0,
                is_directory=False,
            ),
            Asset(
                id=uuid.uuid4(),
                content_type="application/x-hdf5",
                label="spike_report",
                path="out.h5",
                full_path="/out.h5",
                size=0,
                is_directory=False,
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
