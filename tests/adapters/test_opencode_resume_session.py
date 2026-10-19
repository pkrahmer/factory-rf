"""The opencode runtime resumes the session a request names and reports the session it used."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    SESSION,
    opencode_request,
    result_text,
    stdout,
    step_finish,
    step_start,
    text,
)
from adapters.test_opencode_runtime import _runtime

OTHER_SESSION = "ses_b"
# The first event names another session than the later ones, so the first one is told apart.
EVENTS = stdout(
    step_start().replace(f'"{SESSION}"', f'"{OTHER_SESSION}"'),
    text(result_text()),
    step_finish(),
)


@pytest.mark.parametrize(
    ("resume_session", "events", "session"),
    [
        pytest.param("ses_a", EVENTS, OTHER_SESSION, id="resumed-with-events"),
        pytest.param("ses_a", "", "ses_a", id="resumed-without-events"),
        pytest.param(None, EVENTS, OTHER_SESSION, id="new-with-events"),
        pytest.param(None, "", None, id="new-without-events"),
    ],
)
def test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events(
    tmp_path: Path, resume_session: str | None, events: str, session: str | None
) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=events)])
    request = opencode_request(tmp_path / "work").model_copy(
        update={"resume_session": resume_session}
    )

    result = runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    if resume_session is None:
        assert "--session" not in call.arguments
    else:
        assert call.arguments[-3:] == ["--session", resume_session, request.prompt]
    assert result.session == session
