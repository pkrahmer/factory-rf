"""Tests of the bearer token and the wait between two refreshes."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from factory.domain.tokens import Token, refresh_wait


@pytest.mark.parametrize(
    ("expires_in", "seconds"),
    [
        pytest.param(3599, 600, id="measured-life"),
        pytest.param(7200, 600, id="long-life"),
        pytest.param(1200, 600, id="twice-the-interval"),
        pytest.param(1000, 500, id="half-a-short-life"),
        pytest.param(40, 30, id="floor"),
        pytest.param(10, 30, id="under-the-floor"),
    ],
)
def test_the_wait_is_the_interval_or_half_a_short_life_and_at_least_the_floor(
    expires_in: int, seconds: int
) -> None:
    assert refresh_wait(Token(value="t", expires_in=expires_in)) == timedelta(seconds=seconds)


@pytest.mark.parametrize(
    ("value", "expires_in", "accepted"),
    [
        pytest.param("", 3599, False, id="blank-value"),
        pytest.param("a b", 3599, False, id="value-with-space"),
        pytest.param("a\nb", 3599, False, id="value-with-newline"),
        pytest.param("t", 0, False, id="expires-in-0"),
        pytest.param("t", -1, False, id="expires-in-minus-1"),
        pytest.param("t", 1, True, id="expires-in-1"),
    ],
)
def test_a_token_needs_a_value_without_whitespace_and_a_positive_life(
    value: str, expires_in: int, accepted: bool
) -> None:
    if accepted:
        assert Token(value=value, expires_in=expires_in).expires_in == expires_in
    else:
        with pytest.raises(ValidationError):
            Token(value=value, expires_in=expires_in)
