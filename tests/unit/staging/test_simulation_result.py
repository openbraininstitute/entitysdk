from pathlib import Path

from entitysdk.staging import simulation_result as test_module
from entitysdk.utils.io import load_json


def test_stage_simulation_result(
    api_url,
    client,
    tmp_path,
    simulation,
    simulation_config,
    simulation_result,
    circuit_httpx_mocks,
    simulation_httpx_mocks,
    simulation_result_httpx_mocks,
    httpx_mock,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation.id}",
        json=simulation.model_dump(mode="json"),
    )

    test_module.stage_simulation_result(
        client,
        model=simulation_result,
        output_dir=tmp_path,
    )
    expected_voltage_report_1 = tmp_path / "output" / "SomaVoltRec 1.h5"
    expected_voltage_report_2 = tmp_path / "output" / "SomaVoltRec 2.h5"
    expected_spike_report = tmp_path / "output" / "spikes.h5"

    assert expected_voltage_report_1.exists()
    assert expected_voltage_report_2.exists()
    assert expected_spike_report.exists()

    # simulation should also have been staged in the same directory because a simulation config
    # was not explicitly passed as an argument.
    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"
    expected_spikes_1 = tmp_path / "PoissonInputStimulus_spikes_1.h5"
    expected_spikes_2 = tmp_path / "PoissonInputStimulus_spikes_2.h5"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
    assert expected_spikes_1.exists()
    assert expected_spikes_2.exists()

    expected_circuit_config_path = tmp_path / "circuit" / "circuit_config.json"
    expected_circuit_nodes_path = tmp_path / "circuit" / "nodes.h5"
    expected_circuit_edges_path = tmp_path / "circuit" / "edges.h5"

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
