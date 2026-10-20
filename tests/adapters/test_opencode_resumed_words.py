"""A resumed opencode call is the first call's words, then `--session` and the prompt."""

from collections.abc import Callable
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    REPLY,
    RESUME_REPLY,
    SESSION,
    WAIT_SECONDS,
    opencode_request,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
)
from factory.adapters.agent_launch import FINISH_MESSAGE
from factory.domain.agent_runs import AgentRunRequest

FIRST_WORDS = [
    "run",
    "--format",
    "json",
    "--auto",
    "--model",
    "anthropic/claude-sonnet-5-5",
    "--agent",
    "factory-coder",
]
OVER_BUDGET = Step(
    stdout_before_wait=stdout(step_start(1000), step_finish(2000, cost=1.2)),
    wait_seconds=WAIT_SECONDS,
)


def _budget_stop(work: Path) -> tuple[list[Step], AgentRunRequest]:
    return [OVER_BUDGET, RESUME_REPLY], opencode_request(work)


def _resume_session(work: Path) -> tuple[list[Step], AgentRunRequest]:
    request = opencode_request(work).model_copy(
        update={"resume_session": "ses_r", "prompt": "Go on."}
    )
    return [REPLY], request


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(
            _budget_stop, [*FIRST_WORDS, "--session", SESSION, FINISH_MESSAGE], id="budget-resume"
        ),
        pytest.param(
            _resume_session, [*FIRST_WORDS, "--session", "ses_r", "Go on."], id="resume-session"
        ),
    ],
)
def test_a_resumed_call_keeps_every_word_of_the_first_before_its_session(
    tmp_path: Path,
    setup: Callable[[Path], tuple[list[Step], AgentRunRequest]],
    expected: list[str],
) -> None:
    steps, request = setup(tmp_path / "work")
    runtime = stand_in_runtime(tmp_path, steps)

    runtime.run(request)

    assert read_calls(tmp_path / "bin")[-1].arguments == expected
