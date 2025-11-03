import json
from pathlib import Path

import pytest

from entitysdk import models
from entitysdk.models.activity import Activity
from entitysdk.models.entity import Entity

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
]


def _get_update_data(model_class):
    if issubclass(model_class, Entity):
        return {"name": "New Name"}
    if issubclass(model_class, Activity):
        return {"end_time": "2025-11-03T12:40:59.794317Z"}
    msg = f"Invalid class: {model_class.__name__}"
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
