"""The instance's provider limit cool-down and ceiling, read from their two variables."""

from datetime import timedelta

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import (
    PROVIDER_LIMIT_CEILING_VARIABLE,
    PROVIDER_LIMIT_COOLDOWN_VARIABLE,
    read_settings,
)
from settings_support import BASE

COOLDOWN = "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES"
CEILING = "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES"
NOT_MINUTES = "is not a whole number of minutes of at least 1"


def test_the_variables_have_their_names() -> None:
    assert (PROVIDER_LIMIT_COOLDOWN_VARIABLE, PROVIDER_LIMIT_CEILING_VARIABLE) == (
        COOLDOWN,
        CEILING,
    )


@pytest.mark.parametrize(
    ("variables", "cooldown", "ceiling"),
    [
        pytest.param({}, 10, 120, id="unset"),
        pytest.param({COOLDOWN: "", CEILING: ""}, 10, 120, id="empty"),
        pytest.param({COOLDOWN: "  ", CEILING: "  "}, 10, 120, id="blank"),
        pytest.param({COOLDOWN: "5", CEILING: "60"}, 5, 60, id="five-and-sixty"),
        pytest.param({COOLDOWN: "1", CEILING: "1"}, 1, 1, id="one-and-one"),
        pytest.param({COOLDOWN: "30", CEILING: "30"}, 30, 30, id="ceiling-equals-cooldown"),
    ],
)
def test_the_cooldown_and_ceiling_are_read_in_minutes(
    variables: dict[str, str], cooldown: int, ceiling: int
) -> None:
    limit = read_settings({**BASE, **variables}).provider_limit

    assert limit.cooldown == timedelta(minutes=cooldown)
    assert limit.ceiling == timedelta(minutes=ceiling)


@pytest.mark.parametrize("variable", [COOLDOWN, CEILING])
@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5"])
def test_a_value_that_is_not_whole_minutes_of_at_least_one_is_refused(
    variable: str, value: str
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, variable: value})

    assert raised.value.variable == variable
    assert NOT_MINUTES in raised.value.fault


def test_a_ceiling_below_the_cooldown_is_refused_naming_the_ceiling() -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, COOLDOWN: "30", CEILING: "20"})

    assert raised.value.variable == CEILING
    assert "is shorter than the cool-down" in raised.value.fault
