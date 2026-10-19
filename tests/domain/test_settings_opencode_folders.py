"""The setting that names the opencode build's own folders in the agent's home."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import OPENCODE_FOLDERS_VARIABLE, read_settings
from settings_support import BASE

INSIDE = "which is not a folder inside the agent's home"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, [], id="unset"),
        pytest.param(" ", [], id="blank"),
        pytest.param(
            ".config/sso-opencode, .local/share/sso",
            [".config/sso-opencode", ".local/share/sso"],
            id="two",
        ),
    ],
)
def test_the_opencode_folders_are_the_named_ones_in_their_order(
    value: str | None, expected: list[str]
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[OPENCODE_FOLDERS_VARIABLE] = value

    assert OPENCODE_FOLDERS_VARIABLE == "FACTORY_OPENCODE_FOLDERS"
    assert read_settings(environ).opencode_folders == expected


@pytest.mark.parametrize(
    ("value", "entry"),
    [
        pytest.param("/abs", "/abs", id="absolute"),
        pytest.param("../up", "../up", id="parent"),
        pytest.param("a/../b", "a/../b", id="inner-parent"),
        pytest.param("a//b", "a//b", id="empty-segment"),
        pytest.param(".", ".", id="dot"),
        pytest.param("a,", "", id="empty-entry"),
    ],
)
def test_an_opencode_folder_outside_the_agent_s_home_is_refused_naming_it(
    value: str, entry: str
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, OPENCODE_FOLDERS_VARIABLE: value})

    assert raised.value.variable == "FACTORY_OPENCODE_FOLDERS"
    assert raised.value.fault == f"holds {entry}, {INSIDE}"
