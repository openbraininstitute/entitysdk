import json
import uuid

import pytest

from entitysdk.downloaders import simulation as test_module
from entitysdk.exception import EntitySDKError
from entitysdk.models import Simulation
from entitysdk.types import AssetLabel, ContentType


def _mock_asset_response(asset_id, content_type, label):
    return {
        "id": str(asset_id),
        "path": "content.json",
        "full_path": "content.json",
        "is_directory": False,
        "content_type": str(content_type),
        "label": str(label),
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
        "storage_type": "aws_s3_internal",
    }


def _mock_simulation(simulation_id, assets):
    return Simulation(
        id=simulation_id,
        simulation_campaign_id=uuid.uuid4(),
        entity_id=uuid.uuid4(),
        scan_parameters={},
        assets=assets,
    )


def test_download_simulation_config_content(
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    asset_id = uuid.uuid4()
    simulation_id = uuid.uuid4()
    expected = {"foo": "bar"}

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=json.dumps(expected),
    )
    asset = _mock_asset_response(
        asset_id, ContentType.application_json, AssetLabel.sonata_simulation_config
    )
    model = _mock_simulation(simulation_id, assets=[asset])
    content = test_module.download_simulation_config_content(client, model=model)
    assert content == expected


def test_download_node_sets_file(
    client,
    tmp_path,
    httpx_mock,
    api_url,
    request_headers,
):
    simulation_id = uuid.uuid4()

    # no assets
    model = _mock_simulation(simulation_id, assets=[])
    res = test_module.download_node_sets_file(client, model=model, output_path=tmp_path)
    assert res is None

    # too many assets
    asset_id = uuid.uuid4()
    asset = _mock_asset_response(
        asset_id, ContentType.application_json, AssetLabel.custom_node_sets
    )
    model = _mock_simulation(simulation_id, assets=[asset, asset])
    with pytest.raises(EntitySDKError, match="Too many node_sets_file for Simulation"):
        test_module.download_node_sets_file(client, model=model, output_path=tmp_path)

    expected = {"foo": "bar"}
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=json.dumps(expected),
    )
    model = _mock_simulation(simulation_id, assets=[asset])
    res = test_module.download_node_sets_file(client, model=model, output_path=tmp_path)
    with res.open() as fd:
        assert expected == json.load(fd)


def test_download_spike_replay_files(
    client,
    tmp_path,
    httpx_mock,
    api_url,
    request_headers,
):
    simulation_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    asset = _mock_asset_response(
        asset_id, ContentType.application_json, AssetLabel.custom_node_sets
    )
    model = _mock_simulation(simulation_id, assets=[asset])
    res = test_module.download_spike_replay_files(client, model=model, output_dir=tmp_path)
    assert res == []

    asset = _mock_asset_response(asset_id, ContentType.application_x_hdf5, AssetLabel.replay_spikes)
    model = _mock_simulation(simulation_id, assets=[asset])
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{simulation_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="asdf",
    )
    res = test_module.download_spike_replay_files(client, model=model, output_dir=tmp_path)
    for p in res:
        assert p.exists()
