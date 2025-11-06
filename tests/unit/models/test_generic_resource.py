import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from entitysdk import models

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"
MODELS = [
    {
        "class": models.AnalysisNotebookEnvironment,
        "file": DATA_DIR / "analysis_notebook_environment.json",
    },
    {
        "class": models.AnalysisNotebookExecution,
        "file": DATA_DIR / "analysis_notebook_execution.json",
    },
    {
        "class": models.AnalysisNotebookResult,
        "file": DATA_DIR / "analysis_notebook_result.json",
    },
    {
        "class": models.AnalysisNotebookTemplate,
        "file": DATA_DIR / "analysis_notebook_template.json",
    },
    {
        "class": models.CellMorphology,
        "file": DATA_DIR / "cell_morphology.json",
    },
    {
        "class": models.CellMorphologyProtocol,
        "file": DATA_DIR / "cell_morphology_protocol__digital_reconstruction.json",
    },
    {
        "class": models.CellMorphologyProtocol,
        "file": DATA_DIR / "cell_morphology_protocol__modified_reconstruction.json",
    },
    {
        "class": models.CellMorphologyProtocol,
        "file": DATA_DIR / "cell_morphology_protocol__computationally_synthesized.json",
    },
    {
        "class": models.CellMorphologyProtocol,
        "file": DATA_DIR / "cell_morphology_protocol__placeholder.json",
    },
    {
        "class": models.Circuit,
        "file": DATA_DIR / "circuit.json",
    },
    {
        "class": models.ElectricalCellRecording,
        "file": DATA_DIR / "electrical_cell_recording.json",
    },
    {
        "class": models.EMCellMesh,
        "file": DATA_DIR / "em_cell_mesh.json",
    },
    {
        "class": models.EMDenseReconstructionDataset,
        "file": DATA_DIR / "em_dense_reconstruction_dataset.json",
    },
    {
        "class": models.IonChannelModel,
        "file": DATA_DIR / "ion_channel_model.json",
    },
    {
        "class": models.IonChannelModelingCampaign,
        "file": DATA_DIR / "ion_channel_modeling_campaign.json",
    },
    {
        "class": models.IonChannelModelingConfigGeneration,
        "file": DATA_DIR / "ion_channel_modeling_config_generation.json",
    },
    {
        "class": models.IonChannelModelingConfig,
        "file": DATA_DIR / "ion_channel_modeling_config.json",
    },
    {
        "class": models.IonChannelModelingExecution,
        "file": DATA_DIR / "ion_channel_modeling_execution.json",
    },
    {
        "class": models.IonChannelRecording,
        "file": DATA_DIR / "ion_channel_recording.json",
    },
    {
        "class": models.IonChannel,
        "file": DATA_DIR / "ion_channel.json",
    },
    {
        "class": models.MEModelCalibrationResult,
        "file": DATA_DIR / "memodel_calibration_result.json",
    },
    {
        "class": models.SimulationCampaign,
        "file": DATA_DIR / "simulation_campaign.json",
    },
    {
        "class": models.SkeletonizationCampaign,
        "file": DATA_DIR / "skeletonization_campaign.json",
    },
    {
        "class": models.SkeletonizationConfig,
        "file": DATA_DIR / "skeletonization_config.json",
    },
    {
        "class": models.SkeletonizationConfigGeneration,
        "file": DATA_DIR / "skeletonization_config_generation.json",
    },
    {
        "class": models.SkeletonizationExecution,
        "file": DATA_DIR / "skeletonization_execution.json",
    },
    {
        "class": models.ValidationResult,
        "file": DATA_DIR / "validation_result.json",
    },
]
ENTITY_ADAPTERS = {models.CellMorphologyProtocol}


def _get_update_data(model_class: type[BaseModel]):
    if "name" in model_class.model_fields or model_class in ENTITY_ADAPTERS:
        return {"name": "New Name"}
    if "end_time" in model_class.model_fields:
        return {"end_time": "2025-11-03T12:40:59.794317Z"}
    msg = f"Unsupported class: {model_class.__name__}"
    raise RuntimeError(msg)


@pytest.fixture(params=MODELS, ids=[d["class"].__name__ for d in MODELS])
def model_info(request):
    return request.param


@pytest.fixture
def json_data(model_info):
    return json.loads(model_info["file"].read_bytes())


@pytest.fixture
def model(model_info, json_data):
    return model_info["class"].model_validate(json_data)


def test_read(client, httpx_mock, model_info, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=model_info["class"],
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_data


def test_register(client, httpx_mock, model, json_data):
    httpx_mock.add_response(
        method="POST",
        json=model.model_dump(mode="json", exclude_unset=True) | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=model)
    expected_json = json_data | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update(client, httpx_mock, model, json_data, model_info):
    update_data = _get_update_data(model_info["class"])
    httpx_mock.add_response(
        method="PATCH",
        json=model.model_dump(mode="json", exclude_unset=True) | update_data,
    )
    updated = client.update_entity(
        entity_id=model.id,
        entity_type=model_info["class"],
        attrs_or_entity=update_data,
    )

    expected_json = json_data | update_data
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json
