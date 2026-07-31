import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

from entitysdk.exception import StagingError
from entitysdk.models import Asset, SimulatableExtracellularRecordingArray
from entitysdk.staging import simulation as test_module
from entitysdk.types import StorageType
from entitysdk.utils.io import load_json


def test_stage_simulation(
    client,
    tmp_path,
    simulation,
    simulation_config,
    circuit_httpx_mocks,
    simulation_httpx_mocks,
    httpx_mock,
    api_url,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{simulation.entity_id}",
        json={"id": str(simulation.entity_id), "type": "circuit"},
    )
    res = test_module.stage_simulation(
        client,
        model=simulation,
        output_dir=tmp_path,
        override_results_dir=Path("foo/bar"),
    )

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"
    expected_compartment_sets_path = tmp_path / "compartment_sets.json"
    expected_spikes_1 = tmp_path / "PoissonInputStimulus_spikes_1.h5"
    expected_spikes_2 = tmp_path / "PoissonInputStimulus_spikes_2.h5"
    expected_circuit_config_path = tmp_path / "circuit" / "circuit_config.json"
    expected_circuit_nodes_path = tmp_path / "circuit" / "nodes.h5"
    expected_circuit_edges_path = tmp_path / "circuit" / "edges.h5"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
    assert expected_compartment_sets_path.exists()
    assert expected_spikes_1.exists()
    assert expected_spikes_2.exists()
    assert expected_circuit_config_path.exists()
    assert expected_circuit_nodes_path.exists()
    assert expected_circuit_edges_path.exists()

    res = load_json(expected_simulation_config_path)
    assert res["network"] == str(expected_circuit_config_path)
    assert res["node_sets_file"] == Path(expected_node_sets_path).name
    assert res["compartment_sets_file"] == Path(expected_compartment_sets_path).name

    assert res["reports"] == simulation_config["reports"]
    assert res["conditions"] == simulation_config["conditions"]

    assert len(res["inputs"]) == len(simulation_config["inputs"])
    assert res["inputs"]["PoissonInputStimulus"]["spike_file"] == expected_spikes_1.name
    assert res["inputs"]["PoissonInputStimulus_2"]["spike_file"] == expected_spikes_2.name

    assert res["output"]["output_dir"] == "foo/bar"
    assert res["output"]["spikes_file"] == "foo/bar/spikes.h5"


def test_stage_simulation__external_circuit_config(
    client,
    tmp_path,
    simulation,
    simulation_config,
    simulation_httpx_mocks,
):
    circuit_config_path = "my-external-path"

    res = test_module.stage_simulation(
        client,
        model=simulation,
        output_dir=tmp_path,
        circuit_config_path=Path(circuit_config_path),
    )

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"
    expected_compartment_sets_path = tmp_path / "compartment_sets.json"
    expected_spikes_1 = tmp_path / "PoissonInputStimulus_spikes_1.h5"
    expected_spikes_2 = tmp_path / "PoissonInputStimulus_spikes_2.h5"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
    assert expected_compartment_sets_path.exists()
    assert expected_spikes_1.exists()
    assert expected_spikes_2.exists()

    res = load_json(expected_simulation_config_path)
    assert res["network"] == circuit_config_path
    assert res["node_sets_file"] == Path(expected_node_sets_path).name
    assert res["compartment_sets_file"] == Path(expected_compartment_sets_path).name

    assert res["reports"] == simulation_config["reports"]
    assert res["conditions"] == simulation_config["conditions"]

    assert len(res["inputs"]) == len(simulation_config["inputs"])
    assert res["inputs"]["PoissonInputStimulus"]["spike_file"] == expected_spikes_1.name
    assert res["inputs"]["PoissonInputStimulus_2"]["spike_file"] == expected_spikes_2.name


def test_stage_simulation__without_compartment_sets_file(
    client,
    tmp_path,
    simulation,
    monkeypatch,
):
    monkeypatch.setattr(
        test_module,
        "download_simulation_config_content",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(test_module, "download_spike_replay_files", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(test_module, "download_node_sets_file", lambda *_args, **_kwargs: None)
    fetch_compartment_sets_file = Mock()
    monkeypatch.setattr(test_module, "fetch_compartment_sets_file", fetch_compartment_sets_file)

    test_module.stage_simulation(
        client,
        model=simulation,
        output_dir=tmp_path,
        circuit_config_path=Path("my-external-path"),
    )

    fetch_compartment_sets_file.assert_not_called()


def test_transform_inputs__raises():
    inputs = {"foo": {"input_type": "spikes", "module": "synapse_replay", "spike_file": "foo.txt"}}

    with pytest.raises(StagingError, match="not present in spike asset file names"):
        test_module._transform_inputs(inputs, [])


def test_stage_simulation__wrong_entity_Type(
    client,
    tmp_path,
    simulation,
    simulation_config,
    simulation_httpx_mocks,
    httpx_mock,
    api_url,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{simulation.entity_id}",
        json={"id": str(simulation.entity_id), "type": "cell_morphology"},
    )

    with pytest.raises(StagingError, match="references unsupported type cell_morphology"):
        test_module.stage_simulation(
            client,
            model=simulation,
            output_dir=tmp_path,
        )


def test__transform_simulation_config():
    circuit_config_path = Path("path/to/circuit_config.json")

    res = test_module._transform_simulation_config(
        simulation_config={},
        circuit_config_path=circuit_config_path,
        node_sets_path=None,
        compartment_sets_path=None,
        spike_paths=[],
        output_dir=Path(),
        override_results_dir=None,
    )
    assert res == {"network": "path/to/circuit_config.json", "output": {}, "inputs": {}}

    with pytest.raises(StagingError, match="Simulation has spikes, but no `inputs` defined"):
        test_module._transform_simulation_config(
            simulation_config={},
            circuit_config_path=circuit_config_path,
            node_sets_path=None,
            compartment_sets_path=None,
            spike_paths=[
                Path(),
            ],
            output_dir=Path(),
            override_results_dir=None,
        )


def _recording_array(array_id, asset_id):
    return SimulatableExtracellularRecordingArray(
        id=array_id,
        name="array",
        description="array",
        electrode_type="custom",
        circuit_id=uuid.uuid4(),
        assets=[
            Asset(
                id=asset_id,
                content_type="application/x-hdf5",
                label="electrode_locations",
                path="electrodes.h5",
                full_path="/electrodes.h5",
                size=0,
                is_directory=False,
                storage_type=StorageType.aws_s3_internal,
                status="created",
            )
        ],
    )


def test_stage_recording_arrays(client, tmp_path, httpx_mock, api_url):
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    asset1 = uuid.uuid4()
    asset2 = uuid.uuid4()
    arrays = [_recording_array(id1, asset1), _recording_array(id2, asset2)]

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulatable-extracellular-recording-array/{id1}",
        json=arrays[0].model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulatable-extracellular-recording-array/{id2}",
        json=arrays[1].model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulatable-extracellular-recording-array/{id1}/assets/{asset1}",
        json=arrays[0].assets[0].model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulatable-extracellular-recording-array/{id2}/assets/{asset2}",
        json=arrays[1].assets[0].model_dump(mode="json"),
    )
    httpx_mock.add_response(
        method="GET",
        url=(f"{api_url}/simulatable-extracellular-recording-array/{id1}/assets/{asset1}/download"),
        content=b"array-1",
    )
    httpx_mock.add_response(
        method="GET",
        url=(f"{api_url}/simulatable-extracellular-recording-array/{id2}/assets/{asset2}/download"),
        content=b"array-2",
    )

    reports = {
        "lfp_report_A": {
            "type": "lfp",
            "electrodes_file": f"electrodes_files/{id1}.h5",
        },
        "lfp_report_B": {
            "type": "lfp",
            "electrodes_file": f"wrong/path/{id2}.h5",
        },
        "SomaVoltRec": {"type": "compartment", "cells": "All"},
    }

    res = test_module._stage_recording_arrays(
        client,
        reports=reports,
        recording_arrays=arrays,
        output_dir=tmp_path,
    )

    path1 = tmp_path / "electrodes_files" / f"{id1}.h5"
    path2 = tmp_path / "electrodes_files" / f"{id2}.h5"
    assert path1.read_bytes() == b"array-1"
    assert path2.read_bytes() == b"array-2"
    assert res["lfp_report_A"]["electrodes_file"] == f"electrodes_files/{id1}.h5"
    assert res["lfp_report_B"]["electrodes_file"] == f"electrodes_files/{id2}.h5"
    assert res["SomaVoltRec"] == reports["SomaVoltRec"]


def test_stage_recording_arrays__empty_arrays_with_config_entries(client, tmp_path):
    reports = {"lfp": {"type": "lfp", "electrodes_file": f"electrodes_files/{uuid.uuid4()}.h5"}}
    with pytest.raises(StagingError, match="recording_arrays is empty"):
        test_module._stage_recording_arrays(
            client,
            reports=reports,
            recording_arrays=[],
            output_dir=tmp_path,
        )


def test_stage_recording_arrays__arrays_without_config_entries(client, tmp_path):
    array = _recording_array(uuid.uuid4(), uuid.uuid4())
    with pytest.raises(StagingError, match="no electrodes_file entries"):
        test_module._stage_recording_arrays(
            client,
            reports={"SomaVoltRec": {"type": "compartment"}},
            recording_arrays=[array],
            output_dir=tmp_path,
        )


def test_stage_recording_arrays__missing_config_id(client, tmp_path):
    array = _recording_array(uuid.uuid4(), uuid.uuid4())
    missing_id = uuid.uuid4()
    reports = {"lfp": {"type": "lfp", "electrodes_file": f"electrodes_files/{missing_id}.h5"}}
    with pytest.raises(StagingError, match="not present in recording_arrays"):
        test_module._stage_recording_arrays(
            client,
            reports=reports,
            recording_arrays=[array],
            output_dir=tmp_path,
        )
