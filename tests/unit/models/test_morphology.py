from unittest.mock import Mock, patch

import pytest

from entitysdk import client as test_module
from entitysdk.common import ProjectContext
from entitysdk.models.morphology import BrainRegion, ReconstructionMorphology, Species, Strain


@pytest.fixture
def mock_project_context():
    return ProjectContext(
        project_id="103d7868-147e-4f07-af0d-71d8568f575c",
        virtual_lab_id="103d7868-147e-4f07-af0d-71d8568f575c",
    )


@pytest.fixture
def json_morphology_expanded():
    return {
        "authorized_project_id": "103d7868-147e-4f07-af0d-71d8568f575c",
        "authorized_public": False,
        "license": {
            "id": 3,
            "creation_date": "2025-02-20T13:42:46.532333Z",
            "update_date": "2025-02-20T13:42:46.532333Z",
            "name": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "description": "Foo",
            "label": "CC BY-NC-SA 4.0 Deed",
        },
        "id": 6466,
        "creation_date": "2025-02-20T13:44:50.111791Z",
        "update_date": "2025-02-20T13:44:50.111791Z",
        "name": "04446-04462-X10187-Y13578_final",
        "description": "Bar",
        "brain_location": None,
        "species": {
            "id": 1,
            "creation_date": "2025-02-20T13:42:56.228818Z",
            "update_date": "2025-02-20T13:42:56.228818Z",
            "name": "Mus musculus",
            "taxonomy_id": "NCBITaxon:10090",
        },
        "strain": None,
        "brain_region": {
            "id": 262,
            "creation_date": "2025-02-20T13:36:51.010167Z",
            "update_date": "2025-02-20T13:36:51.010167Z",
            "name": "Reticular nucleus of the thalamus",
            "acronym": "RT",
            "children": [],
        },
    }


@patch("entitysdk.client.make_db_api_request")
def test_read_reconstruction_morphology(
    mock_request, json_morphology_expanded, mock_project_context
):
    mock_request.return_value = Mock(json=lambda: json_morphology_expanded)

    entity = test_module.get_entity(
        url=None,
        entity_type=ReconstructionMorphology,
        project_context=mock_project_context,
        token="mock-token",
    )

    assert entity.id == 6466


@patch("entitysdk.client.make_db_api_request")
def test_register_reconstruction_morphology(mock_request, mock_project_context):
    morph = ReconstructionMorphology(
        name="my-morph",
        species=Species(taxonomy_id="NCBITaxon"),
        strain=Strain(name="my-strain", pref_label="my-strain"),
        brain_region=BrainRegion(acronym="CB", children=[1, 2]),
    )

    mock_request.return_value = Mock(json=lambda: morph.model_dump() | {"id": 1})

    registered = test_module.register_entity(
        url=None, entity=morph, project_context=mock_project_context, token="mock-token"
    )

    assert registered.id == 1
    assert registered.name == morph.name


@patch("entitysdk.client.make_db_api_request")
def test_update_reconstruction_morphology(mock_request, mock_project_context):
    morph = ReconstructionMorphology(
        id=1,
        name="foo",
        species=Species(taxonomy_id="NCBITaxon"),
        strain=Strain(name="my-strain", pref_label="my-strain"),
        brain_region=BrainRegion(acronym="CB", children=[1, 2]),
    )

    mock_request.return_value = Mock(json=lambda: morph.model_dump() | {"id": 1})

    updated = test_module.update_entity(
        url=None,
        entity_type=ReconstructionMorphology,
        attrs_or_entity={
            "name": "foo",
        },
        project_context=mock_project_context,
        token="mock-token",
    )

    assert updated.id == 1
    assert updated.name == "foo"
