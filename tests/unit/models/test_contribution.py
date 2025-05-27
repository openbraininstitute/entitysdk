import pytest

from entitysdk.models import agent
from entitysdk.models import contribution as test_module


@pytest.fixture
def role():
    return test_module.Role(name="foo", role_id="1")


def test_role(role):
    assert role.name == "foo"
    assert role.role_id == "1"


def test_contribution(role):
    person = agent.Person(type="person", given_name="foo", family_name="bar", pref_label="test")

    res = test_module.Contribution(
        agent=person,
        role=role,
    )

    assert res.agent == person
    assert res.role == role

    organization = agent.Organization(
        type="organization", pref_label="test", alternative_name="test"
    )

    res = test_module.Contribution(
        agent=organization,
        role=role,
    )

    assert res.agent == organization
    assert res.role == role

    res = test_module.Contribution.model_validate(
        {
            "agent": person.model_dump(mode="json"),
            "role": role.model_dump(mode="json"),
        }
    )
    assert res.agent == person
    assert res.role == role

    res = test_module.Contribution.model_validate(
        {
            "agent": organization.model_dump(mode="json"),
            "role": role.model_dump(mode="json"),
        }
    )
    assert res.agent == organization
    assert res.role == role
