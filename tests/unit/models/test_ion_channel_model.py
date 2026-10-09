import uuid

from entitysdk import models, types
from entitysdk.models.ion_channel_model import IonChannelModel, NeuronBlock


def test_temperature_keeps_its_fraction():
    ic_model = IonChannelModel(
        name="foo",
        nmodl_suffix="Kv3_1",
        description="foo description",
        subject=models.Subject(
            sex=types.Sex.male,
            species={"name": "foo", "taxonomy_id": "bar"},
        ),
        brain_region={
            "name": "foo",
            "annotation_value": 997,
            "acronym": "bar",
            "parent_structure_id": None,
            "hierarchy_id": str(uuid.uuid4()),
            "color_hex_triplet": "#FFFFFF",
        },
        is_temperature_dependent=False,
        temperature_celsius=34.5,
        neuron_block=NeuronBlock(),
    )

    assert ic_model.temperature_celsius == 34.5
