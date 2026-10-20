"""The `claude -p` runtime hands each call the agent's login token, read by the call's own shell."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_os_user import _request, _sudo_calls, _write_sudo
from factory.adapters.claude_runtime import (
    LOGIN_SCRIPT,
    LOGIN_VARIABLE,
    SHELL_EXECUTABLE,
    SWITCHES,
    ClaudeCodeRuntime,
)
from factory.domain.agent_runs import (
    ALLOWED_ENVIRONMENT_NAMES,
    AgentRunRequest,
    GuardSettings,
    scrub_environment,
)
from factory.domain.errors import AgentRuntimeError
from run_process_recorder import Recorder

LOGIN = "stand-in-login"
CHANGED_LOGIN = "changed-login"
REQUEST_LOGIN = "request-login"
GIVEN = {"HOME": "/home/agent", "LANG": "C.UTF-8"}
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


def _login_path(tmp_path: Path) -> Path:
    return tmp_path / "login" / "claude-login"


def _write_login(path: Path, content: bytes | None) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _runtime(
    tmp_path: Path, login_file: Path | None, steps: list[Step], sudo: Path | None = None
) -> tuple[ClaudeCodeRuntime, Path]:
    executable = write_stand_in(tmp_path / "bin", steps)
    if sudo is None:
        runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state", login_file=login_file)
    else:
        runtime = ClaudeCodeRuntime(
            str(executable), tmp_path / "state", sudo_executable=str(sudo), login_file=login_file
        )
    return runtime, executable


def _guarded_request(tmp_path: Path, os_user: str | None) -> AgentRunRequest:
    request = _request(tmp_path, os_user)
    guard = GuardSettings(root=request.working_directory, write_paths=[], protected_paths=[])
    return request.model_copy(update={"guard": guard})


@pytest.mark.parametrize(
    ("configured", "content", "expected"),
    [
        pytest.param(True, f"{LOGIN}\n".encode(), LOGIN, id="token"),
        pytest.param(False, None, None, id="no-setting"),
        pytest.param(True, None, None, id="missing"),
        pytest.param(True, b"", None, id="empty"),
        pytest.param(True, b"  \n \n", None, id="blank"),
    ],
)
def test_the_call_gets_the_login_from_a_file_that_holds_one_and_otherwise_none(
    tmp_path: Path, *, configured: bool, content: bytes | None, expected: str | None
) -> None:
    login = _login_path(tmp_path)
    _write_login(login, content)
    runtime, _ = _runtime(tmp_path, login if configured else None, [Step(stdout=REPLY)])

    result = runtime.run(_request(tmp_path, None))

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(LOGIN_VARIABLE) == expected
    assert {**GIVEN, **SWITCHES}.items() <= call.environment.items()
    assert result.end_reason == "completed"
    assert result.decision == "doing"


@pytest.mark.parametrize(
    ("configured", "content", "expected"),
    [
        pytest.param(False, None, None, id="no-setting"),
        pytest.param(True, None, None, id="missing"),
        pytest.param(True, f"{LOGIN}\n".encode(), LOGIN, id="token"),
    ],
)
def test_the_request_s_login_entry_is_dropped_for_the_file_s(
    tmp_path: Path, *, configured: bool, content: bytes | None, expected: str | None
) -> None:
    login = _login_path(tmp_path)
    _write_login(login, content)
    runtime, _ = _runtime(tmp_path, login if configured else None, [Step(stdout=REPLY)])
    request = _request(tmp_path, None)
    carrying = request.model_copy(
        update={"environment": {**request.environment, LOGIN_VARIABLE: REQUEST_LOGIN}}
    )

    runtime.run(carrying)

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(LOGIN_VARIABLE) == expected


def test_a_resumed_call_reads_the_login_file_again(tmp_path: Path) -> None:
    login = _login_path(tmp_path)
    _write_login(login, f"{LOGIN}\n".encode())
    steps = [
        Step(stdout=BUDGET_STOP, exit_status=1, writes={str(login): f"{CHANGED_LOGIN}\n"}),
        Step(stdout=REPLY),
    ]
    runtime, _ = _runtime(tmp_path, login, steps)

    result = runtime.run(_request(tmp_path, None))

    first, resumed = read_calls(tmp_path / "bin")
    assert "--resume" in resumed.arguments
    assert first.environment[LOGIN_VARIABLE] == LOGIN
    assert resumed.environment[LOGIN_VARIABLE] == CHANGED_LOGIN
    assert result.end_reason == "completed"


@pytest.mark.parametrize(
    ("before", "after", "expected_before", "expected_after"),
    [
        pytest.param(
            f"{LOGIN}\n".encode(), f"{CHANGED_LOGIN}\n".encode(), LOGIN, CHANGED_LOGIN, id="changed"
        ),
        pytest.param(None, f"{LOGIN}\n".encode(), None, LOGIN, id="new"),
        pytest.param(f"{LOGIN}\n".encode(), None, LOGIN, None, id="removed"),
    ],
)
def test_one_runtime_reads_the_login_file_again_at_every_run(
    tmp_path: Path,
    *,
    before: bytes | None,
    after: bytes | None,
    expected_before: str | None,
    expected_after: str | None,
) -> None:
    login = _login_path(tmp_path)
    _write_login(login, before)
    runtime, _ = _runtime(tmp_path, login, [Step(stdout=REPLY), Step(stdout=REPLY)])

    runtime.run(_request(tmp_path, None))
    _write_login(login, after)
    runtime.run(_request(tmp_path, None))

    first, second = read_calls(tmp_path / "bin")
    assert first.environment.get(LOGIN_VARIABLE) == expected_before
    assert second.environment.get(LOGIN_VARIABLE) == expected_after


def test_with_a_user_the_login_shell_runs_after_sudo_and_env_i_and_hands_over_the_login(
    tmp_path: Path,
) -> None:
    login = _login_path(tmp_path)
    _write_login(login, f"{LOGIN}\n".encode())
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, executable = _runtime(tmp_path, login, [Step(stdout=REPLY)], sudo)

    runtime.run(_request(tmp_path, "agent"))

    [claude_call] = read_calls(tmp_path / "bin")
    assert claude_call.environment[LOGIN_VARIABLE] == LOGIN
    [sudo_call] = _sudo_calls(tmp_path / "sudo-bin")
    expected = {**GIVEN, **SWITCHES}
    head = ["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]
    arguments = sudo_call.arguments
    assert arguments[: len(head)] == head
    assignments = arguments[len(head) : len(head) + len(expected)]
    assert sorted(assignments) == sorted(f"{name}={value}" for name, value in expected.items())
    assert arguments[len(head) + len(expected) :] == [
        SHELL_EXECUTABLE,
        "-c",
        LOGIN_SCRIPT,
        "factory-login",
        str(login),
        str(executable),
        *claude_call.arguments,
    ]


@pytest.mark.parametrize(
    "os_user", [pytest.param("agent", id="user"), pytest.param(None, id="no-user")]
)
def test_the_login_stands_in_no_argument_no_run_file_and_no_result(
    tmp_path: Path, recorder: Recorder, os_user: str | None
) -> None:
    login = _login_path(tmp_path)
    _write_login(login, f"{LOGIN}\n".encode())
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, executable = _runtime(tmp_path, login, [Step(stdout=REPLY)], sudo)

    result = runtime.run(_guarded_request(tmp_path, os_user))

    [claude_call] = read_calls(tmp_path / "bin")
    assert claude_call.environment[LOGIN_VARIABLE] == LOGIN
    assert all(LOGIN not in argument for argument in claude_call.arguments)
    assert len(claude_call.files) == 1
    assert all(LOGIN not in text for text in claude_call.files.values())
    for sudo_call in _sudo_calls(tmp_path / "sudo-bin"):
        assert all(LOGIN not in argument for argument in sudo_call.arguments)
    assert LOGIN not in result.model_dump_json()
    [process_request] = recorder.requests
    assert LOGIN not in process_request.model_dump_json()
    if os_user is None:
        assert _sudo_calls(tmp_path / "sudo-bin") == []
        assert process_request.argv == [
            SHELL_EXECUTABLE,
            "-c",
            LOGIN_SCRIPT,
            "factory-login",
            str(login),
            str(executable),
            *claude_call.arguments,
        ]


def _folder(path: Path) -> None:
    path.mkdir(parents=True)


def _utf_16(path: Path) -> None:
    _write_login(path, LOGIN.encode("utf-16"))


def _utf_16_le(path: Path) -> None:
    _write_login(path, LOGIN.encode("utf-16-le"))


@pytest.mark.parametrize(
    ("make", "os_user", "reason"),
    [
        pytest.param(_folder, None, "cannot be read", id="folder"),
        pytest.param(_utf_16, None, "not ASCII text", id="utf-16"),
        pytest.param(_utf_16_le, None, "not ASCII text", id="utf-16-without-mark"),
        pytest.param(_utf_16, "agent", "not ASCII text", id="utf-16-with-a-user"),
    ],
)
def test_a_login_file_that_cannot_be_used_stops_the_run_naming_the_file(
    tmp_path: Path, *, make: Callable[[Path], None], os_user: str | None, reason: str
) -> None:
    login = _login_path(tmp_path)
    make(login)
    sudo = _write_sudo(tmp_path / "sudo-bin")
    runtime, _ = _runtime(tmp_path, login, [Step(stdout=REPLY)], sudo)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(_request(tmp_path, os_user))

    assert str(raised.value) == (
        f"agent runtime failed: cannot read the agent's login file {login}: {reason}"
    )
    assert read_calls(tmp_path / "bin") == []
    assert list((tmp_path / "state").iterdir()) == []


def test_the_version_call_gets_no_login_and_no_login_shell(
    tmp_path: Path, recorder: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(LOGIN_VARIABLE, raising=False)
    login = _login_path(tmp_path)
    _write_login(login, f"{LOGIN}\n".encode())
    runtime, executable = _runtime(tmp_path, login, [Step(stdout="2.1.289 (Claude Code)\n")])

    runtime.version()

    [call] = read_calls(tmp_path / "bin")
    assert call.arguments == ["--version"]
    assert LOGIN_VARIABLE not in call.environment
    [process_request] = recorder.requests
    assert process_request.argv == [str(executable), "--version"]


def test_the_allow_list_keeps_its_six_names_and_scrubbing_drops_the_login() -> None:
    source = {"PATH": "/usr/bin", "HOME": "/home/factory", LOGIN_VARIABLE: LOGIN}

    scrubbed = scrub_environment(source)

    assert scrubbed == {"PATH": "/usr/bin", "HOME": "/home/factory"}
    assert frozenset({"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TZ"}) == ALLOWED_ENVIRONMENT_NAMES
