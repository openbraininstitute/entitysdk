import pytest

from entitysdk.models.brain_region import BrainRegion


@pytest.fixture
def json_data():
    return {
        "id": "38553ac8-7d71-4591-bfee-2fc72e2dffdf",
        "update_date": "2025-05-09T13:32:18.034672Z",
        "creation_date": "2025-05-09T13:32:18.034672Z",
        "name": "Accessory abducens nucleus",
        "annotation_value": 568,
        "acronym": "ACVI",
        "parent_structure_id": "596305b3-71b2-41e4-afd3-b9f2e90f79f8",
        "hierarchy_id": "e3e70682-c209-4cac-a29f-6fbed82c07cd",
        "color_hex_triplet": "188064",
    }


def test_model(json_data):
    res = BrainRegion.model_validate(json_data)
    assert res.model_dump(mode="json") == json_data
