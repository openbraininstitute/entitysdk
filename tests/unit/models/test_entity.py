"""Tests for Entity forward-reference resolution."""

import uuid

from entitysdk.models import CellMorphology, Derivation, Subject
from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity


def test_entity_is_fully_defined_after_import():
    assert Entity.__pydantic_complete__


def test_entity_subclasses_model_validate_without_explicit_rebuild():
    """defer_build may leave subclasses incomplete until first use; validation still works."""
    subject = Subject.model_validate(
        {
            "name": "subject",
            "description": "",
            "sex": "male",
            "species": {"name": "Mus musculus", "taxonomy_id": "NCBITaxon:10090"},
        }
    )
    morphology = CellMorphology.model_validate(
        {
            "name": "morph",
            "description": "",
            "cell_morphology_protocol": {
                "name": "protocol",
                "description": "",
                "generation_type": "placeholder",
            },
        }
    )

    assert subject.name == "subject"
    assert morphology.name == "morph"


def test_entity_accepts_derivation_lists():
    derivation_id = uuid.uuid4()
    entity = Entity(
        generated_from_derivations=[
            Derivation(id=derivation_id, label="generated"),
        ],
        used_by_derivations=[],
    )

    assert entity.generated_from_derivations is not None
    assert entity.generated_from_derivations[0].id == derivation_id
    assert entity.used_by_derivations == []


def test_entity_accepts_contributions():
    entity = Entity(contributions=[])

    assert entity.contributions == []


def test_entity_model_validate_accepts_derivation_payload():
    entity = Entity.model_validate(
        {
            "generated_from_derivations": [{"id": str(uuid.uuid4()), "label": "derivation"}],
            "contributions": [],
        }
    )

    assert entity.generated_from_derivations is not None
    assert isinstance(entity.generated_from_derivations[0], Derivation)


def test_entity_model_validate_accepts_contribution_payload():
    entity = Entity.model_validate(
        {
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
