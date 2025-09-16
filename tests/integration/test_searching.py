import pytest

from entitysdk.models import (
    Contribution,
    ElectricalCellRecording,
    EModel,
    IonChannel,
    IonChannelModel,
    IonChannelRecording,
    License,
    MEModel,
    MEModelCalibrationResult,
    MTypeClass,
    Organization,
    Person,
    ReconstructionMorphology,
    Role,
    SingleNeuronSimulation,
    SingleNeuronSynaptome,
    SingleNeuronSynaptomeSimulation,
    Species,
    Strain,
    ValidationResult,
)


@pytest.mark.parametrize(
    "entity_type",
    [
        Contribution,
        IonChannel,
        IonChannelModel,
        IonChannelRecording,
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
        ValidationResult,
        MEModelCalibrationResult,
        SingleNeuronSimulation,
        SingleNeuronSynaptomeSimulation,
        SingleNeuronSynaptome,
    ],
)
def test_is_searchable(entity_type, client):
    res = client.search_entity(entity_type=entity_type, limit=1).one()
    assert res.id
