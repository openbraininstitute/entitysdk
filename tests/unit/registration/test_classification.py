"""Tests for classification registration helpers."""

import uuid

from entitysdk.models import EModel, ETypeClass, ETypeClassification, MTypeClass, MTypeClassification
from entitysdk.registration.classification import (
    register_etype_classification,
    register_mtype_classification,
)

from .conftest import load_extracted_json


def test_register_etype_classification(client, register_entity_responder):
    register_entity_responder(("etype-classification",))
    entity = EModel.model_validate(
        {**load_extracted_json("emodel"), "id": str(uuid.uuid4())},
    )
    etype_class = ETypeClass.model_validate(load_extracted_json("etype"))

    registered = register_etype_classification(
        client=client,
        entity=entity,
        etype_class=etype_class,
    )

    assert isinstance(registered, ETypeClassification)
    assert registered.id is not None
    assert registered.entity_id == entity.id
    assert registered.etype_class_id == etype_class.id


def test_register_mtype_classification(client, register_entity_responder):
    register_entity_responder(("mtype-classification",))
    entity = EModel.model_validate(
        {**load_extracted_json("emodel"), "id": str(uuid.uuid4())},
    )
    mtype_class = MTypeClass.model_validate(load_extracted_json("mtype"))

    registered = register_mtype_classification(
        client=client,
        entity=entity,
        mtype_class=mtype_class,
    )

    assert isinstance(registered, MTypeClassification)
    assert registered.id is not None
    assert registered.entity_id == entity.id
    assert registered.mtype_class_id == mtype_class.id
