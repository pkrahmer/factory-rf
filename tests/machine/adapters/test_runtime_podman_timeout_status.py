"""A runtime's call in a container that podman ended with 255 at its limit ends `time_limit`."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from claude_stand_in import REPLY
from container_runtime_support import container_request, make_state
from factory.agents.adapters import opencode_runtime
from factory.agents.adapters.claude_runtime import ClaudeCodeRuntime
from factory.agents.adapters.opencode_runtime import OpencodeRuntime
from factory.machine.adapters.fake_containers import FakeContainerRuns
from factory.shared.adapters.process import ProcessRequest, ProcessResult, Stream
from opencode_stand_in import MODELS, stdout, step_finish, step_start
from run_process_recorder import Recorder

PODMAN_TIMEOUT = 255

ROWS = [
    pytest.param(30.0, "time_limit", id="at-the-limit"),
    pytest.param(29.9, "died", id="before-the-limit"),
]


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

    result = runtime.run(container_request(tmp_path))

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
    runtime = OpencodeRuntime("opencode", make_state(tmp_path), models=MODELS, containers=fake)

    result = runtime.run(container_request(tmp_path))

    assert result.end_reason == end_reason
    if end_reason == "time_limit":
        assert len(requests) == 1
