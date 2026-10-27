"""The opencode runtime resumes the session a request names and reports the session it used."""

from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    SESSION,
    opencode_request,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
)
from opencode_resume_support import WAIT_SECONDS
from time_limits import ROOMY_LIMIT

OTHER_SESSION = "ses_b"
# The first event names another session than the later ones, so the first one is told apart.
EVENTS = stdout(
    step_start().replace(f'"{SESSION}"', f'"{OTHER_SESSION}"'),
    text(result_text()),
    step_finish(),
)
DEFAULT_LIMIT = timedelta(seconds=30)


@pytest.mark.parametrize(
    ("resume_session", "step", "time_limit", "session"),
    [
        pytest.param(
            "ses_a", Step(stdout=EVENTS), DEFAULT_LIMIT, OTHER_SESSION, id="resumed-with-events"
        ),
        pytest.param("ses_a", Step(), DEFAULT_LIMIT, "ses_a", id="resumed-without-events"),
        pytest.param(None, Step(stdout=EVENTS), DEFAULT_LIMIT, OTHER_SESSION, id="new-with-events"),
        pytest.param(None, Step(), DEFAULT_LIMIT, None, id="new-without-events"),
        pytest.param(
            None,
            Step(stdout_before_wait=EVENTS, wait_seconds=WAIT_SECONDS),
            ROOMY_LIMIT,
            OTHER_SESSION,
            id="timed-out-with-events",
        ),
        pytest.param(
            "ses_a",
            Step(wait_seconds=WAIT_SECONDS),
            ROOMY_LIMIT,
            "ses_a",
            id="timed-out-resumed-without-events",
        ),
    ],
)
def test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events(
    tmp_path: Path,
    resume_session: str | None,
    step: Step,
    time_limit: timedelta,
    session: str | None,
) -> None:
    runtime = stand_in_runtime(tmp_path, [step])
    request = opencode_request(tmp_path / "work", time_limit=time_limit).model_copy(
        update={"resume_session": resume_session}
    )

    result = runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    if resume_session is None:
        assert "--session" not in call.arguments
    else:
        assert call.arguments[-3:] == ["--session", resume_session, request.prompt]
    assert result.session == session
    assert (result.end_reason == "time_limit") == (time_limit == ROOMY_LIMIT)
