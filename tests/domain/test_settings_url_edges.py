"""The edges of the repository URL's password rule and the faults an operator reads."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
from settings_support import BASE, raising

URL_VARIABLE = "FACTORY_REPOSITORY_URL"


def _returning(text: str) -> Callable[[Path], str]:
    def read_file(_path: Path) -> str:
        return text

    return read_file


@pytest.mark.parametrize(
    ("url", "accepted"),
    [
        pytest.param("https://github.com/owner/a:b@c/project.git", True, id="colon-and-at-in-path"),
        pytest.param(
            "https://github.com/owner/x://u:" + "p@y.git", True, id="second-scheme-in-path"
        ),
        pytest.param("https://u@x@github.com/owner/project.git", True, id="at-in-user-no-password"),
        pytest.param(
            "https://u@x:" + "y@github.com/owner/project.git", False, id="at-in-user-password"
        ),
    ],
)
def test_the_password_rule_judges_only_the_authority(url: str, accepted: bool) -> None:
    environ = {**BASE, URL_VARIABLE: url}

    if accepted:
        assert read_settings(environ).repository_url == url
    else:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert raised.value.variable == URL_VARIABLE
        assert raised.value.fault == "holds a password; use the token file"


@pytest.mark.parametrize(
    ("added", "read_file", "variable", "fault"),
    [
        pytest.param(
            {URL_VARIABLE: "a/b,c/d"},
            None,
            URL_VARIABLE,
            "names more than one repository",
            id="comma",
        ),
        pytest.param(
            {URL_VARIABLE: "a b"}, None, URL_VARIABLE, "names more than one repository", id="space"
        ),
        pytest.param(
            {URL_VARIABLE: "https://user:" + "example-value" + "@github.com/owner/project.git"},
            None,
            URL_VARIABLE,
            "holds a password; use the token file",
            id="password",
        ),
        pytest.param(
            {"FACTORY_INSTANCE": "Factory-1"},
            None,
            "FACTORY_INSTANCE",
            "is not a name",
            id="instance",
        ),
        pytest.param(
            {"FACTORY_AGENT_USER": "Agent"},
            None,
            "FACTORY_AGENT_USER",
            "is not a name",
            id="agent-user",
        ),
        pytest.param(
            {
                "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES": "30",
                "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES": "20",
            },
            None,
            "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES",
            "is shorter than the cool-down",
            id="ceiling",
        ),
        pytest.param(
            {},
            raising(PermissionError("denied")),
            "FACTORY_IMAGE_ID_FILE",
            "cannot read /opt/factory/image-id: denied",
            id="image-unreadable",
        ),
        pytest.param(
            {},
            _returning("  \n"),
            "FACTORY_IMAGE_ID_FILE",
            "/opt/factory/image-id is empty",
            id="image-empty",
        ),
    ],
)
def test_a_refused_setting_names_its_variable_and_its_fault(
    added: dict[str, str],
    read_file: Callable[[Path], str] | None,
    variable: str,
    fault: str,
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, **added}, read_file)

    assert raised.value.variable == variable
    assert raised.value.fault == fault
    assert str(raised.value) == f"{variable}: {fault}"
