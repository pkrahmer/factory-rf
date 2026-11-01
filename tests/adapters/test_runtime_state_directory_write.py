"""Both agent runtimes refuse a state directory they cannot write and make a missing one."""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from adapters.claude_stand_in import REPLY, Step, claude_request, read_calls, write_stand_in
from adapters.opencode_stand_in import MODELS, opencode_request, write_opencode
from adapters.opencode_stand_in import REPLY as OPENCODE_REPLY
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.errors import AgentRuntimeError

ROOT = os.geteuid() == 0

# Builds a runtime that keeps its files in the given state directory and calls a stand-in
# under `tmp_path / "bin"`, and a request it can run.
Setup = Callable[[Path, Path], tuple[AgentRuntime, AgentRunRequest]]


def _claude(tmp_path: Path, state: Path) -> tuple[AgentRuntime, AgentRunRequest]:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    return ClaudeCodeRuntime(str(executable), state), claude_request(tmp_path)


def _opencode(tmp_path: Path, state: Path) -> tuple[AgentRuntime, AgentRunRequest]:
    executable = write_opencode(tmp_path / "bin", [OPENCODE_REPLY])
    runtime = OpencodeRuntime(str(executable), state, models=MODELS)
    return runtime, opencode_request(tmp_path / "work")


RUNTIMES = [pytest.param(_claude, id="claude"), pytest.param(_opencode, id="opencode")]


@pytest.fixture
def read_only_state(tmp_path: Path) -> Iterator[Path]:
    """A state directory that exists and that its owner may read but not write."""
    state = tmp_path / "state"
    state.mkdir()
    state.chmod(0o500)
    yield state
    state.chmod(0o755)


@pytest.mark.skipif(ROOT, reason="root writes in unwritable directories")
@pytest.mark.parametrize("setup", RUNTIMES)
def test_a_run_whose_state_directory_cannot_be_written_fails_before_the_call(
    tmp_path: Path, read_only_state: Path, setup: Setup
) -> None:
    runtime, request = setup(tmp_path, read_only_state)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(request)

    assert raised.value.detail.startswith(f"cannot write the state directory {read_only_state}: ")
    assert read_calls(tmp_path / "bin") == []
    assert list(read_only_state.iterdir()) == []


@pytest.mark.parametrize("setup", RUNTIMES)
def test_a_run_makes_its_missing_state_directory_and_completes(
    tmp_path: Path, setup: Setup
) -> None:
    state = tmp_path / "missing" / "state"
    runtime, request = setup(tmp_path, state)

    result = runtime.run(request)

    assert state.is_dir()
    assert result.end_reason == "completed"
