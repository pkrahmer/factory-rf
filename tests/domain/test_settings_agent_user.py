"""The operating-system user the agents run as, read from the environment."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import AGENT_USER_VARIABLE, InstanceSettings, read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"FACTORY_AGENT_USER": "agent"}, "agent"),
        ({}, None),
        ({"FACTORY_AGENT_USER": ""}, None),
        ({"FACTORY_AGENT_USER": "   "}, None),
    ],
    ids=["set", "missing", "empty", "blank"],
)
def test_the_agent_user_comes_from_its_variable_or_is_none(
    variables: dict[str, str], expected: str | None
) -> None:
    assert read_settings({**BASE, **variables}).agent_user == expected


@pytest.mark.parametrize("value", ["Agent", "1x"], ids=["capital", "leading-digit"])
def test_an_agent_user_that_is_no_name_is_refused_naming_its_variable(value: str) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, "FACTORY_AGENT_USER": value})

    assert raised.value.variable == "FACTORY_AGENT_USER"
    assert raised.value.variable == AGENT_USER_VARIABLE


@pytest.mark.parametrize(
    ("value", "accepted"),
    [("agent", True), (None, True), ("Agent", False)],
    ids=["name", "none", "capital"],
)
def test_settings_built_directly_accept_only_a_name_as_agent_user(
    value: str | None, *, accepted: bool
) -> None:
    model: type[BaseModel] = InstanceSettings

    if accepted:
        settings = model(repository_url="/srv/project.git", instance="factory-1", agent_user=value)
        assert isinstance(settings, InstanceSettings)
        assert settings.agent_user == value
    else:
        with pytest.raises(ValidationError):
            model(repository_url="/srv/project.git", instance="factory-1", agent_user=value)
