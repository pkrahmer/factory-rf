"""The `opencode run` runtime starts each call in a container, played by the fake container runs."""

import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.container_runtime_support import (
    container_environment,
    files_in,
    make_workspace,
    read_only,
    write_record_program,
)
from adapters.opencode_stand_in import (
    MODELS,
    REPLY,
    opencode_request,
    stdout,
    step_finish,
    step_start,
    write_opencode,
)
from adapters.test_agent_launch_login import API_LOGIN
from factory.adapters import opencode_runtime
from factory.adapters.agent_launch import VERSION_TIME_LIMIT, LoginFiles, login_argv
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.process import ProcessRequest, ProcessResult, Stream
from factory.domain.agent_runs import AgentRunRequest
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
    return opencode_request(
        tmp_path / "work",
        environment=container_environment(tmp_path / "bin"),
        time_limit=time_limit,
        os_user=os_user,
    )


def _api_login(tmp_path: Path) -> Path:
    path = tmp_path / "login" / "api"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    return path


def _state(tmp_path: Path) -> Path:
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    return state


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    fake: FakeContainerRuns,
    *,
    api_login_file: Path | None = None,
) -> OpencodeRuntime:
    executable = write_opencode(tmp_path / "bin", steps)
    return OpencodeRuntime(
        str(executable),
        _state(tmp_path),
        models=MODELS,
        containers=fake,
        api_login_file=api_login_file,
    )


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
    state = _state(tmp_path)

    if not with_containers:
        assert OpencodeRuntime("opencode", state).containers is None
        return
    if refused:
        with pytest.raises(ValueError, match=r".+"):
            OpencodeRuntime("opencode", state, containers=fake, confine_executable=confine)
        return
    assert OpencodeRuntime("opencode", state, containers=fake).containers is fake


@pytest.mark.parametrize("api", [pytest.param(False, id="no-login"), pytest.param(True, id="api")])
def test_a_run_in_a_container_mounts_the_login_and_configuration_and_completes(
    tmp_path: Path, workspace: Path, fake: FakeContainerRuns, *, api: bool
) -> None:
    api_file = _api_login(tmp_path) if api else None
    runtime = _runtime(tmp_path, [REPLY], fake, api_login_file=api_file)
    state = tmp_path / "state"

    result = runtime.run(_request(tmp_path))

    assert (result.end_reason, result.decision, result.entry) == (
        "completed",
        "doing",
        "Built it.",
    )
    [call] = fake.calls
    config = call.mounts[-1].source
    assert config.parent == state
    assert config.name.startswith("opencode-")
    start = call.command.index(str(tmp_path / "bin" / "opencode"))
    assert call.command[:start] == login_argv(LoginFiles(api=api_file))
    assert call.command[start + 1] == "run"
    logins = [] if api_file is None else [read_only(api_file)]
    assert call.mounts == [*logins, read_only(config)]
    assert call.environment == {
        **container_environment(tmp_path / "bin"),
        "OPENCODE_CONFIG": str(config),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    assert call.time_limit == LIMIT
    assert call.working_directory == WORK_CHECKOUT
    [seen] = read_calls(tmp_path / "bin")
    assert seen.working_directory.resolve() == (workspace / "checkout").resolve()
    assert seen.environment["HOME"] == str(workspace / "home")
    assert not config.exists()
    assert files_in(state) == []
    assert not any(API_LOGIN in word for word in call.command)
    assert not any(API_LOGIN in value for value in call.environment.values())


def test_a_run_in_a_container_reports_the_login_read_from_the_mounted_file(
    tmp_path: Path, fake: FakeContainerRuns
) -> None:
    runtime = _runtime(tmp_path, [REPLY], fake, api_login_file=_api_login(tmp_path))

    result = runtime.run(_request(tmp_path))

    assert result.login == "api_key"


def test_a_request_with_an_operating_system_user_is_refused_in_a_container(
    tmp_path: Path, fake: FakeContainerRuns
) -> None:
    runtime = _runtime(tmp_path, [REPLY], fake)

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
        return ProcessResult(
            exit_status=137,
            stdout=stdout(step_start(), step_finish()),
            stderr="",
            timed_out=False,
            duration=timedelta(seconds=seconds),
        )

    monkeypatch.setattr(opencode_runtime, "run_streaming", answer)
    runtime = OpencodeRuntime("opencode", _state(tmp_path), models=MODELS, containers=fake)

    result = runtime.run(_request(tmp_path, time_limit=timedelta(seconds=30)))

    assert result.end_reason == end_reason
    assert len(requests) == 1


@pytest.mark.parametrize(
    "version_time_limit",
    [pytest.param(None, id="default"), pytest.param(timedelta(seconds=7), id="given")],
)
def test_the_version_runs_in_a_container_with_the_version_time_limit(
    tmp_path: Path, fake: FakeContainerRuns, version_time_limit: timedelta | None
) -> None:
    executable = write_opencode(tmp_path / "bin", [Step(stdout="1.19.3\n")])
    state = _state(tmp_path)
    runtime = (
        OpencodeRuntime(str(executable), state, containers=fake)
        if version_time_limit is None
        else OpencodeRuntime(
            str(executable), state, containers=fake, version_time_limit=version_time_limit
        )
    )

    version = runtime.version()

    assert version == "1.19.3"
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
    executable = write_opencode(tmp_path / "bin", [REPLY])
    runtime = OpencodeRuntime(str(executable), _state(tmp_path), models=MODELS)
    request = _request(tmp_path)

    result = runtime.run(request)

    assert result.end_reason == "completed"
    [seen] = read_calls(tmp_path / "bin")
    assert seen.working_directory.resolve() == request.working_directory.resolve()


def test_a_call_in_a_container_starts_no_leftovers_program_and_no_temporary_folder(
    tmp_path: Path, fake: FakeContainerRuns, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorder = Recorder()
    monkeypatch.setattr(opencode_runtime, "run_process", recorder)
    program, record = write_record_program(tmp_path / "leftovers-bin")
    temporary_root = tmp_path / "temporary"
    temporary_root.mkdir()
    executable = write_opencode(tmp_path / "bin", [REPLY])
    runtime = OpencodeRuntime(
        str(executable),
        _state(tmp_path),
        models=MODELS,
        containers=fake,
        leftovers=[str(program)],
        temporary_root=temporary_root,
    )

    result = runtime.run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert not record.exists()
    assert recorder.requests == []
    assert files_in(temporary_root) == []
