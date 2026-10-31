"""The idle shutdown's action, read from the instance's environment and kept in its settings."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("value", "minutes", "expected"),
    [
        pytest.param(None, None, "poweroff", id="unset"),
        pytest.param("", None, "poweroff", id="empty"),
        pytest.param("  ", None, "poweroff", id="blank"),
        pytest.param("poweroff", None, "poweroff", id="poweroff"),
        pytest.param("exit", None, "exit", id="exit"),
        pytest.param("exit", "0", "exit", id="exit-with-the-shutdown-off"),
        pytest.param("Exit", None, None, id="capitalised"),
        pytest.param("stop", None, None, id="other-word"),
        pytest.param("exit now", None, None, id="exit-and-more"),
    ],
)
def test_the_idle_shutdown_action_is_read_or_refused(
    value: str | None, minutes: str | None, expected: str | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ["FACTORY_IDLE_SHUTDOWN_ACTION"] = value
    if minutes is not None:
        environ["FACTORY_IDLE_SHUTDOWN_MINUTES"] = minutes

    if expected is not None:
        assert read_settings(environ).idle_shutdown_action == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_IDLE_SHUTDOWN_ACTION"
    assert raised.value.fault == "is neither poweroff nor exit"
