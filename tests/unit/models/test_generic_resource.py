import json
import operator
from pathlib import Path
from typing import Literal

import pytest
from pydantic import BaseModel

from entitysdk import models, route
from entitysdk.models.core import Identifiable

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"

# routes not implemented yet in entitysdk
MISSING_ROUTES = {
    "calibration",
    "cell-composition",
    "validation",
}

# resources that don't provide an update endpoint
NO_UPDATE_RESOURCES = {
    "CellComposition",
    "Consortium",
    "Contribution",
    "Derivation",
    "EMDenseReconstructionDataset",  # should be updatable?
    "Entity",
    "ETypeClassification",
    "ExternalUrl",  # should be updatable?
    "MeasurementAnnotation",
    "MTypeClassification",
    "Organization",
    "Person",
    "ScientificArtifactExternalUrlLink",
    "ScientificArtifactPublicationLink",
}

# map route to class while keeping the first class in case of multiple classes for the same route
ROUTE_TO_CLASS_NAME: dict[str, str] = {
    route_name: entity_class_name
    for entity_class_name, route_name in reversed(route._ROUTES.items())
}
ROUTE_TO_CLASS: dict[str, type[Identifiable]] = {
    route_name: getattr(models, entity_class_name)
    for route_name, entity_class_name in ROUTE_TO_CLASS_NAME.items()
}


class ModelInfo(BaseModel):
    file: Path
    cls: type[Identifiable] | None
    route: str
    mode: Literal["one", "many"]
    source: Literal["manual", "extracted"]


def _read_extracted_models_data():
    root = DATA_DIR / "extracted"
    return [
        ModelInfo.model_validate(
            {
                "file": path,
                "cls": ROUTE_TO_CLASS.get(path.parent.name),
                "route": path.parent.name,
                "mode": path.parent.parent.name,
                "source": root.name,
            }
        )
        for path in root.rglob("*.json")
    ]


def _read_manual_models_data():
    root = DATA_DIR / "manual"
    return [
        ModelInfo.model_validate(
            {
                "file": path,
                "cls": ROUTE_TO_CLASS.get(route),
                "route": route,
                "mode": path.parent.name,
                "source": root.name,
            }
        )
        for path, route in (
            (
                path,
                path.stem.split("__", 1)[0].replace("_", "-"),
            )
            for path in root.rglob("*.json")
        )
    ]


ALL_MODELS = _read_extracted_models_data() + _read_manual_models_data()
MANY_MODELS = sorted(
    [m for m in ALL_MODELS if m.mode == "many"],
    key=operator.attrgetter("route", "source", "mode", "file"),
)
SINGLE_MODELS = sorted(
    [m for m in ALL_MODELS if m.mode != "many"],
    key=operator.attrgetter("route", "source", "mode", "file"),
)

ENTITY_ADAPTERS = {models.CellMorphologyProtocol}


def _get_update_data(model_class: type[BaseModel]):
    if "name" in model_class.model_fields or model_class in ENTITY_ADAPTERS:  # named entities
        return {"name": "New Name"}
    if "end_time" in model_class.model_fields:  # activities
        return {"end_time": "2025-11-03T12:40:59.794317Z"}
    if "title" in model_class.model_fields:  # publication
        return {"title": "New custom title"}
    if "pref_label" in model_class.model_fields:  # mtype_class, etype_class
        return {"pref_label": "New custom pref_label"}
    msg = f"Unsupported class for testing update: {model_class.__name__}"
    raise RuntimeError(msg)


@pytest.fixture(params=SINGLE_MODELS, ids=[f"{m.route}/{m.file.name}" for m in SINGLE_MODELS])
def model_info(request) -> ModelInfo:
    param = request.param
    if param.cls is None:
        pytest.xfail("Route not implemented")
    return param


@pytest.fixture
def json_data(model_info) -> dict:
    return json.loads(model_info.file.read_bytes())


@pytest.fixture
def model(model_info, json_data) -> Identifiable:
    return model_info.cls.model_validate(json_data)


@pytest.fixture(params=MANY_MODELS, ids=[f"{m.route}/{m.file.name}" for m in MANY_MODELS])
def many_info(request) -> ModelInfo:
    param = request.param
    if param.cls is None:
        pytest.xfail("Route not implemented")
    return param


@pytest.fixture
def many_json_data(many_info) -> dict:
    return json.loads(many_info.file.read_bytes())


def test_models():
    models = ALL_MODELS
    assert len(models) > 0
    assert set(m.mode for m in models) == {"one", "many"}
    assert set(m.source for m in models) == {"manual", "extracted"}
    # compare the routes imported from files with the implemented routes
    assert set(ROUTE_TO_CLASS) & MISSING_ROUTES == set()
    assert set(ROUTE_TO_CLASS) | MISSING_ROUTES == set(m.route for m in models)


def test_read_one(client, httpx_mock, model_info, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=model_info.cls,
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_data


def test_create_one(client, httpx_mock, model, json_data):
    httpx_mock.add_response(
        method="POST",
        json=model.model_dump(mode="json", exclude_unset=True) | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=model)
    expected_json = json_data | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update_one(client, httpx_mock, model, json_data, model_info):
    if model_info.cls.__name__ in NO_UPDATE_RESOURCES:
        pytest.skip("No update endpoint")
    update_data = _get_update_data(model_info.cls)
    httpx_mock.add_response(
        method="PATCH",
        json=model.model_dump(mode="json", exclude_unset=True) | update_data,
    )
    updated = client.update_entity(
        entity_id=model.id,
        entity_type=model_info.cls,
        attrs_or_entity=update_data,
    )

    expected_json = json_data | update_data
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json


def test_read_many(client, httpx_mock, many_info, many_json_data):
    # overwrite page and total_items so that only a single request is made
    pagination = many_json_data["pagination"]
    pagination["page"] = 1
    pagination["total_items"] = min(pagination["total_items"], pagination["page_size"])
    httpx_mock.add_response(method="GET", json=many_json_data)

    entity_list = list(client.search_entity(entity_type=many_info.cls))
    for entity, expected_json in zip(entity_list, many_json_data["data"], strict=True):
        assert entity.model_dump(mode="json", exclude_unset=True) == expected_json
