from entitysdk.models import agent as test_module
from entitysdk.models.core import Identifiable

from ..util import MOCK_UUID


def test_person_entity():
    agent = test_module.Person(
        givenName="foo",
        familyName="bar",
        pref_label="test",
        type="person",
    )
    assert agent.givenName == "foo"
    assert agent.familyName == "bar"
    assert agent.pref_label == "test"
    assert agent.type == "person"


def test_organization_entity():
    organization = test_module.Organization(
        pref_label="foo",
        alternative_name="bar",
        type="organization",
    )
    assert organization.pref_label == "foo"
    assert organization.alternative_name == "bar"
    assert organization.type == "organization"


def test_agent_discriminated_union():
    class A(Identifiable):
        agent: test_module.AgentUnion | None = None

    res = A.model_validate(
        {
            "id": MOCK_UUID,
        }
    )
    assert res.id == MOCK_UUID

    res = A.model_validate(
        {
            "id": MOCK_UUID,
            "agent": {
                "type": "organization",
                "pref_label": "foo",
            },
        }
    )
    assert res.id == MOCK_UUID
    assert isinstance(res.agent, test_module.Organization)

    res = A.model_validate(
        {
            "id": MOCK_UUID,
            "agent": {
                "type": "person",
                "pref_label": "foo",
                "givenName": "John",
                "familyName": "Smith",
            },
        }
    )
    assert res.id == MOCK_UUID
    assert isinstance(res.agent, test_module.Person)
