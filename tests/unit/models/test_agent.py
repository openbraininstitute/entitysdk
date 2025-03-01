from entitysdk.models import agent as test_module


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
