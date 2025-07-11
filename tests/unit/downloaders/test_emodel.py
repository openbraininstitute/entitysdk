import uuid

from entitysdk.downloaders.emodel import download_hoc
from entitysdk.models.emodel import EModel
from entitysdk.types import AssetLabel, ContentType


def _mock_asset_response(asset_id):
    return {
        "id": str(asset_id),
        "path": "foo.hoc",
        "full_path": "foo.hoc",
        "is_directory": False,
        "label": AssetLabel.neuron_hoc,
        "content_type": ContentType.application_hoc,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def test_download_hoc(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test downloading a hoc file from an EModel entity."""
    emodel_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    hierarchy_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.hoc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )

    emodel = EModel(
        id=emodel_id,
        name="foo",
        species={"name": "foo", "taxonomy_id": "bar"},
        brain_region={
            "name": "foo",
            "annotation_value": 997,
            "acronym": "bar",
            "parent_structure_id": None,
            "hierarchy_id": str(hierarchy_id),
            "color_hex_triplet": "#FFFFFF",
        },
        iteration="foofoo",
        score=42,
        seed=0,
        assets=[_mock_asset_response(asset_id)],
    )

    output_path = download_hoc(
        client=client,
        emodel=emodel,
        output_dir=tmp_path,
    )

    assert output_path.is_file()
