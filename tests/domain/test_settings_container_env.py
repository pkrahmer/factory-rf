"""The settings that name the containers' extra environment and the operator's CA bundle."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import (
    CA_BUNDLE_VARIABLE,
    CONTAINER_ENV_VARIABLE,
    InstanceSettings,
    read_settings,
)
from settings_support import BASE

_NOT_A_NAME = "which is not a variable name"
_SET_BY_FACTORY = "which the factory sets itself"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, (), id="unset"),
        pytest.param("  ", (), id="blank"),
        pytest.param(" , ", (), id="blank-parts"),
        pytest.param("HTTPS_PROXY,NO_PROXY", ("HTTPS_PROXY", "NO_PROXY"), id="two-in-order"),
        pytest.param("A,A", "names A twice", id="twice"),
        pytest.param("1X", f"holds 1X, {_NOT_A_NAME}", id="leading-digit"),
        pytest.param("A-B", f"holds A-B, {_NOT_A_NAME}", id="dash"),
        pytest.param("HOME", f"holds HOME, {_SET_BY_FACTORY}", id="home"),
        pytest.param(
            "ANTHROPIC_API_KEY", f"holds ANTHROPIC_API_KEY, {_SET_BY_FACTORY}", id="api-key"
        ),
        pytest.param(
            "CLAUDE_CODE_OAUTH_TOKEN",
            f"holds CLAUDE_CODE_OAUTH_TOKEN, {_SET_BY_FACTORY}",
            id="oauth-token",
        ),
        pytest.param(
            "OPENCODE_CONFIG", f"holds OPENCODE_CONFIG, {_SET_BY_FACTORY}", id="opencode-config"
        ),
        pytest.param("GIT_ASKPASS", f"holds GIT_ASKPASS, {_SET_BY_FACTORY}", id="askpass"),
        pytest.param(
            "FACTORY_TOKEN_FILE",
            f"holds FACTORY_TOKEN_FILE, {_SET_BY_FACTORY}",
            id="factory-prefix",
        ),
        pytest.param("FACTORYX", ("FACTORYX",), id="factory-without-underscore"),
        pytest.param("http_proxy,_X", ("http_proxy", "_X"), id="lower-case-and-underscore"),
    ],
)
def test_the_container_env_setting_is_read_as_a_list_of_names(
    value: str | None, expected: tuple[str, ...] | str
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[CONTAINER_ENV_VARIABLE] = value

    assert CONTAINER_ENV_VARIABLE == "FACTORY_CONTAINER_ENV"
    if isinstance(expected, tuple):
        assert read_settings(environ).container_env == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_CONTAINER_ENV"
    assert raised.value.fault == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="unset"),
        pytest.param("  ", None, id="blank"),
        pytest.param("/etc/ca.pem", Path("/etc/ca.pem"), id="absolute"),
        pytest.param("ca.pem", "is not an absolute path", id="relative"),
    ],
)
def test_the_ca_bundle_setting_is_read_as_an_absolute_path(
    value: str | None, expected: Path | str | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[CA_BUNDLE_VARIABLE] = value

    assert CA_BUNDLE_VARIABLE == "FACTORY_CA_BUNDLE"
    if not isinstance(expected, str):
        assert read_settings(environ).ca_bundle == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_CA_BUNDLE"
    assert raised.value.fault == expected


@pytest.mark.parametrize(
    ("path", "accepted"),
    [
        pytest.param(Path("/etc/ca.pem"), True, id="absolute"),
        pytest.param(Path("ca.pem"), False, id="relative"),
    ],
)
def test_the_settings_model_refuses_a_relative_ca_bundle(path: Path, accepted: bool) -> None:
    model: type[BaseModel] = InstanceSettings
    url = BASE["FACTORY_REPOSITORY_URL"]

    if accepted:
        assert (
            InstanceSettings(repository_url=url, instance="f-1", ca_bundle=path).ca_bundle == path
        )
        return
    with pytest.raises(ValidationError):
        model(repository_url=url, instance="f-1", ca_bundle=path)
