"""The free space the instance asks for, read from its environment and kept in its settings."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings, read_settings
from settings_support import AGENT_HOME, BASE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, 5),
        ("", 5),
        ("   ", 5),
        ("1", 1),
        (" 12 ", 12),
        ("0", None),
        ("-1", None),
        ("2.5", None),
        ("five", None),
        ("٣", None),
    ],
    ids=[
        "unset",
        "empty",
        "blank",
        "one",
        "padded",
        "zero",
        "negative",
        "decimal",
        "word",
        "arabic",
    ],
)
def test_the_minimum_free_space_is_read_or_refused(value: str | None, expected: int | None) -> None:
    environ = dict(BASE) if value is None else {**BASE, "FACTORY_MIN_FREE_GB": value}

    if expected is not None:
        assert read_settings(environ).min_free_gb == expected
        return
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ)
    assert raised.value.variable == "FACTORY_MIN_FREE_GB"
    assert raised.value.fault == "is not a whole number of gigabytes of at least 1"


@pytest.mark.parametrize(
    ("fields", "expected"),
    [({}, 5), ({"min_free_gb": 1}, 1), ({"min_free_gb": 0}, None)],
    ids=["default", "one", "zero"],
)
def test_the_settings_keep_a_minimum_free_space_of_at_least_one(
    fields: dict[str, int], expected: int | None
) -> None:
    model: type[BaseModel] = InstanceSettings

    if expected is None:
        with pytest.raises(ValidationError):
            model(
                repository_url="/srv/project.git",
                instance="factory-1",
                agent_home=AGENT_HOME,
                **fields,
            )
        return
    settings = model(
        repository_url="/srv/project.git", instance="factory-1", agent_home=AGENT_HOME, **fields
    )
    assert isinstance(settings, InstanceSettings)
    assert settings.min_free_gb == expected
