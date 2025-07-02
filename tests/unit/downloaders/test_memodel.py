import os
import uuid

from entitysdk.downloaders.memodel import download_memodel
from entitysdk.models.emodel import EModel
from entitysdk.models.memodel import MEModel
from entitysdk.models.morphology import ReconstructionMorphology
from entitysdk.types import AssetLabel, ContentType, ValidationStatus


def _mock_morph_asset_response(asset_id):
    """Mock response for morphology asset."""
    return {
        "id": str(asset_id),
        "path": "foo.asc",
        "full_path": "foo.asc",
        "is_directory": False,
        "label": AssetLabel.morphology,
        "content_type": ContentType.application_asc,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def _mock_ic_asset_response(asset_id):
    """Mock response for ion channel model asset."""
    return {
        "id": str(asset_id),
        "path": "foo.mod",
        "full_path": "foo.mod",
        "is_directory": False,
        "label": AssetLabel.neuron_mechanisms,
        "content_type": ContentType.application_mod,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def _mock_emodel_asset_response(asset_id):
    """Mock response for emodel asset."""
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


def test_download_memodel(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test downloading all memodel-related files from an MEModel entity."""
    memodel_id = uuid.uuid4()
    morph_id = uuid.uuid4()
    emodel_id = uuid.uuid4()
    ic_model_id = uuid.uuid4()
    morph_asset_id = uuid.uuid4()
    emodel_asset_id = uuid.uuid4()
    ic_asset_id = uuid.uuid4()
    hierarchy_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/reconstruction-morphology/{morph_id}/assets/{morph_asset_id}",
        match_headers=request_headers,
        json=_mock_morph_asset_response(morph_id) | {"path": "foo.asc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/reconstruction-morphology/{morph_id}/assets/{morph_asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel_id}/assets/{emodel_asset_id}",
        match_headers=request_headers,
        json=_mock_emodel_asset_response(emodel_asset_id) | {"path": "foo.hoc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel_id}/assets/{emodel_asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{ic_model_id}/assets/{ic_asset_id}",
        match_headers=request_headers,
        json=_mock_ic_asset_response(ic_asset_id) | {"path": "foo.mod"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/ion-channel-model/{ic_model_id}/assets/{ic_asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/emodel/{emodel_id}",
        match_headers=request_headers,
        json={
            "id": str(emodel_id),
            "name": "foo",
            "species": {"name": "foo", "taxonomy_id": "bar"},
            "brain_region": {
                "name": "foo",
                "annotation_value": 997,
                "acronym": "bar",
                "parent_structure_id": None,
                "hierarchy_id": str(hierarchy_id),
                "color_hex_triplet": "#FFFFFF",
            },
            "iteration": "foofoo",
            "score": 42,
            "seed": 0,
            "ion_channel_models": [
                {
                    "id": str(ic_model_id),
                    "name": "foo",
                    "nmodl_suffix": "Ca_HVA",
                    "description": "foo description",
                    "species": {"name": "foo", "taxonomy_id": "bar"},
                    "brain_region": {
                        "name": "foo",
                        "annotation_value": 997,
                        "acronym": "bar",
                        "parent_structure_id": None,
                        "hierarchy_id": str(hierarchy_id),
                        "color_hex_triplet": "#FFFFFF",
                    },
                    "is_temperature_dependent": False,
                    "temperature_celsius": 34,
                    "neuron_block": {},
                    "assets": [_mock_ic_asset_response(ic_asset_id)],
                }
            ],
            "assets": [_mock_emodel_asset_response(emodel_asset_id)],
        },
    )

    memodel = MEModel(
        id=memodel_id,
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
        validation_status=ValidationStatus.done,
        morphology=ReconstructionMorphology(
            id=morph_id, name="foo", assets=[_mock_morph_asset_response(morph_asset_id)]
        ),
        emodel=EModel(
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
            # assets=[
            #     _mock_emodel_asset_response(emodel_asset_id)
            # ]
        ),
    )

    downloaded_memodel = download_memodel(
        client=client,
        memodel=memodel,
        output_dir=tmp_path,
    )
    assert downloaded_memodel.hoc_path.is_file()
    assert downloaded_memodel.morphology_path.is_file()
    assert downloaded_memodel.mechanisms_dir.is_dir()
    assert len(os.listdir(downloaded_memodel.mechanisms_dir)) == 1
