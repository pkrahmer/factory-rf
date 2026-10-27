"""The opencode runtime starts its call with the API key."""

import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    MODELS,
    REPLY_EVENTS,
    opencode_request,
    write_opencode,
)
from agent_login_support import API_LOGIN
from factory.adapters.agent_launch import API_LOGIN_VARIABLE
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.errors import AgentRuntimeError
from run_layout_support import (
    Layout,
)

GIVEN = {"HOME": "/home/agent", "LANG": "C.UTF-8"}
SUDO_LINE = "sudo: a password is required"
# A few seconds, so the child has room to start; the stand-in waits far longer.
SHORT_LIMIT = timedelta(seconds=3)
ELAPSED_BOUND = 20


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    *,
    api_login_file: Path | None = None,
    version_time_limit: timedelta = timedelta(seconds=30),
) -> OpencodeRuntime:
    executable = write_opencode(tmp_path / "bin", steps)
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    return OpencodeRuntime(
        str(executable),
        state,
        models=MODELS,
        api_login_file=api_login_file,
        version_time_limit=version_time_limit,
    )


def _run_id(config: str) -> str:
    return Path(config).name.removeprefix("opencode-").removesuffix(".json")


def _warned_by_sudo(tmp_path: Path, _: Layout) -> tuple[OpencodeRuntime, AgentRunRequest]:
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS, stderr=f"{SUDO_LINE}\n")])
    return runtime, opencode_request(tmp_path / "work", environment=GIVEN)


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_warned_by_sudo, id="sudo"),
    ],
)
def test_a_call_that_printed_valid_events_is_no_refusal_whatever_its_stderr_holds(
    tmp_path: Path,
    layout: Layout,
    build: Callable[[Path, Layout], tuple[OpencodeRuntime, AgentRunRequest]],
) -> None:
    runtime, request = build(tmp_path, layout)

    result = runtime.run(request)

    assert result.end_reason == "completed"
    assert result.decision == "doing"
    assert result.entry == "Built it."


def _api_file(tmp_path: Path, content: str | None) -> Path | None:
    if content is None:
        return None
    path = tmp_path / "login" / "api-login"
    path.parent.mkdir()
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("content", "key", "login"),
    [
        pytest.param(f"{API_LOGIN}\n", API_LOGIN, "api_key", id="key"),
        pytest.param("", None, "none", id="empty"),
        pytest.param(None, None, None, id="no-file"),
    ],
)
def test_the_call_gets_the_api_file_s_key_and_the_result_names_the_login(
    tmp_path: Path, content: str | None, key: str | None, login: str | None
) -> None:
    api = _api_file(tmp_path, content)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], api_login_file=api)

    result = runtime.run(opencode_request(tmp_path / "work", environment=GIVEN))

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(API_LOGIN_VARIABLE) == key
    assert result.login == login
    assert all(API_LOGIN not in argument for argument in call.arguments)
    assert all(API_LOGIN not in config for config in call.files.values())
    assert API_LOGIN not in result.model_dump_json()


def test_an_api_file_that_is_a_folder_stops_the_run_naming_it(tmp_path: Path) -> None:
    api = tmp_path / "login" / "api-login"
    api.mkdir(parents=True)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], api_login_file=api)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(opencode_request(tmp_path / "work"))

    assert str(raised.value) == (
        f"agent runtime failed: cannot read the agent's API login file {api}: cannot be read"
    )
    assert read_calls(tmp_path / "bin") == []


def test_the_version_is_the_first_word_of_a_call_without_login_words(tmp_path: Path) -> None:
    api = _api_file(tmp_path, f"{API_LOGIN}\n")
    runtime = _runtime(tmp_path, [Step(stdout="1.19.3\n")], api_login_file=api)

    assert runtime.version() == "1.19.3"
    [call] = read_calls(tmp_path / "bin")
    assert call.arguments == ["--version"]
    assert API_LOGIN_VARIABLE not in set(call.environment)


@pytest.mark.parametrize(
    "step",
    [
        pytest.param(Step(stdout="1.19.3\n", exit_status=1), id="exit-1"),
        pytest.param(Step(stdout=""), id="nothing"),
        pytest.param(Step(stdout_before_wait="", wait_seconds=30, stdout="1.19.3\n"), id="waits"),
    ],
)
def test_a_version_that_cannot_be_read_is_a_runtime_error(tmp_path: Path, step: Step) -> None:
    runtime = _runtime(tmp_path, [step], version_time_limit=SHORT_LIMIT)
    started = time.monotonic()

    with pytest.raises(AgentRuntimeError):
        runtime.version()

    assert time.monotonic() - started < ELAPSED_BOUND
