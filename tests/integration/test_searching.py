import pytest

from entitysdk.models.agent import Organization, Person
from entitysdk.models.contribution import Role
from entitysdk.models.morphology import (
    License,
    ReconstructionMorphology,
    Species,
    Strain,
)
from entitysdk.models.mtype import MTypeClass


@pytest.mark.parametrize(
    "entity_type",
    [
        License,
        MTypeClass,
        Person,
        ReconstructionMorphology,
        Role,
        Species,
        Strain,
        Organization,
    ],
)
def test_is_searchable(entity_type, client):
    res = client.search_entity(entity_type=entity_type, limit=1).one()
    assert res.id
