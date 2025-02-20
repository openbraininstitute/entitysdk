from unittest.mock import Mock, patch

import pytest

from entitysdk import client as test_module
from entitysdk.common import ProjectContext
from entitysdk.models.morphology import ReconstructionMorphology


@pytest.fixture
def mock_project_context():
    return ProjectContext(
        project_id="103d7868-147e-4f07-af0d-71d8568f575c",
        virtual_lab_id="103d7868-147e-4f07-af0d-71d8568f575c",
    )


@patch("entitysdk.client.make_request")
def test_client__morph_read(mock_make_request, mock_project_context):
    mock_make_request.return_value = Mock(
        json=lambda: {
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
    )

    entity = test_module.get_entity(
        url=None,
        model_cls=ReconstructionMorphology,
        project_context=mock_project_context,
        token="mock-token",
    )

    assert entity.id == 6466
