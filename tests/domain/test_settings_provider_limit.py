"""The instance's provider limit, read from its two variables."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings

BASE = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, 428, id="unset"),
        pytest.param("", 428, id="empty"),
        pytest.param("  ", 428, id="blank"),
        pytest.param("429", 429, id="429"),
        pytest.param("100", 100, id="100"),
        pytest.param("599", 599, id="599"),
        pytest.param("abc", None, id="abc"),
        pytest.param("99", None, id="99"),
        pytest.param("600", None, id="600"),
        pytest.param("٤٢٨", None, id="arabic-indic-digits"),
    ],
)
def test_the_limit_status_is_read_or_refused(value: str | None, expected: int | None) -> None:
    environ = dict(BASE) if value is None else {**BASE, "FACTORY_PROVIDER_LIMIT_STATUS": value}

    if expected is not None:
        assert read_settings(environ).provider_limit.status == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_PROVIDER_LIMIT_STATUS"
    assert raised.value.fault == "is not an HTTP status from 100 to 599"


@pytest.mark.parametrize(
    ("value", "expected", "refused"),
    [
        pytest.param(None, None, False, id="unset"),
        pytest.param("", None, False, id="empty"),
        pytest.param("  ", None, False, id="blank"),
        pytest.param("spend limit", "spend limit", False, id="pattern"),
        pytest.param("(", None, True, id="not-a-pattern"),
    ],
)
def test_the_limit_message_is_read_or_refused(
    value: str | None, expected: str | None, *, refused: bool
) -> None:
    environ = dict(BASE) if value is None else {**BASE, "FACTORY_PROVIDER_LIMIT_MESSAGE": value}

    if not refused:
        assert read_settings(environ).provider_limit.message == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_PROVIDER_LIMIT_MESSAGE"
    assert raised.value.fault.startswith("is not a regular expression: ")
