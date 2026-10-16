"""The `claude -p` runtime starts the agent as another user through `sudo -n -u ... env -i`."""

import json
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import SWITCHES, ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import AgentRuntimeError

GIVEN = {"HOME": "/home/agent", "LANG": "C.UTF-8"}
SUDO_CALLS = "sudo-calls.jsonl"
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)

# Records its arguments and environment, then either plays a refusal or runs what follows `--`,
# after printing a warning to standard error if one is given.
SUDO_SCRIPT = r"""
import json
import os
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
arguments = sys.argv[1:]
record = {"arguments": arguments, "environment": dict(os.environ)}
with (here / "sudo-calls.jsonl").open("a", encoding="utf-8") as out:
    out.write(json.dumps(record) + "\n")
refusal = here / "refusal.json"
if refusal.exists():
    played = json.loads(refusal.read_text(encoding="utf-8"))
    sys.stderr.write(played["stderr"])
    sys.exit(played["exit_status"])
warning = here / "warning.txt"
if warning.exists():
    sys.stderr.write(warning.read_text(encoding="utf-8"))
    sys.stderr.flush()
rest = arguments[arguments.index("--") + 1 :]
os.execvp(rest[0], rest)
"""


class SudoCall(BaseModel):
    """What the `sudo` stand-in saw on one call: its arguments and its environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]


def _write_sudo(
    directory: Path, refusal: tuple[str, int] | None = None, warning: str | None = None
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    if warning is not None:
        (directory / "warning.txt").write_text(warning, encoding="utf-8")
    if refusal is not None:
        stderr, exit_status = refusal
        (directory / "refusal.json").write_text(
            json.dumps({"stderr": stderr, "exit_status": exit_status}), encoding="utf-8"
        )
    path = directory / "sudo"
    path.write_text(f"#!{sys.executable}\n{SUDO_SCRIPT}", encoding="utf-8")
    path.chmod(0o755)
    return path


def _sudo_calls(directory: Path) -> list[SudoCall]:
    calls = directory / SUDO_CALLS
    if not calls.exists():
        return []
    return [
        SudoCall.model_validate_json(line)
        for line in calls.read_text(encoding="utf-8").splitlines()
    ]


def _request(tmp_path: Path, os_user: str | None) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment=GIVEN,
        os_user=os_user,
    )


def _runtime(tmp_path: Path, sudo: Path) -> tuple[ClaudeCodeRuntime, Path]:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", sudo_executable=str(sudo))
    return runtime, executable


def _without_locale(environment: dict[str, str]) -> dict[str, str]:
    # The stand-ins' Python adds LC_CTYPE when it starts in an empty environment.
    return {name: value for name, value in environment.items() if name != "LC_CTYPE"}


def test_without_a_user_the_agent_starts_directly_and_sudo_never_runs(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, _ = _runtime(tmp_path, sudo)

    runtime.run(_request(tmp_path, None))

    [call] = read_calls(tmp_path / "bin")
    assert _without_locale(call.environment) == {**GIVEN, **SWITCHES}
    assert _sudo_calls(tmp_path / "sudo-bin") == []


def test_with_a_user_sudo_gets_the_user_env_i_the_environment_and_the_executable(
    tmp_path: Path,
) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, executable = _runtime(tmp_path, sudo)

    runtime.run(_request(tmp_path, "agent"))

    [call] = _sudo_calls(tmp_path / "sudo-bin")
    expected = {**GIVEN, **SWITCHES}
    head = call.arguments[:6]
    assignments = call.arguments[6 : 6 + len(expected)]
    assert head == ["-n", "-u", "agent", "--", "env", "-i"]
    assert sorted(assignments) == sorted(f"{name}={value}" for name, value in expected.items())
    assert call.arguments[6 + len(expected)] == str(executable)
    assert _without_locale(call.environment) == {}


def test_with_a_user_the_agent_sees_only_the_request_environment_and_the_switches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GH_TOKEN", "example-value")
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, _ = _runtime(tmp_path, sudo)

    runtime.run(_request(tmp_path, "agent"))

    [call] = read_calls(tmp_path / "bin")
    assert _without_locale(call.environment) == {**GIVEN, **SWITCHES}


def test_with_a_user_the_agent_runs_in_the_request_working_directory(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, _ = _runtime(tmp_path, sudo)
    request = _request(tmp_path, "agent")

    runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    assert call.working_directory == request.working_directory


def test_a_sudo_refusal_is_a_runtime_error_naming_its_line(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin", ("sudo: a password is required\n", 1))
    runtime, _ = _runtime(tmp_path, sudo)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(_request(tmp_path, "agent"))

    assert "sudo: a password is required" in raised.value.detail


def test_a_sudo_warning_before_a_reply_gives_the_reply_s_result(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin", warning="sudo: unable to resolve host x\n")
    runtime, _ = _runtime(tmp_path, sudo)

    result = runtime.run(_request(tmp_path, "agent"))

    assert result.end_reason == "completed"
    assert result.decision == "doing"
    assert result.entry == "Done."


def test_a_failure_without_a_sudo_line_is_a_dead_run(tmp_path: Path) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin", ("boom\n", 1))
    runtime, _ = _runtime(tmp_path, sudo)

    result = runtime.run(_request(tmp_path, "agent"))

    assert result.end_reason == "died"


def test_a_missing_sudo_executable_is_a_runtime_error(tmp_path: Path) -> None:
    runtime, _ = _runtime(tmp_path, tmp_path / "no-sudo")

    with pytest.raises(AgentRuntimeError):
        runtime.run(_request(tmp_path, "agent"))
