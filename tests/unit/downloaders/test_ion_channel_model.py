import uuid

from entitysdk.downloaders.ion_channel_model import download_ion_channel_mechanism
from entitysdk.models.ion_channel_model import IonChannelModel, NeuronBlock
from entitysdk.types import AssetLabel, ContentType


def _mock_asset_response(asset_id):
    return {
        "id": str(asset_id),
        "path": "foo.mod",
        "full_path": "foo.mod",
        "is_directory": False,
        "content_type": ContentType.application_mod,
        "label": AssetLabel.neuron_mechanisms,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def test_download_ion_channel_model(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test downloading an ion channel model file from an EModel entity."""
    model_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    hierarchy_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{model_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.mod"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{model_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )

    ic_model = IonChannelModel(
        id=model_id,
        name="foo",
        nmodl_suffix="Ca_HVA",
        description="foo description",
        species={"name": "foo", "taxonomy_id": "bar"},
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
        neuron_block=NeuronBlock(),
        assets=[_mock_asset_response(asset_id)],
    )

    output_path = download_ion_channel_mechanism(
        client=client,
        ion_channel_model=ic_model,
        output_dir=tmp_path,
    )

    assert output_path.is_file()
