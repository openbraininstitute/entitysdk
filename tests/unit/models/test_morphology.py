import pytest

from entitysdk.models.morphology import (
    BrainLocation,
    BrainRegion,
    ReconstructionMorphology,
    Species,
    Strain,
)

from ..util import MOCK_UUID


@pytest.fixture
def species(random_uuid):
    return Species(id=random_uuid, name="Mus musculus", taxonomy_id="NCBITaxon:10090")


@pytest.fixture
def strain(species, random_uuid):
    return Strain(
        name="Cux2-CreERT2",
        taxonomy_id="http://bbp.epfl.ch/neurosciencegraph/ontologies/speciestaxonomy/RBS4I6tyfUBSDt1i0jXLpgN",
        species_id=random_uuid,
    )


@pytest.fixture
def brain_location(random_uuid):
    return BrainLocation(
        id=random_uuid,
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
            "id": str(MOCK_UUID),
            "creation_date": "2025-02-20T13:42:46.532333Z",
            "update_date": "2025-02-20T13:42:46.532333Z",
            "name": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "description": "Foo",
            "label": "CC BY-NC-SA 4.0 Deed",
        },
        "id": str(MOCK_UUID),
        "creation_date": "2025-02-20T13:44:50.111791Z",
        "update_date": "2025-02-20T13:44:50.111791Z",
        "name": "04446-04462-X10187-Y13578_final",
        "description": "Bar",
        "location": None,
        "species": {
            "id": str(MOCK_UUID),
            "creation_date": "2025-02-20T13:42:56.228818Z",
            "update_date": "2025-02-20T13:42:56.228818Z",
            "name": "Mus musculus",
            "taxonomy_id": "NCBITaxon:10090",
        },
        "strain": None,
        "brain_region": {
            "id": 1,
            "creation_date": "2025-02-20T13:36:51.010167Z",
            "update_date": "2025-02-20T13:36:51.010167Z",
            "name": "Reticular nucleus of the thalamus",
            "acronym": "RT",
            "children": [],
        },
    }


def test_read_reconstruction_morphology(client, httpx_mock, auth_token, json_morphology_expanded):
    httpx_mock.add_response(method="GET", json=json_morphology_expanded)

    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=ReconstructionMorphology,
        token=auth_token,
        with_assets=False,
    )

    assert entity.id == MOCK_UUID


def test_register_reconstruction_morphology(client, httpx_mock, auth_token, morphology):
    httpx_mock.add_response(
        method="POST", json=morphology.model_dump(mode="json") | {"id": str(MOCK_UUID)}
    )

    registered = client.register_entity(entity=morphology, token=auth_token)

    assert registered.id == MOCK_UUID
    assert registered.name == morphology.name


def test_update_reconstruction_morphology(client, httpx_mock, auth_token, morphology):
    morphology = morphology.evolve(id=1)
    httpx_mock.add_response(
        method="PATCH",
        json=morphology.model_dump(mode="json") | {"id": str(MOCK_UUID), "name": "foo"},
    )

    updated = client.update_entity(
        entity_id=MOCK_UUID,
        entity_type=ReconstructionMorphology,
        attrs_or_entity={
            "name": "foo",
        },
        token=auth_token,
    )

    assert updated.id == MOCK_UUID
    assert updated.name == "foo"
