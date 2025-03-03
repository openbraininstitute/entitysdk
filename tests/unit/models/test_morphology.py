from unittest.mock import Mock

import pytest

from entitysdk.models.morphology import (
    BrainLocation,
    BrainRegion,
    ReconstructionMorphology,
    Species,
    Strain,
)


@pytest.fixture
def species():
    return Species(id=1, name="Mus musculus", taxonomy_id="NCBITaxon:10090")


@pytest.fixture
def strain(species):
    return Strain(
        id=1,
        name="Cux2-CreERT2",
        taxonomy_id="http://bbp.epfl.ch/neurosciencegraph/ontologies/speciestaxonomy/RBS4I6tyfUBSDt1i0jXLpgN",
        species_id=1,
    )


@pytest.fixture
def brain_location():
    return BrainLocation(
        id=1,
        x=4101.52490234375,
        y=1173.8499755859375,
        z=4744.60009765625,
    )


@pytest.fixture
def brain_region():
    return BrainRegion(
        id=68,
        name="Frontal pole, layer 1",
        acronym="FRP1",
        children=[],
    )


@pytest.fixture
def morphology(species, strain, brain_region):
    return ReconstructionMorphology(
        name="my-morph",
        description="my-description",
        species=species,
        strain=strain,
        brain_region=brain_region,
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
        "location": None,
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


def test_read_reconstruction_morphology(client, json_morphology_expanded):
    client._http_client.request.return_value = Mock(json=lambda: json_morphology_expanded)

    entity = client.get(
        entity_id=1,
        entity_type=ReconstructionMorphology,
        token="mock-token",
        with_assets=False,
    )

    assert entity.id == 6466


def test_register_reconstruction_morphology(client, morphology):
    client._http_client.request.return_value = Mock(
        json=lambda: morphology.model_dump() | {"id": 1}
    )

    registered = client.register(entity=morphology, token="mock-token")

    assert registered.id == 1
    assert registered.name == morphology.name


def test_update_reconstruction_morphology(client, morphology):
    morphology = morphology.evolve(id=1)

    client._http_client.request.return_value = Mock(
        json=lambda: morphology.model_dump() | {"id": 1, "name": "foo"}
    )

    updated = client.update(
        entity_id=1,
        entity_type=ReconstructionMorphology,
        attrs_or_entity={
            "name": "foo",
        },
        token="mock-token",
    )

    assert updated.id == 1
    assert updated.name == "foo"
