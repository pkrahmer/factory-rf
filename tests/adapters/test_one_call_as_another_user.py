"""A call as another user is one `sudo` call, with no program started after it."""

import json
from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, write_stand_in
from adapters.opencode_stand_in import (
    MODELS,
    REPLY,
    RESUME_REPLY,
    opencode_request,
    over_budget,
    write_opencode,
)
from adapters.opencode_stand_in import Step as OpencodeStep
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from sudo_support import Sudo, write_sudo

LIMIT = timedelta(seconds=30)
USER = "agent"


def _claude_reply(subtype: str = "success", cost: float = 0.1) -> str:
    reply: dict[str, object] = {
        "type": "result",
        "subtype": subtype,
        "is_error": subtype != "success",
        "num_turns": 1,
        "total_cost_usd": cost,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
    }
    if subtype == "success":
        reply["structured_output"] = {"decision": "doing", "entry": "Done."}
    return json.dumps(reply)


def _claude_request(tmp_path: Path) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir()
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("3"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=LIMIT,
        working_directory=work,
        environment={"HOME": "/home/agent", "LANG": "C.UTF-8"},
        os_user=USER,
    )


def _claude(tmp_path: Path, sudo: Sudo, *, resumed: bool) -> None:
    steps = [Step(stdout=_claude_reply())]
    if resumed:
        steps.insert(0, Step(stdout=_claude_reply("error_max_budget_usd", 3.0)))
    executable = write_stand_in(tmp_path / "bin", steps)
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo.path))
    result = runtime.run(_claude_request(tmp_path))
    assert result.end_reason == "completed"


def _opencode(tmp_path: Path, sudo: Sudo, *, resumed: bool) -> None:
    steps: list[OpencodeStep] = [over_budget(), RESUME_REPLY] if resumed else [REPLY]
    executable = write_opencode(tmp_path / "bin", steps)
    state = tmp_path / "state"
    state.mkdir()
    runtime = OpencodeRuntime(str(executable), state, models=MODELS, sudo_executable=str(sudo.path))
    result = runtime.run(opencode_request(tmp_path / "work", os_user=USER))
    assert result.end_reason == "completed"


def _make(tmp_path: Path, sudo: Sudo) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "Makefile").write_text('check:\n\t@echo "check: green (0.1 s)"\n', encoding="utf-8")
    user = CommandUser(
        os_user=USER, sudo_executable=str(sudo.path), environment={"PATH": "/usr/bin:/bin"}
    )
    result = MakeProjectCommands(project, user=user).run("check", time_limit=LIMIT)
    assert result.status == "passed"


@pytest.mark.parametrize(
    ("call", "sudo_calls"),
    [
        pytest.param(lambda t, s: _claude(t, s, resumed=False), 1, id="claude-completed"),
        pytest.param(lambda t, s: _claude(t, s, resumed=True), 2, id="claude-resumed"),
        pytest.param(lambda t, s: _opencode(t, s, resumed=False), 1, id="opencode-completed"),
        pytest.param(lambda t, s: _opencode(t, s, resumed=True), 2, id="opencode-resumed"),
        pytest.param(_make, 1, id="make-command"),
    ],
)
def test_a_call_as_another_user_is_one_sudo_call_per_agent_call(
    tmp_path: Path, call: Callable[[Path, Sudo], None], sudo_calls: int
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin")

    call(tmp_path, sudo)

    assert len(sudo.calls()) == sudo_calls
