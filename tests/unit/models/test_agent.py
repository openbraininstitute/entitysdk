from entitysdk.models import agent as test_module


def test_person_entity():
    agent = test_module.Person(
        givenName="foo",
        familyName="bar",
        pref_label="test",
    )
    assert agent.givenName == "foo"
    assert agent.familyName == "bar"
    assert agent.pref_label == "test"


def test_organization_entity():
    organization = test_module.Organization(
        pref_label="foo",
        alternative_name="bar",
    )
    assert organization.pref_label == "foo"
    assert organization.alternative_name == "bar"
