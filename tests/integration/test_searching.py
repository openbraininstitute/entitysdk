import pytest

from entitysdk.models import (
    CellMorphology,
    CellMorphologyProtocol,
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
        CellMorphology,
        CellMorphologyProtocol,
        Contribution,
        IonChannel,
        IonChannelModel,
        IonChannelRecording,
        License,
        MTypeClass,
        Person,
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
