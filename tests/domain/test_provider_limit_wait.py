"""The provider limit's cool-down and ceiling: their defaults and their bounds."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from factory.domain.provider_limits import DEFAULT_CEILING, DEFAULT_COOLDOWN, ProviderLimit


def test_the_limit_waits_ten_minutes_up_to_two_hours_by_default() -> None:
    limit = ProviderLimit()

    assert timedelta(minutes=10) == DEFAULT_COOLDOWN
    assert timedelta(minutes=120) == DEFAULT_CEILING
    assert (limit.cooldown, limit.ceiling) == (DEFAULT_COOLDOWN, DEFAULT_CEILING)


@pytest.mark.parametrize(
    ("cooldown", "ceiling", "fault"),
    [
        pytest.param(timedelta(minutes=1), timedelta(minutes=1), None, id="one-minute-each"),
        pytest.param(timedelta(seconds=59), timedelta(minutes=1), "", id="cooldown-59-seconds"),
        pytest.param(
            timedelta(minutes=10),
            timedelta(minutes=10) - timedelta(seconds=1),
            "the ceiling is shorter than the cool-down",
            id="ceiling-below-cooldown",
        ),
    ],
)
def test_the_cooldown_is_a_minute_or_more_and_the_ceiling_no_shorter(
    cooldown: timedelta, ceiling: timedelta, fault: str | None
) -> None:
    if fault is None:
        limit = ProviderLimit(cooldown=cooldown, ceiling=ceiling)
        assert (limit.cooldown, limit.ceiling) == (cooldown, ceiling)
        return
    with pytest.raises(ValidationError) as raised:
        ProviderLimit(cooldown=cooldown, ceiling=ceiling)
    assert fault in str(raised.value)
