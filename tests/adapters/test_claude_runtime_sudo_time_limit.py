"""Under `sudo`, the agent's own `timeout` kills the call at its limit, read as `time_limit`."""

import json
import time
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, write_stand_in
from adapters.test_claude_runtime_os_user import _request, _write_sudo
from factory.adapters import claude_runtime
from factory.adapters.claude_runtime import SWITCHES, ClaudeCodeRuntime
from factory.adapters.process import ProcessRequest, ProcessResult
from factory.domain.agent_runs import AgentRunResult
from factory.domain.errors import AgentRuntimeError

REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "duration_api_ms": 90,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)
BUDGET_STOP = json.dumps(
    {
        "type": "result",
        "subtype": "error_max_budget_usd",
        "is_error": True,
        "num_turns": 3,
        "total_cost_usd": 1.0,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
    }
)
WARNING = "sudo: unable to resolve host x"


class Recorder:
    """Stands in for `run_process`: keeps each request and answers with the next given result."""

    def __init__(self) -> None:
        self.requests: list[ProcessRequest] = []
        self.results: list[ProcessResult] = []

    def __call__(self, request: ProcessRequest) -> ProcessResult:
        self.requests.append(request)
        return self.results[len(self.requests) - 1]


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    recording = Recorder()
    monkeypatch.setattr(claude_runtime, "run_process", recording)
    return recording


def _process_result(stdout: str, exit_status: int, seconds: float) -> ProcessResult:
    return ProcessResult(
        exit_status=exit_status,
        stdout=stdout,
        stderr="",
        timed_out=False,
        duration=timedelta(seconds=seconds),
    )


def _assert_no_measures(result: AgentRunResult) -> None:
    assert result.decision is None
    assert result.entry is None
    assert result.turns is None
    assert result.tokens is None
    assert result.cost_usd is None
    assert result.model_duration is None


@pytest.mark.parametrize(
    ("seconds", "limit_argument"),
    [pytest.param(30.0, "30s", id="whole"), pytest.param(1.5, "2s", id="rounded-up")],
)
def test_with_a_user_sudo_runs_the_agent_under_timeout_with_the_limit_rounded_up(
    tmp_path: Path, seconds: float, limit_argument: str
) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin")
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo))
    request = _request(tmp_path, "agent").model_copy(
        update={"time_limit": timedelta(seconds=seconds)}
    )

    runtime.run(request)

    [call] = [
        json.loads(line)
        for line in (tmp_path / "sudo-bin" / "sudo-calls.jsonl").read_text("utf-8").splitlines()
    ]
    arguments: list[str] = call["arguments"]
    expected = {**request.environment, **SWITCHES}
    head = ["-n", "-u", "agent", "--", "timeout", "--signal=KILL", limit_argument, "env", "-i"]
    assert arguments[: len(head)] == head
    assignments = arguments[len(head) : len(head) + len(expected)]
    assert sorted(assignments) == sorted(f"{name}={value}" for name, value in expected.items())
    assert arguments[len(head) + len(expected)] == str(executable)


def test_with_a_user_the_inner_kill_at_the_limit_is_a_time_limit_without_measures(
    tmp_path: Path,
) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin")
    executable = write_stand_in(tmp_path / "bin", [Step(stdout_before_wait=REPLY, wait_seconds=60)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo))
    request = _request(tmp_path, "agent").model_copy(update={"time_limit": timedelta(seconds=1)})

    started = time.monotonic()
    result = runtime.run(request)
    elapsed = time.monotonic() - started

    assert result.end_reason == "time_limit"
    _assert_no_measures(result)
    assert elapsed < 31


@pytest.mark.parametrize(
    ("os_user", "process", "end_reason"),
    [
        pytest.param("agent", _process_result(REPLY, 137, 30.0), "time_limit", id="137-at-limit"),
        pytest.param("agent", _process_result(REPLY, -9, 30.0), "time_limit", id="kill-at-limit"),
        pytest.param("agent", _process_result(REPLY, 137, 29.9), "died", id="137-before-limit"),
        pytest.param("agent", _process_result(REPLY, -9, 29.9), "died", id="sigkill-before-limit"),
        pytest.param("agent", _process_result(REPLY, 1, 30.0), "died", id="status-1-at-limit"),
        pytest.param(None, _process_result(REPLY, 137, 30.0), "died", id="137-without-a-user"),
    ],
)
def test_a_kill_status_at_the_limit_under_sudo_is_a_time_limit_and_otherwise_a_death(
    tmp_path: Path,
    recorder: Recorder,
    os_user: str | None,
    process: ProcessResult,
    end_reason: str,
) -> None:
    recorder.results = [process]
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state", sudo_executable="sudo")

    result = runtime.run(_request(tmp_path, os_user))

    assert result.end_reason == end_reason
    if end_reason == "time_limit":
        _assert_no_measures(result)


def test_a_sudo_line_before_the_inner_kill_is_a_runtime_error(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin", warning=f"{WARNING}\n")
    executable = write_stand_in(tmp_path / "bin", [Step(stdout_before_wait=REPLY, wait_seconds=60)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo))
    request = _request(tmp_path, "agent").model_copy(update={"time_limit": timedelta(seconds=1)})

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(request)

    assert WARNING in raised.value.detail


@pytest.mark.parametrize(
    ("os_user", "time_limit", "under_timeout"),
    [
        pytest.param("agent", timedelta(seconds=60), True, id="with-a-user"),
        pytest.param(None, timedelta(seconds=30), False, id="without-a-user"),
    ],
)
def test_the_outer_limit_adds_the_grace_only_under_sudo(
    tmp_path: Path,
    recorder: Recorder,
    os_user: str | None,
    time_limit: timedelta,
    under_timeout: bool,
) -> None:
    recorder.results = [_process_result(REPLY, 0, 1.0)]
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state", sudo_executable="sudo")

    runtime.run(_request(tmp_path, os_user))

    [process_request] = recorder.requests
    assert process_request.time_limit == time_limit
    assert ("timeout" in process_request.argv) == under_timeout


def test_the_resume_under_sudo_is_limited_by_what_is_left_of_the_time_limit(
    tmp_path: Path, recorder: Recorder
) -> None:
    recorder.results = [_process_result(BUDGET_STOP, 1, 0.0), _process_result(REPLY, 0, 0.0)]
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state", sudo_executable="sudo")

    runtime.run(_request(tmp_path, "agent"))

    [_, resume] = recorder.requests
    start = resume.argv.index("timeout")
    assert resume.argv[start : start + 3] == ["timeout", "--signal=KILL", "30s"]
    assert resume.time_limit is not None
    assert timedelta(seconds=59) < resume.time_limit <= timedelta(seconds=60)
