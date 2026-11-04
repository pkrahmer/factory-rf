"""The transcript folder and the days its copies are kept, read from the instance's environment."""

from pathlib import Path

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
from settings_support import AGENT_HOME, BASE, CONTAINER

DIR = "FACTORY_TRANSCRIPT_DIR"
DAYS = "FACTORY_TRANSCRIPT_DAYS"
FOLDER = "/srv/transcripts"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="unset"),
        pytest.param("", None, id="empty"),
        pytest.param(FOLDER, Path(FOLDER), id="absolute-outside"),
        pytest.param("transcripts", DIR, id="relative"),
        pytest.param(f"{CONTAINER['FACTORY_WORKSPACE']}/transcripts", DIR, id="in-workspace"),
        pytest.param("/work/checkout/transcripts", DIR, id="in-checkout"),
        pytest.param("/state/transcripts", DIR, id="in-state-directory"),
        pytest.param(f"{AGENT_HOME}/transcripts", DIR, id="in-agent-home"),
    ],
)
def test_the_transcript_folder_is_read_or_refused(
    value: str | None, expected: Path | str | None
) -> None:
    environ = {**BASE, **CONTAINER}
    if value is not None:
        environ[DIR] = value

    if isinstance(expected, str):
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert raised.value.variable == expected
        return
    assert read_settings(environ).transcript_dir == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="unset"),
        pytest.param("", None, id="empty"),
        pytest.param("1", 1, id="one"),
        pytest.param("0", DAYS, id="zero"),
        pytest.param("-1", DAYS, id="negative"),
        pytest.param("x", DAYS, id="word"),
    ],
)
def test_the_transcript_days_are_read_or_refused(
    value: str | None, expected: int | str | None
) -> None:
    environ = {**BASE, **CONTAINER, DIR: FOLDER}
    if value is not None:
        environ[DAYS] = value

    if isinstance(expected, str):
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert raised.value.variable == expected
        return
    assert read_settings(environ).transcript_days == expected
