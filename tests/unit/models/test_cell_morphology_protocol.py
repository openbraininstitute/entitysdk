import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from entitysdk.models.cell_morphology_protocol import (
    CellMorphologyProtocol,
    ComputationallySynthesizedCellMorphologyProtocol,
    DigitalReconstructionCellMorphologyProtocol,
    ModifiedReconstructionCellMorphologyProtocol,
    PlaceholderCellMorphologyProtocol,
)

DATA_DIR = Path(__file__).parent / "data"
MODELS_DIR = DATA_DIR / "manual" / "one"
MODELS = [
    {
        "class": DigitalReconstructionCellMorphologyProtocol,
        "file": MODELS_DIR / "cell_morphology_protocol__digital_reconstruction.json",
    },
    {
        "class": ModifiedReconstructionCellMorphologyProtocol,
        "file": MODELS_DIR / "cell_morphology_protocol__modified_reconstruction.json",
    },
    {
        "class": ComputationallySynthesizedCellMorphologyProtocol,
        "file": MODELS_DIR / "cell_morphology_protocol__computationally_synthesized.json",
    },
    {
        "class": PlaceholderCellMorphologyProtocol,
        "file": MODELS_DIR / "cell_morphology_protocol__placeholder.json",
    },
]


@pytest.fixture(params=MODELS, ids=[d["class"].__name__ for d in MODELS])
def model_info(request):
    return request.param


@pytest.fixture
def json_data(model_info):
    return json.loads(model_info["file"].read_bytes())


def test_adapter(json_data, model_info):
    specific_class = model_info["class"]
    Adapter = CellMorphologyProtocol

    # test adapter from json
    model = Adapter.model_validate(json_data)
    assert isinstance(model, specific_class)

    # test adapter from kwargs
    new_model = Adapter(**json_data)
    assert new_model == model

    # test specific class from json
    new_model = specific_class.model_validate(json_data)
    assert new_model == model

    # test specific class from kwargs
    new_model = specific_class(**json_data)
    assert new_model == model

    with pytest.raises(TypeError, match="Positional args not supported"):
        Adapter("name")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Adapter(generation_type=json_data["generation_type"], invalid_input="invalid")
