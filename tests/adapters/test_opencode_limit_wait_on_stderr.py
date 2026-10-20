"""A limit line on the opencode runtime's standard error gives the run the wait it names."""

import time
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step
from adapters.opencode_stand_in import (
    BOUND_SECONDS,
    REPLY,
    RESUME_REPLY,
    WAITING,
    opencode_request,
    stand_in_runtime,
)


@pytest.mark.parametrize(
    ("line", "first", "end_reason", "limit_wait"),
    [
        pytest.param(
            "HTTP 428 spend limit reached, retry after 120 seconds",
            WAITING,
            "provider_limit",
            timedelta(seconds=120),
            id="seconds",
        ),
        pytest.param(
            "HTTP 428 Precondition Required: try again in 7 minutes",
            WAITING,
            "provider_limit",
            timedelta(seconds=420),
            id="minutes",
        ),
        pytest.param(
            "HTTP 428 Precondition Required", WAITING, "provider_limit", None, id="no-wait"
        ),
        pytest.param(
            "HTTP 500 Internal Server Error, retry after 120 seconds",
            REPLY,
            "completed",
            None,
            id="500",
        ),
        pytest.param(
            "HTTP 4281 Precondition Required, retry after 120 seconds",
            REPLY,
            "completed",
            None,
            id="4281",
        ),
    ],
)
def test_a_limit_line_on_standard_error_gives_the_wait_it_names(
    tmp_path: Path, line: str, first: Step, end_reason: str, limit_wait: timedelta | None
) -> None:
    runtime = stand_in_runtime(tmp_path, [first, RESUME_REPLY], stderr_first=line)

    started = time.monotonic()
    result = runtime.run(opencode_request(tmp_path / "work"))

    assert time.monotonic() - started < BOUND_SECONDS
    assert result.end_reason == end_reason
    assert result.limit_wait == limit_wait
