"""The opencode runtime starts its call as the agent user, through the wrapper, with the API key."""

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
from adapters.test_agent_launch_login import API_LOGIN
from adapters.test_claude_runtime_os_user import _sudo_calls, _write_sudo
from confine_support import (
    LINE,
    ConfineCall,
    Layout,
    Played,
    read_records,
    run_request,
    write_confine,
)
from factory.adapters.agent_launch import API_LOGIN_VARIABLE, temporary_folder
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, SWITCHES, OpencodeRuntime
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.confinement import Confinement
from factory.domain.errors import AgentRuntimeError

GIVEN = {"HOME": "/home/agent", "LANG": "C.UTF-8"}
SUDO_HEAD = ["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]
SUDO_LINE = "sudo: a password is required"
# A few seconds, so the child has room to start; the stand-in waits far longer.
SHORT_LIMIT = timedelta(seconds=3)
ELAPSED_BOUND = 20


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    *,
    sudo: Path | None = None,
    api_login_file: Path | None = None,
    version_time_limit: timedelta = timedelta(seconds=30),
) -> OpencodeRuntime:
    executable = write_opencode(tmp_path / "bin", steps)
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    if sudo is None:
        return OpencodeRuntime(
            str(executable),
            state,
            models=MODELS,
            api_login_file=api_login_file,
            version_time_limit=version_time_limit,
        )
    return OpencodeRuntime(
        str(executable),
        state,
        models=MODELS,
        sudo_executable=str(sudo),
        api_login_file=api_login_file,
        version_time_limit=version_time_limit,
    )


def _run_id(config: str) -> str:
    return Path(config).name.removeprefix("opencode-").removesuffix(".json")


@pytest.mark.parametrize(
    "refused", [pytest.param(False, id="runs"), pytest.param(True, id="refused")]
)
def test_with_an_agent_user_sudo_starts_the_call_after_env_i_and_its_environment(
    tmp_path: Path, *, refused: bool
) -> None:
    sudo = _write_sudo(tmp_path / "sudo-bin", (f"{SUDO_LINE}\n", 1) if refused else None)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], sudo=sudo)
    request = opencode_request(tmp_path / "work", environment=GIVEN, os_user="agent")

    if refused:
        with pytest.raises(AgentRuntimeError) as raised:
            runtime.run(request)
        assert raised.value.detail == f"{sudo} refused the agent run: {SUDO_LINE}"
        return
    runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    [sudo_call] = _sudo_calls(tmp_path / "sudo-bin")
    expected = {**GIVEN, CONFIG_VARIABLE: call.environment[CONFIG_VARIABLE], **SWITCHES}
    count = len(expected)
    assert sudo_call.arguments[:9] == SUDO_HEAD
    assert sorted(sudo_call.arguments[9 : 9 + count]) == sorted(
        f"{name}={value}" for name, value in expected.items()
    )
    assert sudo_call.arguments[9 + count :] == [str(tmp_path / "bin" / "opencode"), *call.arguments]


def _confined_runtime(layout: Layout, steps: list[Step], confine: Path) -> OpencodeRuntime:
    executable = write_opencode(layout.stand_in, steps)
    layout.state.mkdir(exist_ok=True)
    return OpencodeRuntime(
        str(executable),
        layout.state,
        models=MODELS,
        confine_executable=str(confine),
        temporary_root=layout.temporary_root,
    )


def test_through_the_wrapper_the_call_gets_its_rules_with_opencode_s_folders(
    layout: Layout,
) -> None:
    confine = write_confine(layout)
    runtime = _confined_runtime(layout, [Step(stdout=REPLY_EVENTS)], confine)

    result = runtime.run(run_request(layout))

    [call] = read_calls(layout.stand_in)
    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    run = _run_id(call.environment[CONFIG_VARIABLE])
    rules = Confinement.model_validate_json(confined.rules_text)
    home = layout.home
    assert result.end_reason == "completed"
    assert confined.arguments == [
        "--rules",
        str(layout.state / f"confine-{run}.json"),
        "--",
        str(layout.stand_in / "opencode"),
        *call.arguments,
    ]
    assert confined.rules_mode == 0o640
    for folder in (".local/share/opencode", ".local/state/opencode", ".cache/opencode"):
        assert home / folder in rules.folders
    assert not any(folder.is_relative_to(home / ".config") for folder in rules.folders)
    assert not any(file.is_relative_to(home / ".config") for file in rules.files)
    assert rules.temporary_directory == temporary_folder(layout.temporary_root, run)
    assert list(layout.temporary_root.iterdir()) == []


def test_a_wrapper_line_without_events_is_a_runtime_error_naming_it(layout: Layout) -> None:
    confine = write_confine(layout, Played())
    runtime = _confined_runtime(layout, [Step(stdout=REPLY_EVENTS)], confine)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(run_request(layout))

    assert raised.value.detail == f"{confine} refused the agent run: {LINE}"


def _warned_by_sudo(tmp_path: Path, _: Layout) -> tuple[OpencodeRuntime, AgentRunRequest]:
    sudo = _write_sudo(tmp_path / "sudo-bin", warning=f"{SUDO_LINE}\n")
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], sudo=sudo)
    return runtime, opencode_request(tmp_path / "work", environment=GIVEN, os_user="agent")


def _warned_by_wrapper(_: Path, layout: Layout) -> tuple[OpencodeRuntime, AgentRunRequest]:
    confine = write_confine(layout, Played(stdout=REPLY_EVENTS, exit_status=0))
    return _confined_runtime(layout, [Step(stdout=REPLY_EVENTS)], confine), run_request(layout)


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_warned_by_sudo, id="sudo"),
        pytest.param(_warned_by_wrapper, id="wrapper"),
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
    sudo = _write_sudo(tmp_path / "sudo-bin")
    api = _api_file(tmp_path, content)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], sudo=sudo, api_login_file=api)

    result = runtime.run(opencode_request(tmp_path / "work", environment=GIVEN, os_user="agent"))

    [call] = read_calls(tmp_path / "bin")
    [sudo_call] = _sudo_calls(tmp_path / "sudo-bin")
    assert call.environment.get(API_LOGIN_VARIABLE) == key
    assert result.login == login
    assert all(API_LOGIN not in argument for argument in sudo_call.arguments)
    assert all(API_LOGIN not in config for config in call.files.values())
    assert API_LOGIN not in result.model_dump_json()
    if api is None:
        count = len({**GIVEN, CONFIG_VARIABLE: "", **SWITCHES})
        assert sudo_call.arguments[9 + count] == str(tmp_path / "bin" / "opencode")


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
