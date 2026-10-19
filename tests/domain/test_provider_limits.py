"""A provider's spend limit: the pattern that recognizes it and the wait a message names."""

from datetime import timedelta

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.provider_limits import ProviderLimit, limit_in_text, named_wait

LIMIT: type[BaseModel] = ProviderLimit


@pytest.mark.parametrize(
    ("text", "limit", "found"),
    [
        pytest.param('API Error: 428 {"message": "limit"}', ProviderLimit(), True, id="api-error"),
        pytest.param("status (428)", ProviderLimit(), True, id="parenthesised"),
        pytest.param("HTTP 428:", ProviderLimit(), True, id="http"),
        pytest.param("14280 tokens", ProviderLimit(), False, id="inside-a-longer-number"),
        pytest.param("4280", ProviderLimit(), False, id="prefix-of-a-number"),
        pytest.param("", ProviderLimit(), False, id="empty"),
        pytest.param("rate limited", ProviderLimit(), False, id="no-status"),
        pytest.param(
            "the spend limit is reached",
            ProviderLimit(message="spend limit"),
            True,
            id="message-without-status",
        ),
    ],
)
def test_the_limit_is_in_a_text_by_its_whole_status_or_its_message(
    text: str, limit: ProviderLimit, *, found: bool
) -> None:
    assert limit_in_text(text, limit) is found


@pytest.mark.parametrize(
    ("fields", "accepted"),
    [
        pytest.param({"status": 99}, False, id="status-99"),
        pytest.param({"status": 100}, True, id="status-100"),
        pytest.param({"status": 599}, True, id="status-599"),
        pytest.param({"status": 600}, False, id="status-600"),
        pytest.param({"message": "("}, False, id="message-not-a-pattern"),
    ],
)
def test_a_limit_needs_an_http_status_and_a_message_that_compiles(
    fields: dict[str, object], *, accepted: bool
) -> None:
    if accepted:
        limit = LIMIT(**fields)
        assert isinstance(limit, ProviderLimit)
        assert limit.status == fields["status"]
        return
    with pytest.raises(ValidationError):
        LIMIT(**fields)


MINUTES_7 = timedelta(seconds=420)
SECONDS_120 = timedelta(seconds=120)


@pytest.mark.parametrize(
    ("text", "wait"),
    [
        ("try again in 7 minutes", MINUTES_7),
        ("in 7 min", MINUTES_7),
        ("in 7 m", MINUTES_7),
        ("retry after 120 seconds", SECONDS_120),
        ("in 120 s", SECONDS_120),
        ("in 120 sec", SECONDS_120),
        ("Retry-After: 120", SECONDS_120),
        ("retry-after 120", SECONDS_120),
        ("in 999999", timedelta(seconds=999999)),
        ("retry-after 999999", timedelta(seconds=999999)),
        ("in 2 h", timedelta(hours=2)),
        ("in 2 hours", timedelta(hours=2)),
        ("in 1 hour", timedelta(hours=1)),
        ("in 45", timedelta(seconds=45)),
        ("retry after 30 seconds, or else in 7 minutes", timedelta(seconds=30)),
        ("try again in 7 minutes; Retry-After: 120", MINUTES_7),
        ("in 0 minutes", None),
        ("in 1234567", None),
        ("limit reached", None),
        ("in seven minutes", None),
    ],
)
def test_the_named_wait_is_the_first_one_the_text_names(text: str, wait: timedelta | None) -> None:
    assert named_wait(text) == wait
