"""The `claude -p` runtime resumes the session a request names."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import REPLY, Step, claude_request, read_calls, write_stand_in
from adapters.test_claude_runtime_resume import _after, _budget_reply
from factory.adapters.claude_runtime import FINISH_MESSAGE, ClaudeCodeRuntime
from factory.domain.agent_runs import AgentRunRequest

INSTRUCTIONS_FLAG = "--append-system-prompt-file"


def _runtime(tmp_path: Path, steps: list[Step]) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    return ClaudeCodeRuntime(str(executable), tmp_path / "state")


def _resuming(tmp_path: Path, resume_session: str | None) -> AgentRunRequest:
    return claude_request(tmp_path).model_copy(update={"resume_session": resume_session})


def _files_id(arguments: list[str]) -> str:
    name = Path(_after(arguments, INSTRUCTIONS_FLAG)).name
    return name.removeprefix("instructions-").removesuffix(".md")


@pytest.mark.parametrize("resume_session", [None, "ses_a"], ids=["new", "resumed"])
def test_a_run_starts_a_new_session_or_resumes_the_named_one_and_keeps_it(
    tmp_path: Path, resume_session: str | None
) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)])
    request = _resuming(tmp_path, resume_session)

    result = runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    arguments = call.arguments
    assert result.end_reason == "completed"
    assert _after(arguments, "-p") == request.prompt
    assert _after(arguments, "--max-budget-usd") == format(request.agent.budget_usd, "f")
    if resume_session is None:
        assert "--resume" not in arguments
        assert result.session == _after(arguments, "--session-id")
        return
    assert _after(arguments, "--resume") == resume_session
    assert "--session-id" not in arguments
    assert result.session == resume_session
    assert _files_id(arguments)
    assert _files_id(arguments) != resume_session


def test_a_resumed_session_stopped_by_its_budget_is_resumed_once_with_the_finish_message(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=_budget_reply()), Step(stdout=REPLY)])

    result = runtime.run(_resuming(tmp_path, "ses_a"))

    first, second = read_calls(tmp_path / "bin")
    assert result.end_reason == "completed"
    assert _after(first.arguments, "--resume") == "ses_a"
    assert _after(second.arguments, "--resume") == "ses_a"
    assert _after(second.arguments, "-p") == FINISH_MESSAGE
    assert "--session-id" not in second.arguments
    assert result.session == "ses_a"
