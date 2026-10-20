"""A resume that its time limit ended keeps the first call's session when it has none."""

from datetime import timedelta

import pytest

from factory.domain.agent_runs import AgentRunResult, resumed_result

FIRST = AgentRunResult(
    end_reason="provider_limit",
    duration=timedelta(seconds=60),
    session="ses_a",
    limit_wait=timedelta(seconds=420),
)


@pytest.mark.parametrize(
    ("session", "expected"),
    [
        pytest.param(None, "ses_a", id="no-second-session"),
        pytest.param("ses_b", "ses_b", id="second-session"),
    ],
)
def test_a_resume_ended_by_its_time_limit_keeps_a_session_and_sums_durations(
    session: str | None, expected: str
) -> None:
    second = AgentRunResult(
        end_reason="time_limit", duration=timedelta(seconds=60), session=session
    )

    result = resumed_result(FIRST, second)

    assert result.session == expected
    assert result.end_reason == "time_limit"
    assert result.duration == timedelta(seconds=120)
