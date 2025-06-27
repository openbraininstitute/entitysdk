from entitysdk.models.core import AgentUnion, Identifiable, Organization, Person

from ..util import MOCK_UUID


def test_person_entity():
    agent = Person(
        given_name="foo",
        family_name="bar",
        pref_label="test",
        type="person",
    )
    assert agent.given_name == "foo"
    assert agent.family_name == "bar"
    assert agent.pref_label == "test"
    assert agent.type == "person"


def test_organization_entity():
    organization = Organization(
        pref_label="foo",
        alternative_name="bar",
        type="organization",
    )
    assert organization.pref_label == "foo"
    assert organization.alternative_name == "bar"
    assert organization.type == "organization"


def test_agent_discriminated_union():
    class A(Identifiable):
        agent: AgentUnion | None = None

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
    assert isinstance(res.agent, Organization)

    res = A.model_validate(
        {
            "id": MOCK_UUID,
            "agent": {
                "type": "person",
                "pref_label": "foo",
                "given_name": "John",
                "family_name": "Smith",
            },
        }
    )
    assert res.id == MOCK_UUID
    assert isinstance(res.agent, Person)
