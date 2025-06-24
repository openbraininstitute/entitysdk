from pathlib import Path

import pytest

from entitysdk.exception import StagingError
from entitysdk.staging import simulation as test_module
from entitysdk.utils.io import load_json


def test_stage_simulation(
    client,
    tmp_path,
    simulation,
    simulation_config,
    circuit_httpx_mocks,
    simulation_httpx_mocks,
):
    res = test_module.stage_simulation(
        client,
        model=simulation,
        output_dir=tmp_path,
        override_results_dir="foo/bar",
    )

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"
    expected_spikes_1 = tmp_path / "PoissonInputStimulus_spikes_1.h5"
    expected_spikes_2 = tmp_path / "PoissonInputStimulus_spikes_2.h5"
    expected_circuit_config_path = tmp_path / "circuit" / "circuit_config.json"
    expected_circuit_nodes_path = tmp_path / "circuit" / "nodes.h5"
    expected_circuit_edges_path = tmp_path / "circuit" / "edges.h5"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
    assert expected_spikes_1.exists()
    assert expected_spikes_2.exists()
    assert expected_circuit_config_path.exists()
    assert expected_circuit_nodes_path.exists()
    assert expected_circuit_edges_path.exists()

    res = load_json(expected_simulation_config_path)
    assert res["network"] == str(expected_circuit_config_path)
    assert res["node_sets_file"] == Path(expected_node_sets_path).name

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
        circuit_config_path=circuit_config_path,
    )

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"
    expected_spikes_1 = tmp_path / "PoissonInputStimulus_spikes_1.h5"
    expected_spikes_2 = tmp_path / "PoissonInputStimulus_spikes_2.h5"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
    assert expected_spikes_1.exists()
    assert expected_spikes_2.exists()

    res = load_json(expected_simulation_config_path)
    assert res["network"] == circuit_config_path
    assert res["node_sets_file"] == Path(expected_node_sets_path).name

    assert res["reports"] == simulation_config["reports"]
    assert res["conditions"] == simulation_config["conditions"]

    assert len(res["inputs"]) == len(simulation_config["inputs"])
    assert res["inputs"]["PoissonInputStimulus"]["spike_file"] == expected_spikes_1.name
    assert res["inputs"]["PoissonInputStimulus_2"]["spike_file"] == expected_spikes_2.name


def test_transform_inputs__raises():
    inputs = {"foo": {"input_type": "spikes", "spike_file": "foo.txt"}}

    with pytest.raises(StagingError, match="not present in spike asset file names"):
        test_module._transform_inputs(inputs, {})
