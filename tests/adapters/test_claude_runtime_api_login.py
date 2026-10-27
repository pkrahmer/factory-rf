"""The `claude -p` runtime hands each call the API file's key, or else the token file's token."""

from collections.abc import Callable
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, claude_request, read_calls, write_stand_in
from agent_login_support import API_LOGIN, SUBSCRIPTION, _utf_16
from claude_reply_support import BUDGET_STOP, REPLY
from factory.adapters.agent_launch import API_LOGIN_VARIABLE, LOGIN_VARIABLE
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import Login
from factory.domain.errors import AgentRuntimeError
from run_process_recorder import Recorder

REQUEST_LOGIN = "request-login"


def _files(tmp_path: Path) -> tuple[Path, Path]:
    folder = tmp_path / "login"
    folder.mkdir(exist_ok=True)
    api, subscription = folder / "api-login", folder / "claude-login"
    api.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    subscription.write_text(f"{SUBSCRIPTION}\n", encoding="utf-8")
    return api, subscription


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    *,
    login_file: Path | None,
    api_login_file: Path | None,
) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    if api_login_file is None:
        return ClaudeCodeRuntime(str(executable), tmp_path / "state", login_file=login_file)
    return ClaudeCodeRuntime(
        str(executable),
        tmp_path / "state",
        login_file=login_file,
        api_login_file=api_login_file,
    )


def test_the_api_file_s_key_wins_and_an_emptied_file_falls_back_to_the_token(
    tmp_path: Path,
) -> None:
    api, subscription = _files(tmp_path)
    runtime = _runtime(
        tmp_path,
        [Step(stdout=REPLY), Step(stdout=REPLY)],
        login_file=subscription,
        api_login_file=api,
    )

    first = runtime.run(claude_request(tmp_path))
    api.write_text("", encoding="utf-8")
    second = runtime.run(claude_request(tmp_path))

    first_call, second_call = read_calls(tmp_path / "bin")
    assert first_call.environment[API_LOGIN_VARIABLE] == API_LOGIN
    assert LOGIN_VARIABLE not in first_call.environment
    assert first.login == "api_key"
    assert second_call.environment[LOGIN_VARIABLE] == SUBSCRIPTION
    assert API_LOGIN_VARIABLE not in second_call.environment
    assert second.login == "subscription"


@pytest.mark.parametrize(
    ("with_subscription", "expected"),
    [
        pytest.param(True, "subscription", id="token-file-only"),
        pytest.param(False, None, id="no-login-file"),
    ],
)
def test_without_an_api_file_the_login_is_the_token_s_or_none(
    tmp_path: Path, *, with_subscription: bool, expected: Login | None
) -> None:
    _, subscription = _files(tmp_path)
    runtime = _runtime(
        tmp_path,
        [Step(stdout=REPLY)],
        login_file=subscription if with_subscription else None,
        api_login_file=None,
    )

    result = runtime.run(claude_request(tmp_path))

    assert result.login == expected


@pytest.mark.parametrize("name", [API_LOGIN_VARIABLE, LOGIN_VARIABLE])
@pytest.mark.parametrize("with_key", [pytest.param(True, id="key"), pytest.param(False, id="none")])
def test_the_request_s_login_entries_are_dropped_for_the_files(
    tmp_path: Path, *, name: str, with_key: bool
) -> None:
    api, _ = _files(tmp_path)
    if not with_key:
        api.write_text("", encoding="utf-8")
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)], login_file=None, api_login_file=api)
    request = claude_request(tmp_path)
    carrying = request.model_copy(
        update={"environment": {**request.environment, name: REQUEST_LOGIN}}
    )

    runtime.run(carrying)

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(API_LOGIN_VARIABLE) == (API_LOGIN if with_key else None)
    assert LOGIN_VARIABLE not in call.environment
    assert REQUEST_LOGIN not in call.environment.values()


def test_the_key_stands_in_no_argument_no_run_file_and_no_result(
    tmp_path: Path, recorder: Recorder
) -> None:
    api, subscription = _files(tmp_path)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)], login_file=subscription, api_login_file=api)

    result = runtime.run(claude_request(tmp_path))

    [claude_call] = read_calls(tmp_path / "bin")
    assert claude_call.environment[API_LOGIN_VARIABLE] == API_LOGIN
    assert all(API_LOGIN not in argument for argument in claude_call.arguments)
    assert claude_call.files
    assert all(API_LOGIN not in text for text in claude_call.files.values())
    assert API_LOGIN not in result.model_dump_json()
    assert recorder.requests
    assert all(API_LOGIN not in request.model_dump_json() for request in recorder.requests)


def _folder(path: Path) -> None:
    path.unlink()
    path.mkdir()


@pytest.mark.parametrize(
    ("make", "reason"),
    [
        pytest.param(_folder, "cannot be read", id="folder"),
        pytest.param(_utf_16, "not ASCII text", id="utf-16"),
    ],
)
def test_an_api_file_that_cannot_be_used_stops_the_run_naming_the_file(
    tmp_path: Path, *, make: Callable[[Path], None], reason: str
) -> None:
    api, subscription = _files(tmp_path)
    make(api)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)], login_file=subscription, api_login_file=api)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(claude_request(tmp_path))

    assert str(raised.value) == (
        f"agent runtime failed: cannot read the agent's API login file {api}: {reason}"
    )
    assert read_calls(tmp_path / "bin") == []
    assert list((tmp_path / "state").iterdir()) == []


def test_a_resumed_call_whose_api_file_was_emptied_gets_the_token(tmp_path: Path) -> None:
    api, subscription = _files(tmp_path)
    steps = [Step(stdout=BUDGET_STOP, exit_status=1, writes={str(api): ""}), Step(stdout=REPLY)]
    runtime = _runtime(tmp_path, steps, login_file=subscription, api_login_file=api)

    result = runtime.run(claude_request(tmp_path))

    first, resumed = read_calls(tmp_path / "bin")
    assert "--resume" in resumed.arguments
    assert first.environment[API_LOGIN_VARIABLE] == API_LOGIN
    assert resumed.environment[LOGIN_VARIABLE] == SUBSCRIPTION
    assert result.login == "subscription"


def test_the_version_call_gets_no_login_words_and_neither_name(
    tmp_path: Path, recorder: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(LOGIN_VARIABLE, raising=False)
    monkeypatch.delenv(API_LOGIN_VARIABLE, raising=False)
    api, subscription = _files(tmp_path)
    runtime = _runtime(
        tmp_path,
        [Step(stdout="2.1.289 (Claude Code)\n")],
        login_file=subscription,
        api_login_file=api,
    )

    runtime.version()

    [call] = read_calls(tmp_path / "bin")
    assert call.arguments == ["--version"]
    assert LOGIN_VARIABLE not in call.environment
    assert API_LOGIN_VARIABLE not in call.environment
    [process_request] = recorder.requests
    assert process_request.argv == [str(tmp_path / "bin" / "claude"), "--version"]
