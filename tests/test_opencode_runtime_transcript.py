"""opencode's transcript: the event stream of a session's last run, one event per line."""

from pathlib import Path

import pytest

from claude_stand_in import Step
from opencode_stand_in import (
    REPLY,
    REPLY_EVENTS,
    RESUME_REPLY,
    SESSION,
    budget_steps,
    opencode_request,
    over_budget,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
)

OTHER_SESSION = "ses_other"
SECOND_EVENTS = stdout(
    step_start(20_000), text(result_text("doing", "The second run."), 20_100), step_finish(20_500)
)
SECOND_REPLY = Step(stdout=SECOND_EVENTS)
FIRST_CALL_EVENTS = stdout(*budget_steps(0.4, 0.4, 0.21))


@pytest.mark.parametrize(
    ("steps", "runs", "asked", "expected"),
    [
        pytest.param([REPLY], 1, SESSION, REPLY_EVENTS, id="its-run"),
        pytest.param([REPLY], 1, OTHER_SESSION, None, id="never-seen"),
        pytest.param(
            [over_budget(), RESUME_REPLY],
            1,
            SESSION,
            FIRST_CALL_EVENTS + RESUME_REPLY.stdout,
            id="resumed-within-the-run",
        ),
        pytest.param([REPLY, SECOND_REPLY], 2, SESSION, SECOND_EVENTS, id="second-run"),
    ],
)
def test_a_session_transcript_is_the_event_stream_of_its_last_run(
    tmp_path: Path, *, steps: list[Step], runs: int, asked: str, expected: str | None
) -> None:
    runtime = stand_in_runtime(tmp_path, steps)
    for _ in range(runs):
        assert runtime.run(opencode_request(tmp_path / "work")).session == SESSION

    transcript = runtime.read_transcript(tmp_path / "home", asked)

    if expected is None:
        assert transcript is None
    else:
        assert transcript is not None
        assert transcript.extension == "jsonl"
        assert transcript.content == expected.encode("utf-8")
