"""The opencode runtime's call, its per-run configuration and the run's files."""

import json
import re
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, without_locale
from adapters.opencode_stand_in import (
    MODELS,
    REPLY_EVENTS,
    opencode_request,
    stand_in_runtime,
    stdout,
    step_start,
    write_agent_settings,
    write_opencode,
)
from factory.adapters.agent_launch import API_LOGIN_VARIABLE, LOGIN_VARIABLE
from factory.adapters.opencode_runtime import (
    CONFIG_VARIABLE,
    OPENCODE_TOOLS,
    SWITCHES,
    OpencodeRuntime,
    result_instructions,
)
from factory.application.agent_runtime import AgentRuntime
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import KillPoint, KillPoints

LIMIT = timedelta(seconds=30)
# A few seconds, so the child has room to start; the stand-in waits far longer.
SHORT_LIMIT = timedelta(seconds=3)
CONFIG_NAME = re.compile(
    r"opencode-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.json"
)


@pytest.mark.parametrize(
    ("model", "passed"),
    [
        pytest.param("sonnet", "anthropic/claude-sonnet-5-5", id="alias"),
        pytest.param("openai/gpt-5", "openai/gpt-5", id="provider-model"),
    ],
)
def test_a_run_calls_opencode_run_with_its_words_in_the_working_directory(
    tmp_path: Path, model: str, passed: str
) -> None:
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY_EVENTS)])
    request = opencode_request(tmp_path / "work", model=model)

    runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    assert call.arguments == [
        "run",
        "--format",
        "json",
        "--auto",
        "--model",
        passed,
        "--agent",
        "factory-coder",
        "Stage: doing",
    ]
    assert call.working_directory == request.working_directory


@pytest.mark.parametrize(
    ("model", "tools", "settings", "detail"),
    [
        pytest.param(
            "opus",
            ("Read",),
            None,
            "the opencode runtime has no model for opus: set FACTORY_OPENCODE_MODELS",
            id="alias-without-mapping",
        ),
        pytest.param(
            "sonnet",
            ("Read", "NotebookEdit"),
            None,
            "the opencode runtime has no tool for NotebookEdit",
            id="tool-without-name",
        ),
        pytest.param("sonnet", ("Read",), "missing", "cannot read", id="settings-missing"),
        pytest.param("sonnet", ("Read",), "{not json", "no list", id="settings-no-json"),
        pytest.param("sonnet", ("Read",), "[]", "no list", id="settings-no-object"),
        pytest.param("sonnet", ("Read",), "{}", "no list", id="settings-without-permissions"),
        pytest.param(
            "sonnet",
            ("Read",),
            '{"permissions": {"allow": []}}',
            "no list",
            id="settings-without-deny",
        ),
        pytest.param(
            "sonnet",
            ("Read",),
            '{"permissions": {"deny": "Bash(git push*)"}}',
            "no list",
            id="deny-no-list",
        ),
        pytest.param(
            "sonnet",
            ("Read",),
            '{"permissions": {"deny": ["Bash(git push*)", 3]}}',
            "no list",
            id="deny-not-strings",
        ),
    ],
)
def test_a_request_the_runtime_cannot_configure_fails_before_anything_starts(
    tmp_path: Path, model: str, tools: tuple[str, ...], settings: str | None, detail: str
) -> None:
    settings_file = None
    if settings == "missing":
        settings_file = tmp_path / "missing.json"
    elif settings is not None:
        settings_file = write_agent_settings(tmp_path, settings)
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], settings_file=settings_file)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(opencode_request(tmp_path / "work", model=model, tools=tools))

    if detail == "cannot read":
        assert raised.value.detail.startswith(f"cannot read the agent settings {settings_file}: ")
    elif detail == "no list":
        assert raised.value.detail == (
            f"the agent settings {settings_file} hold no permissions.deny list"
        )
    else:
        assert raised.value.detail == detail
    assert read_calls(tmp_path / "bin") == []
    assert list((tmp_path / "state").iterdir()) == []


@pytest.mark.parametrize(
    ("with_settings", "bash"),
    [
        pytest.param(
            True,
            {"*": "allow", "git push*": "deny", "rm -rf *": "deny"},
            id="settings",
        ),
        pytest.param(False, {"*": "allow"}, id="no-settings"),
    ],
)
def test_the_configuration_defines_the_agent_from_its_definition_and_the_settings(
    tmp_path: Path, *, with_settings: bool, bash: dict[str, str]
) -> None:
    deny = ["Bash(git push*)", "Read(.env)", "Bash(rm -rf *)"]
    settings_file = (
        write_agent_settings(tmp_path, json.dumps({"permissions": {"allow": [], "deny": deny}}))
        if with_settings
        else None
    )
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], settings_file=settings_file)
    request = opencode_request(tmp_path / "work", tools=("Read", "Bash"))

    runtime.run(request)

    [call] = read_calls(tmp_path / "bin")
    config = json.loads(call.files[call.environment[CONFIG_VARIABLE]])
    instructions = result_instructions(["doing", "question"])
    assert config == {
        "autoupdate": False,
        "share": "disabled",
        "snapshot": False,
        "agent": {
            "factory-coder": {
                "mode": "primary",
                "prompt": f"Write the code.\n\n{instructions}",
                "tools": {name: name in ("read", "bash") for name in OPENCODE_TOOLS},
                "permission": {"edit": "allow", "bash": bash},
            }
        },
    }
    assert list(config["agent"]["factory-coder"]["permission"]["bash"]) == list(bash)


def test_the_call_sees_its_configuration_file_and_only_the_request_s_environment(
    tmp_path: Path,
) -> None:
    given = {
        "HOME": "/home/agent",
        "LANG": "C.UTF-8",
        API_LOGIN_VARIABLE: "request-key",
        LOGIN_VARIABLE: "request-token",
    }
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY_EVENTS)])

    runtime.run(opencode_request(tmp_path / "work", environment=given))

    [call] = read_calls(tmp_path / "bin")
    config = Path(call.environment[CONFIG_VARIABLE])
    assert config.parent == tmp_path / "state"
    assert CONFIG_NAME.fullmatch(config.name)
    assert without_locale(call.environment) == {
        "HOME": "/home/agent",
        "LANG": "C.UTF-8",
        CONFIG_VARIABLE: str(config),
        **SWITCHES,
    }


@pytest.mark.parametrize(
    ("step", "time_limit", "end_reason"),
    [
        pytest.param(Step(stdout=REPLY_EVENTS), LIMIT, "completed", id="completed"),
        pytest.param(Step(stdout=REPLY_EVENTS, exit_status=1), LIMIT, "died", id="died"),
        pytest.param(
            Step(stdout_before_wait=stdout(step_start()), wait_seconds=30),
            SHORT_LIMIT,
            "time_limit",
            id="timed-out",
        ),
    ],
)
def test_the_state_directory_holds_no_file_after_a_run(
    tmp_path: Path, step: Step, time_limit: timedelta, end_reason: str
) -> None:
    runtime = stand_in_runtime(tmp_path, [step])
    request = opencode_request(tmp_path / "work", time_limit=time_limit)

    result = runtime.run(request)

    assert result.end_reason == end_reason
    assert list((tmp_path / "state").iterdir()) == []


def test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agent_runtime(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY_EVENTS)], kill_points=kill_points)

    runtime.run(opencode_request(tmp_path / "work"))

    assert kill_points.reached(KillPoint.AGENT_RUN) == 1
    assert isinstance(runtime, AgentRuntime)


@pytest.mark.parametrize(
    ("step", "exists", "detail"),
    [
        pytest.param(
            Step(stdout="1.19.3\n", stderr="no version here", exit_status=1),
            True,
            "{executable} --version failed: no version here",
            id="exit-1",
        ),
        pytest.param(Step(stdout=""), True, "{executable} --version printed nothing", id="nothing"),
        pytest.param(Step(stdout="1.19.3\n"), False, "cannot start {executable}: ", id="missing"),
    ],
)
def test_a_version_that_cannot_be_read_names_the_reason(
    tmp_path: Path, step: Step, *, exists: bool, detail: str
) -> None:
    executable = write_opencode(tmp_path / "bin", [step])
    if not exists:
        executable = tmp_path / "bin" / "missing-opencode"
    runtime = OpencodeRuntime(str(executable), tmp_path, models=MODELS)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.version()

    expected = detail.format(executable=executable)
    if exists:
        assert raised.value.detail == expected
    else:
        assert raised.value.detail.startswith(expected)
        assert len(raised.value.detail) > len(expected)


@pytest.mark.parametrize(
    ("executable_exists", "state_exists", "detail"),
    [
        pytest.param(False, True, "cannot start {executable}: ", id="executable-missing"),
        pytest.param(True, False, "cannot write the state directory {state}: ", id="state-a-file"),
    ],
)
def test_a_run_that_cannot_start_names_the_reason(
    tmp_path: Path, *, executable_exists: bool, state_exists: bool, detail: str
) -> None:
    executable = write_opencode(tmp_path / "bin", [Step(stdout=REPLY_EVENTS)])
    if not executable_exists:
        executable = tmp_path / "bin" / "missing-opencode"
    state = tmp_path / "state"
    if state_exists:
        state.mkdir()
    else:
        state.write_text("a file where the folder should be\n", encoding="utf-8")
    runtime = OpencodeRuntime(str(executable), state, models=MODELS)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(opencode_request(tmp_path / "work"))

    expected = detail.format(executable=executable, state=state)
    assert raised.value.detail.startswith(expected)
    assert len(raised.value.detail) > len(expected)
    assert read_calls(tmp_path / "bin") == []
    if state_exists:
        assert list(state.iterdir()) == []
