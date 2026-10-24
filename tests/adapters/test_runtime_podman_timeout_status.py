"""A runtime's call in a container that podman ended with 255 at its limit ends `time_limit`."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.container_runtime_support import container_environment, make_workspace
from adapters.opencode_stand_in import MODELS, opencode_request, stdout, step_finish, step_start
from adapters.test_claude_runtime_login import REPLY
from factory.adapters import opencode_runtime
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.process import ProcessRequest, ProcessResult, Stream
from factory.domain.agent_runs import AgentRunRequest
from run_process_recorder import Recorder

LIMIT = timedelta(seconds=30)
PODMAN_TIMEOUT = 255

ROWS = [
    pytest.param(30.0, "time_limit", id="at-the-limit"),
    pytest.param(29.9, "died", id="before-the-limit"),
]


@pytest.fixture
def fake(tmp_path: Path) -> FakeContainerRuns:
    return FakeContainerRuns(make_workspace(tmp_path))


def _request(tmp_path: Path) -> AgentRunRequest:
    return opencode_request(
        tmp_path / "work",
        environment=container_environment(tmp_path / "bin"),
        time_limit=LIMIT,
    )


def _ended(seconds: float, output: str) -> ProcessResult:
    return ProcessResult(
        exit_status=PODMAN_TIMEOUT,
        stdout=output,
        stderr="",
        timed_out=False,
        duration=timedelta(seconds=seconds),
    )


@pytest.mark.parametrize(("seconds", "end_reason"), ROWS)
def test_claude_code_in_a_container_reads_podman_s_255_at_the_limit_as_the_time_limit(
    tmp_path: Path, fake: FakeContainerRuns, recorder: Recorder, seconds: float, end_reason: str
) -> None:
    recorder.results = [_ended(seconds, REPLY)]
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state", containers=fake)

    result = runtime.run(_request(tmp_path))

    assert result.end_reason == end_reason
    if end_reason == "time_limit":
        assert len(recorder.requests) == 1


@pytest.mark.parametrize(("seconds", "end_reason"), ROWS)
def test_opencode_in_a_container_reads_podman_s_255_at_the_limit_as_the_time_limit(
    tmp_path: Path,
    fake: FakeContainerRuns,
    monkeypatch: pytest.MonkeyPatch,
    seconds: float,
    end_reason: str,
) -> None:
    requests: list[ProcessRequest] = []

    def answer(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult:
        del on_line
        requests.append(request)
        return _ended(seconds, stdout(step_start(), step_finish()))

    monkeypatch.setattr(opencode_runtime, "run_streaming", answer)
    state = tmp_path / "state"
    state.mkdir()
    runtime = OpencodeRuntime("opencode", state, models=MODELS, containers=fake)

    result = runtime.run(_request(tmp_path))

    assert result.end_reason == end_reason
    if end_reason == "time_limit":
        assert len(requests) == 1
