import pytest

from entitysdk.models import (
    Contribution,
    ElectricalCellRecording,
    EModel,
    IonChannelModel,
    License,
    MEModel,
    MTypeClass,
    Organization,
    Person,
    ReconstructionMorphology,
    Role,
    Species,
    Strain,
)


@pytest.mark.parametrize(
    "entity_type",
    [
        Contribution,
        IonChannelModel,
        License,
        MTypeClass,
        Person,
        ReconstructionMorphology,
        Role,
        Species,
        Strain,
        Organization,
        EModel,
        MEModel,
        ElectricalCellRecording,
    ],
)
def test_is_searchable(entity_type, client):
    res = client.search_entity(entity_type=entity_type, limit=1).one()
    assert res.id
