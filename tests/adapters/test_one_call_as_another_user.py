"""A call as another user is one `sudo` call, with no program started after it."""

from collections.abc import Callable
from datetime import timedelta
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
from adapters.test_claude_runtime_login import BUDGET_STOP
from adapters.test_claude_runtime_login import REPLY as CLAUDE_REPLY
from adapters.test_claude_runtime_os_user import _request
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.adapters.opencode_runtime import OpencodeRuntime
from sudo_support import Sudo, write_sudo

LIMIT = timedelta(seconds=30)
USER = "agent"


def _claude(tmp_path: Path, sudo: Sudo, *, resumed: bool) -> None:
    steps = [Step(stdout=CLAUDE_REPLY)]
    if resumed:
        steps.insert(0, Step(stdout=BUDGET_STOP))
    executable = write_stand_in(tmp_path / "bin", steps)
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo.path))
    result = runtime.run(_request(tmp_path, USER))
    assert result.end_reason == "completed"


def _opencode(tmp_path: Path, sudo: Sudo, *, resumed: bool) -> None:
    steps: list[Step] = [over_budget(), RESUME_REPLY] if resumed else [REPLY]
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
