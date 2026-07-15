"""Tests for Entity forward-reference resolution."""

import uuid

from entitysdk.models import CellMorphology, Derivation, Subject
from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity


def test_entity_is_fully_defined_after_import():
    assert Entity.__pydantic_complete__


def test_entity_subclasses_are_fully_defined_after_import():
    assert Subject.__pydantic_complete__
    assert CellMorphology.__pydantic_complete__


def test_entity_accepts_derivation_lists():
    derivation_id = uuid.uuid4()
    entity = Entity(
        name="entity-with-derivations",
        generated_from_derivations=[
            Derivation(id=derivation_id, label="generated"),
        ],
        used_by_derivations=None,
    )

    assert entity.generated_from_derivations is not None
    assert entity.generated_from_derivations[0].id == derivation_id


def test_entity_accepts_contributions():
    entity = Entity(name="entity-with-contributions", contributions=[])

    assert entity.contributions == []


def test_entity_model_validate_accepts_derivation_payload():
    entity = Entity.model_validate(
        {
            "name": "entity",
            "generated_from_derivations": [{"id": str(uuid.uuid4()), "label": "derivation"}],
            "contributions": [],
        }
    )

    assert entity.generated_from_derivations is not None
    assert isinstance(entity.generated_from_derivations[0], Derivation)


def test_entity_model_validate_accepts_contribution_payload():
    entity = Entity.model_validate(
        {
            "name": "entity",
            "contributions": [
                {
                    "agent": {
                        "type": "person",
                        "pref_label": "Jane Doe",
                        "given_name": "Jane",
                        "family_name": "Doe",
                    },
                    "role": {"name": "curator", "role_id": "curator"},
                }
            ],
        }
    )

    assert entity.contributions is not None
    assert isinstance(entity.contributions[0], Contribution)
