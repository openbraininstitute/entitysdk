from pathlib import Path

from entitysdk.staging import simulation as test_module
from entitysdk.utils.io import load_json


def test_stage_simulation(
    client,
    tmp_path,
    simulation,
    simulation_config,
    simulation_httpx_mocks,
):
    circuit_config_path = "/foo/bar/circuit_config.json"

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
