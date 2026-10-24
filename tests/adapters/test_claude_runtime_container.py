"""The `claude -p` runtime starts each call in a container, played by the fake container runs."""

import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.container_runtime_support import (
    container_environment,
    files_in,
    make_workspace,
    read_only,
    write_record_program,
)
from adapters.test_agent_launch_login import API_LOGIN
from adapters.test_claude_runtime_login import BUDGET_STOP, LOGIN, REPLY
from factory.adapters.agent_launch import (
    LOGIN_VARIABLE,
    VERSION_TIME_LIMIT,
    LoginFiles,
    login_argv,
)
from factory.adapters.claude_runtime import SWITCHES, ClaudeCodeRuntime
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.process import ProcessResult
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.containers import WORK_CHECKOUT, ContainerCall
from factory.domain.errors import AgentRuntimeError
from run_process_recorder import Recorder
from time_limits import ROOMY_BOUND_SECONDS

LIMIT = timedelta(seconds=30)
OS_USER_DETAIL = "a run in a container has no operating-system user"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return make_workspace(tmp_path)


@pytest.fixture
def fake(workspace: Path) -> FakeContainerRuns:
    return FakeContainerRuns(workspace)


def _request(
    tmp_path: Path, *, time_limit: timedelta = LIMIT, os_user: str | None = None
) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read", "Edit"],
            budget_usd=Decimal("3"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["review", "doing", "question"],
        time_limit=time_limit,
        working_directory=work,
        environment=container_environment(tmp_path / "bin"),
        os_user=os_user,
    )


def _write_login(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{text}\n", encoding="utf-8")
    return path


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    fake: FakeContainerRuns,
    *,
    login_file: Path | None = None,
    api_login_file: Path | None = None,
) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    return ClaudeCodeRuntime(
        str(executable),
        tmp_path / "state",
        containers=fake,
        login_file=login_file,
        api_login_file=api_login_file,
    )


def _after(words: list[str], flag: str) -> str:
    return words[words.index(flag) + 1]


@pytest.mark.parametrize(
    ("with_containers", "with_confine", "refused"),
    [
        pytest.param(True, True, True, id="containers-and-confine"),
        pytest.param(True, False, False, id="containers-alone"),
        pytest.param(False, False, False, id="without-containers"),
    ],
)
def test_a_runtime_keeps_its_containers_and_refuses_them_with_a_confine_executable(
    tmp_path: Path,
    fake: FakeContainerRuns,
    *,
    with_containers: bool,
    with_confine: bool,
    refused: bool,
) -> None:
    confine = "factory-confine" if with_confine else None
    state = tmp_path / "state"

    if not with_containers:
        assert ClaudeCodeRuntime("claude", state).containers is None
        return
    if refused:
        with pytest.raises(ValueError, match=r".+"):
            ClaudeCodeRuntime("claude", state, containers=fake, confine_executable=confine)
        return
    assert ClaudeCodeRuntime("claude", state, containers=fake).containers is fake


@pytest.mark.parametrize(
    ("subscription", "api"),
    [
        pytest.param(True, False, id="token-file"),
        pytest.param(True, True, id="token-and-api-files"),
    ],
)
def test_a_run_in_a_container_mounts_the_logins_and_instructions_and_completes(
    tmp_path: Path, workspace: Path, fake: FakeContainerRuns, *, subscription: bool, api: bool
) -> None:
    token = _write_login(tmp_path / "login" / "token", LOGIN) if subscription else None
    api_file = _write_login(tmp_path / "login" / "api", API_LOGIN) if api else None
    runtime = _runtime(
        tmp_path, [Step(stdout=REPLY)], fake, login_file=token, api_login_file=api_file
    )
    request = _request(tmp_path)
    given = {**request.environment, LOGIN_VARIABLE: "request-login"}
    request = request.model_copy(update={"environment": given})
    state = tmp_path / "state"

    result = runtime.run(request)

    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")
    [call] = fake.calls
    instructions = Path(_after(call.command, "--append-system-prompt-file"))
    assert instructions.parent == state
    assert instructions.name.startswith("instructions-")
    executable = str(tmp_path / "bin" / "claude")
    start = call.command.index(executable)
    assert call.command[:start] == login_argv(LoginFiles(subscription=token, api=api_file))
    assert call.command[start + 1] == "-p"
    logins = [path for path in (token, api_file) if path is not None]
    assert call.mounts == [*(read_only(path) for path in logins), read_only(instructions)]
    assert call.environment == {**container_environment(tmp_path / "bin"), **SWITCHES}
    assert "CLAUDE_CONFIG_DIR" not in call.environment
    assert call.time_limit == LIMIT
    assert call.working_directory == WORK_CHECKOUT
    [seen] = read_calls(tmp_path / "bin")
    assert seen.working_directory.resolve() == (workspace / "checkout").resolve()
    assert seen.environment["HOME"] == str(workspace / "home")
    assert files_in(state) == []
    for secret in (LOGIN, API_LOGIN):
        assert not any(secret in word for word in call.command)
        assert not any(secret in value for value in call.environment.values())


def test_a_run_in_a_container_reports_the_login_read_from_the_mounted_file(
    tmp_path: Path, fake: FakeContainerRuns
) -> None:
    token = _write_login(tmp_path / "login" / "token", LOGIN)
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)], fake, login_file=token)

    result = runtime.run(_request(tmp_path))

    assert result.login == "subscription"


def test_a_request_with_an_operating_system_user_is_refused_in_a_container(
    tmp_path: Path, fake: FakeContainerRuns
) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=REPLY)], fake)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(_request(tmp_path, os_user="agent"))

    assert raised.value.detail == OS_USER_DETAIL
    assert fake.calls == []
    assert files_in(tmp_path / "state") == []


@pytest.mark.parametrize(
    ("step", "time_limit", "end_reason"),
    [
        pytest.param(
            Step(wait_seconds=3, exit_status=137),
            timedelta(seconds=3),
            "time_limit",
            id="137-at-the-limit",
        ),
        pytest.param(Step(exit_status=137), timedelta(seconds=30), "died", id="137-at-once"),
    ],
)
def test_a_container_killed_at_its_limit_ends_time_limit_without_a_resume(
    tmp_path: Path, fake: FakeContainerRuns, step: Step, time_limit: timedelta, end_reason: str
) -> None:
    runtime = _runtime(tmp_path, [step], fake)

    started = time.monotonic()
    result = runtime.run(_request(tmp_path, time_limit=time_limit))
    elapsed = time.monotonic() - started

    assert result.end_reason == end_reason
    assert elapsed < ROOMY_BOUND_SECONDS
    assert len(fake.calls) == 1
    if end_reason == "time_limit":
        assert (result.cost_usd, result.turns, result.tokens) == (None, None, None)


@pytest.mark.parametrize(
    ("seconds", "end_reason"),
    [pytest.param(30.0, "time_limit", id="at-the-limit"), pytest.param(29.9, "died", id="before")],
)
def test_podman_s_kill_status_at_the_limit_is_read_as_the_time_limit(
    tmp_path: Path, fake: FakeContainerRuns, recorder: Recorder, seconds: float, end_reason: str
) -> None:
    recorder.results = [
        ProcessResult(
            exit_status=137,
            stdout=REPLY,
            stderr="",
            timed_out=False,
            duration=timedelta(seconds=seconds),
        )
    ]
    runtime = ClaudeCodeRuntime("claude", tmp_path / "state", containers=fake)

    result = runtime.run(_request(tmp_path, time_limit=timedelta(seconds=30)))

    assert result.end_reason == end_reason


def test_a_budget_stop_in_a_container_is_resumed_with_the_same_mounts(
    tmp_path: Path, fake: FakeContainerRuns
) -> None:
    steps = [Step(stdout=BUDGET_STOP, exit_status=1), Step(stdout=REPLY)]
    runtime = _runtime(tmp_path, steps, fake)

    result = runtime.run(_request(tmp_path))

    assert result.decision == "doing"
    first, second = fake.calls
    assert "--resume" in second.command
    assert second.mounts == first.mounts


@pytest.mark.parametrize(
    "version_time_limit",
    [pytest.param(None, id="default"), pytest.param(timedelta(seconds=7), id="given")],
)
def test_the_version_runs_in_a_container_with_the_version_time_limit(
    tmp_path: Path, fake: FakeContainerRuns, version_time_limit: timedelta | None
) -> None:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout="2.1.289 (Claude Code)\n")])
    state = tmp_path / "state"
    runtime = (
        ClaudeCodeRuntime(str(executable), state, containers=fake)
        if version_time_limit is None
        else ClaudeCodeRuntime(
            str(executable), state, containers=fake, version_time_limit=version_time_limit
        )
    )

    version = runtime.version()

    assert version == "2.1.289"
    assert fake.calls == [
        ContainerCall(
            command=[str(executable), "--version"],
            mounts=[],
            environment={},
            time_limit=VERSION_TIME_LIMIT if version_time_limit is None else version_time_limit,
            working_directory=WORK_CHECKOUT,
        )
    ]


def test_without_containers_the_call_runs_in_the_request_s_working_directory(
    tmp_path: Path,
) -> None:
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state")
    request = _request(tmp_path)

    result = runtime.run(request)

    assert result.end_reason == "completed"
    [seen] = read_calls(tmp_path / "bin")
    assert seen.working_directory.resolve() == request.working_directory.resolve()


def test_a_call_in_a_container_starts_no_leftovers_program_and_no_temporary_folder(
    tmp_path: Path, fake: FakeContainerRuns, recorder: Recorder
) -> None:
    program, record = write_record_program(tmp_path / "leftovers-bin")
    temporary_root = tmp_path / "temporary"
    temporary_root.mkdir()
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    runtime = ClaudeCodeRuntime(
        str(executable),
        tmp_path / "state",
        containers=fake,
        leftovers=[str(program)],
        temporary_root=temporary_root,
    )

    result = runtime.run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert not record.exists()
    assert len(recorder.requests) == 1
    assert files_in(temporary_root) == []
