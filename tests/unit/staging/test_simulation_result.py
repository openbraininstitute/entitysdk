from entitysdk.staging import simulation_result as test_module


def test_stage_simulation_result(
    api_url,
    client,
    tmp_path,
    simulation,
    simulation_result,
    voltage_report_1,
    voltage_report_2,
    spike_report,
    httpx_mock,
):
    # httpx_mock.add_response(
    #    method="GET",
    #    url=f"{api_url}/simulation/{simulation.id}/assets/{simulation.assets[0].id}/download",
    #    json=simulation_config,
    # )
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

    test_module.stage_simulation_result(
        client,
        model=simulation_result,
        output_dir=tmp_path,
    )

    expected_voltage_report_1 = tmp_path / "SomaVoltRec 1.h5"
    expected_voltage_report_2 = tmp_path / "SomaVoltRec 2.h5"
    expected_spike_report = tmp_path / "spikes.h5"

    assert expected_voltage_report_1.exists()
    assert expected_voltage_report_2.exists()
    assert expected_spike_report.exists()
