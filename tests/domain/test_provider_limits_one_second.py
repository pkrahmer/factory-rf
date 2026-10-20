"""A named wait of one second is a wait, one of zero seconds is none."""

from datetime import timedelta

import pytest

from factory.domain.provider_limits import named_wait


@pytest.mark.parametrize(
    ("text", "wait"),
    [
        pytest.param("in 1 second", timedelta(seconds=1), id="in-1-second"),
        pytest.param("Retry-After: 1", timedelta(seconds=1), id="retry-after-1"),
        pytest.param("in 0 seconds", None, id="in-0-seconds"),
        pytest.param("Retry-After: 0", None, id="retry-after-0"),
    ],
)
def test_a_named_wait_of_one_second_is_a_wait_and_of_zero_none(
    text: str, wait: timedelta | None
) -> None:
    assert named_wait(text) == wait
