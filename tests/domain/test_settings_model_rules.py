"""The settings model refuses the agent home and container names that the reading refuses."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

import factory
from factory.domain import settings
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import CONTAINER_ENV_VARIABLE, InstanceSettings, read_settings
from settings_support import BASE

REQUIRED: dict[str, object] = {"repository_url": "/srv/project.git", "instance": "factory-1"}
_AGENTS = "/srv/agents"
_SET_BY_FACTORY = "which the factory sets itself"
_NOT_A_NAME = "which is not a variable name"


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        pytest.param({}, "agent_home", id="missing"),
        pytest.param({"agent_home": "agents"}, "is not an absolute path", id="relative"),
        pytest.param({"agent_home": _AGENTS}, Path(_AGENTS), id="absolute"),
    ],
)
def test_the_settings_model_requires_an_absolute_agent_home(
    fields: dict[str, object], expected: str | Path
) -> None:
    model: type[BaseModel] = InstanceSettings

    if isinstance(expected, Path):
        built = model(**REQUIRED, **fields)
        assert isinstance(built, InstanceSettings)
        assert built.agent_home == expected
        return
    with pytest.raises(ValidationError) as raised:
        model(**REQUIRED, **fields)
    assert expected in str(raised.value)


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        pytest.param((), (), id="none"),
        pytest.param(("HTTPS_PROXY",), ("HTTPS_PROXY",), id="one"),
        pytest.param(
            ("HTTPS_PROXY", "NO_PROXY", "_X1"), ("HTTPS_PROXY", "NO_PROXY", "_X1"), id="three"
        ),
        pytest.param(("HOME",), f"holds HOME, {_SET_BY_FACTORY}", id="home"),
        pytest.param(
            ("ANTHROPIC_API_KEY",), f"holds ANTHROPIC_API_KEY, {_SET_BY_FACTORY}", id="api-key"
        ),
        pytest.param(("FACTORY_X",), f"holds FACTORY_X, {_SET_BY_FACTORY}", id="factory-prefix"),
        pytest.param(("1A",), f"holds 1A, {_NOT_A_NAME}", id="leading-digit"),
        pytest.param(("A-B",), f"holds A-B, {_NOT_A_NAME}", id="dash"),
        pytest.param(("A", "A"), "names A twice", id="twice"),
    ],
)
def test_the_settings_model_checks_the_container_env_names(
    names: tuple[str, ...], expected: tuple[str, ...] | str
) -> None:
    model: type[BaseModel] = InstanceSettings

    if isinstance(expected, tuple):
        built = model(**REQUIRED, agent_home=_AGENTS, container_env=names)
        assert isinstance(built, InstanceSettings)
        assert built.container_env == expected
        return
    with pytest.raises(ValidationError) as raised:
        model(**REQUIRED, agent_home=_AGENTS, container_env=names)
    assert expected in str(raised.value)


@pytest.mark.parametrize(
    ("value", "fault"),
    [
        pytest.param("HOME", f"holds HOME, {_SET_BY_FACTORY}", id="home"),
        pytest.param("1A", f"holds 1A, {_NOT_A_NAME}", id="not-a-name"),
        pytest.param("A,A", "names A twice", id="twice"),
    ],
)
def test_the_reading_names_the_container_env_variable_for_a_refused_name(
    value: str, fault: str
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, CONTAINER_ENV_VARIABLE: value})

    assert raised.value.variable == CONTAINER_ENV_VARIABLE
    assert raised.value.fault == fault


def _sources_naming_the_old_home() -> list[Path]:
    package = Path(factory.__file__).parent
    return [
        path
        for path in sorted(package.rglob("*.py"))
        if "/home/agent" in path.read_text(encoding="utf-8")
    ]


@pytest.mark.parametrize(
    ("remainder", "expected"),
    [
        pytest.param(lambda: hasattr(settings, "AGENT_HOME_DEFAULT"), False, id="constant"),
        pytest.param(_sources_naming_the_old_home, [], id="string"),
    ],
)
def test_the_old_agent_home_default_is_gone(
    remainder: Callable[[], object], expected: object
) -> None:
    assert remainder() == expected
