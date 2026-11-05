"""Each agent runtime gives a run that died the text it died with, and no other run any."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from claude_resume_support import _budget_reply, _reply
from claude_stand_in import REPLY, Step, claude_request, write_stand_in
from factory.agents.adapters.claude_runtime import ClaudeCodeRuntime
from factory.agents.application.agent_runtime import AgentRuntime
from factory.agents.domain.agent_runs import AgentRunRequest, AgentRunResult, EndReason
from opencode_stand_in import (
    REPLY_EVENTS,
    error,
    opencode_request,
    over_budget,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
)

LIMIT_TEXT = "You've hit your limit · resets 12am"
OWN_ANSWER = "My own answer, which is never quoted."
# The stand-in waits far past this limit; it need not start to be killed.
SHORT_LIMIT = timedelta(seconds=1)
LIMIT_RESULT = "API Error: 428 spend limit reached, try again in 7 minutes"

Start = Callable[[Path, list[Step]], tuple[AgentRuntime, AgentRunRequest]]


def _claude(tmp_path: Path, steps: list[Step]) -> tuple[AgentRuntime, AgentRunRequest]:
    executable = write_stand_in(tmp_path / "bin", steps)
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state")
    return runtime, claude_request(tmp_path)


def _opencode(tmp_path: Path, steps: list[Step]) -> tuple[AgentRuntime, AgentRunRequest]:
    return stand_in_runtime(tmp_path, steps), opencode_request(tmp_path / "work")


def _run(
    start: Start, tmp_path: Path, steps: list[Step], time_limit: timedelta | None = None
) -> AgentRunResult:
    runtime, request = start(tmp_path, steps)
    if time_limit is not None:
        request = request.model_copy(update={"time_limit": time_limit})
    return runtime.run(request)


@pytest.mark.parametrize(
    ("start", "steps"),
    [
        pytest.param(_claude, [Step(stdout=_reply(is_error=True, result=LIMIT_TEXT))], id="claude"),
        pytest.param(
            _opencode,
            [
                Step(
                    stdout=stdout(step_start(), step_finish(), error(LIMIT_TEXT, status_code=500)),
                    exit_status=1,
                )
            ],
            id="opencode",
        ),
    ],
)
def test_a_run_that_died_with_an_error_reply_gives_the_reply_s_text(
    tmp_path: Path, start: Start, steps: list[Step]
) -> None:
    result = _run(start, tmp_path, steps)

    assert result.end_reason == "died"
    assert result.died_text == LIMIT_TEXT


@pytest.mark.parametrize(
    "start", [pytest.param(_claude, id="claude"), pytest.param(_opencode, id="opencode")]
)
@pytest.mark.parametrize(
    ("step", "expected"),
    [
        pytest.param(
            Step(stderr="first\nsecond\nthird\n", exit_status=1),
            "first / second / third",
            id="three-stderr-lines",
        ),
        pytest.param(Step(exit_status=3), "exit 3", id="empty-stderr"),
    ],
)
def test_a_run_that_died_without_a_reply_gives_its_standard_error_or_its_exit_status(
    tmp_path: Path, start: Start, step: Step, expected: str
) -> None:
    result = _run(start, tmp_path, [step])

    assert result.end_reason == "died"
    assert result.died_text == expected


CLAUDE_ENDS = [
    pytest.param(_claude, [Step(stdout=REPLY)], None, "completed", id="claude-completed"),
    pytest.param(
        _claude,
        [Step(stdout=_reply(structured_output=None))],
        None,
        "no_result",
        id="claude-no-result",
    ),
    pytest.param(
        _claude,
        [Step(stdout=_budget_reply()), Step(stdout=_budget_reply())],
        None,
        "budget",
        id="claude-budget",
    ),
    pytest.param(
        _claude, [Step(wait_seconds=30)], SHORT_LIMIT, "time_limit", id="claude-time-limit"
    ),
    pytest.param(
        _claude,
        [Step(stdout=_reply(is_error=True, result=LIMIT_RESULT))],
        None,
        "provider_limit",
        id="claude-provider-limit",
    ),
]
OPENCODE_ENDS = [
    pytest.param(
        _opencode, [Step(stdout=REPLY_EVENTS)], None, "completed", id="opencode-completed"
    ),
    pytest.param(
        _opencode,
        [Step(stdout=stdout(step_start(), text("No result block."), step_finish()))],
        None,
        "no_result",
        id="opencode-no-result",
    ),
    pytest.param(
        _opencode, [over_budget(with_session=False)], None, "budget", id="opencode-budget"
    ),
    pytest.param(
        _opencode,
        [Step(stdout_before_wait=stdout(step_start()), wait_seconds=30)],
        SHORT_LIMIT,
        "time_limit",
        id="opencode-time-limit",
    ),
    pytest.param(
        _opencode,
        [Step(stdout=stdout(step_start(), step_finish(), error(LIMIT_RESULT)), exit_status=1)],
        None,
        "provider_limit",
        id="opencode-provider-limit",
    ),
]


@pytest.mark.parametrize(
    ("start", "steps", "time_limit", "end_reason"), CLAUDE_ENDS + OPENCODE_ENDS
)
def test_a_run_that_did_not_die_gives_no_died_text(
    tmp_path: Path,
    start: Start,
    steps: list[Step],
    time_limit: timedelta | None,
    end_reason: EndReason,
) -> None:
    result = _run(start, tmp_path, steps, time_limit)

    assert result.end_reason == end_reason
    assert result.died_text is None


@pytest.mark.parametrize(
    ("start", "step"),
    [
        pytest.param(_claude, Step(stdout=_reply(result=OWN_ANSWER), exit_status=1), id="claude"),
        pytest.param(
            _opencode,
            Step(
                stdout=stdout(step_start(), text(result_text(entry=OWN_ANSWER)), step_finish()),
                exit_status=1,
            ),
            id="opencode",
        ),
    ],
)
def test_a_reply_that_is_no_error_is_not_quoted_when_its_process_exits_non_zero(
    tmp_path: Path, start: Start, step: Step
) -> None:
    result = _run(start, tmp_path, [step])

    assert result.end_reason == "died"
    assert result.died_text == "exit 1"


@pytest.mark.parametrize(
    "start", [pytest.param(_claude, id="claude"), pytest.param(_opencode, id="opencode")]
)
@pytest.mark.parametrize(
    ("step", "expected"),
    [
        pytest.param(
            Step(stderr="factory-login-used: subscription\n", exit_status=3),
            "exit 3",
            id="only-the-login-line",
        ),
        pytest.param(
            Step(stderr="factory-login-used: subscription\nfirst\nsecond\n", exit_status=1),
            "first / second",
            id="login-line-among-others",
        ),
    ],
)
def test_a_run_that_died_never_quotes_the_login_shell_s_line(
    tmp_path: Path, start: Start, step: Step, expected: str
) -> None:
    result = _run(start, tmp_path, [step])

    assert result.end_reason == "died"
    assert result.died_text == expected
