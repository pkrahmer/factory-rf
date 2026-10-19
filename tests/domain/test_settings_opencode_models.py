"""The setting that maps the agent files' model aliases to opencode's models."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import OPENCODE_MODELS_VARIABLE, read_settings

BASE = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}
SHAPE = "which is not <alias>=<provider>/<model>"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "opus=anthropic/claude-opus-5-5, sonnet = anthropic/claude-sonnet-5-5",
            {"opus": "anthropic/claude-opus-5-5", "sonnet": "anthropic/claude-sonnet-5-5"},
            id="two",
        ),
        pytest.param(
            "opus=openrouter/anthropic/claude-opus-5-5",
            {"opus": "openrouter/anthropic/claude-opus-5-5"},
            id="model-with-slashes",
        ),
        pytest.param(None, {}, id="unset"),
        pytest.param(" ", {}, id="blank"),
    ],
)
def test_the_opencode_models_map_each_alias_in_their_order(
    value: str | None, expected: dict[str, str]
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[OPENCODE_MODELS_VARIABLE] = value

    models = read_settings(environ).opencode_models

    assert OPENCODE_MODELS_VARIABLE == "FACTORY_OPENCODE_MODELS"
    assert models == expected
    assert list(models) == list(expected)


@pytest.mark.parametrize(
    ("value", "fault"),
    [
        pytest.param("opus", f"holds opus, {SHAPE}", id="no-equals"),
        pytest.param("=anthropic/x", f"holds =anthropic/x, {SHAPE}", id="empty-alias"),
        pytest.param("opus=anthropic", f"holds opus=anthropic, {SHAPE}", id="no-slash"),
        pytest.param("opus=/x", f"holds opus=/x, {SHAPE}", id="empty-provider"),
        pytest.param("opus=anthropic/", f"holds opus=anthropic/, {SHAPE}", id="empty-model"),
        pytest.param("opus=a/b,opus=c/d", "names opus twice", id="alias-twice"),
    ],
)
def test_a_malformed_opencode_models_entry_is_refused_naming_it(value: str, fault: str) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, OPENCODE_MODELS_VARIABLE: value})

    assert raised.value.variable == "FACTORY_OPENCODE_MODELS"
    assert raised.value.fault == fault
