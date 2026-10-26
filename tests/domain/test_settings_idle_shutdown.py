"""The idle shutdown's limit, read from the instance's environment."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, 0, id="unset"),
        pytest.param("", 0, id="empty"),
        pytest.param("  ", 0, id="blank"),
        pytest.param("0", 0, id="zero"),
        pytest.param("1", 1, id="one"),
        pytest.param("30", 30, id="thirty"),
        pytest.param("100000", 100000, id="no-upper-limit"),
        pytest.param("-1", None, id="negative"),
        pytest.param("x", None, id="word"),
        pytest.param("1.5", None, id="decimal"),
        pytest.param("٣", None, id="arabic"),
    ],
)
def test_the_idle_shutdown_minutes_are_read_or_refused(
    value: str | None, expected: int | None
) -> None:
    environ = dict(BASE) if value is None else {**BASE, "FACTORY_IDLE_SHUTDOWN_MINUTES": value}

    if expected is not None:
        assert read_settings(environ).idle_shutdown_minutes == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_IDLE_SHUTDOWN_MINUTES"
    assert raised.value.fault == "is not a whole number of minutes"
