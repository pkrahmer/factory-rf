"""The podman adapter's results and faults: a run's end, `version()` and `image_exists()`."""

import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import process
from factory.adapters.podman_runs import PODMAN_TIME_LIMIT, PodmanRuns
from factory.adapters.process import ProcessResult
from factory.domain.errors import ContainerError
from podman_support import IMAGE, Podman, PodmanPlan
from run_process_recorder import Recorder
from time_limits import ROOMY_BOUND_SECONDS


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "work"
    workspace.mkdir()
    return workspace


@pytest.fixture
def runs(podman: Podman, workspace: Path) -> PodmanRuns:
    return PodmanRuns(str(podman.path), IMAGE, workspace)


def test_a_run_passes_the_command_s_status_and_output_through(
    runs: PodmanRuns, podman: Podman, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_PROBE_VARIABLE", "probe")
    podman.plan(PodmanPlan(image=IMAGE))

    result = runs.run(
        ["/bin/sh", "-c", "echo out; echo err >&2; exit 3"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=10),
        working_directory="/work",
    )

    assert result.exit_status == 3
    assert result.timed_out is False
    assert "out" in result.output
    assert "err" in result.output
    [call] = podman.calls()
    assert call.environment["FACTORY_PROBE_VARIABLE"] == "probe"
    assert call.working_directory == Path("/")


@pytest.mark.parametrize(
    ("plan", "answer", "time_limit", "timed_out", "exit_status"),
    [
        pytest.param(
            PodmanPlan(exit_status=137, wait_seconds=3),
            None,
            timedelta(seconds=3),
            True,
            None,
            id="137-at-the-limit",
        ),
        pytest.param(
            PodmanPlan(exit_status=137),
            None,
            timedelta(seconds=30),
            False,
            137,
            id="137-before-the-limit",
        ),
        pytest.param(
            PodmanPlan(exit_status=-9, wait_seconds=2),
            None,
            timedelta(seconds=2),
            True,
            None,
            id="sigkill-at-the-limit",
        ),
        pytest.param(
            PodmanPlan(),
            ProcessResult(
                exit_status=None,
                stdout="",
                stderr="",
                timed_out=True,
                duration=timedelta(seconds=31),
            ),
            timedelta(seconds=1),
            True,
            None,
            id="the-factory-s-own-kill",
        ),
        pytest.param(
            PodmanPlan(),
            ProcessResult(
                exit_status=1,
                stdout="",
                stderr="",
                timed_out=False,
                duration=timedelta(seconds=5),
            ),
            timedelta(seconds=1),
            False,
            1,
            id="other-status-after-the-limit",
        ),
    ],
)
def test_a_kill_at_the_limit_is_a_timed_out_run(
    runs: PodmanRuns,
    podman: Podman,
    podman_recorder: Recorder,
    *,
    plan: PodmanPlan,
    answer: ProcessResult | None,
    time_limit: timedelta,
    timed_out: bool,
    exit_status: int | None,
) -> None:
    podman.plan(plan)
    if answer is not None:
        podman_recorder.results.append(answer)

    result = runs.run(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=time_limit,
        working_directory="/work",
    )

    assert result.timed_out is timed_out
    assert result.exit_status == exit_status
    [request] = podman_recorder.requests
    assert request.time_limit == time_limit + timedelta(seconds=30)
    assert request.merge_stderr is True
    assert request.cwd == Path("/")


def test_podman_s_own_fault_is_its_exit_status(runs: PodmanRuns, podman: Podman) -> None:
    podman.plan(PodmanPlan(exit_status=125, stderr="Error: factory-stage:1: image not known\n"))

    result = runs.run(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=10),
        working_directory="/work",
    )

    assert result.exit_status == 125
    assert result.timed_out is False
    assert "Error: factory-stage:1: image not known" in result.output


def test_a_podman_that_cannot_start_is_a_container_error_of_the_command(
    tmp_path: Path, workspace: Path
) -> None:
    runs = PodmanRuns(str(tmp_path / "nowhere"), IMAGE, workspace)

    with pytest.raises(ContainerError) as raised:
        runs.run(
            ["/bin/true"],
            mounts=[],
            environment={},
            time_limit=timedelta(seconds=10),
            working_directory="/work",
        )

    assert raised.value.command == "/bin/true"
    assert raised.value.detail.startswith("[Errno 2]")


@dataclass(frozen=True)
class Fault:
    """The `ContainerError` a row expects: its detail, whole or as a prefix."""

    detail: str
    prefix: bool = False


@dataclass(frozen=True)
class Row:
    """One query of the stand-in: its plan, the adapter's limit, the answer or fault expected."""

    plan: PodmanPlan | None  # None: the executable does not exist
    expected: str | bool | Fault
    time_limit: timedelta | None = None
    at_least_seconds: float = 0


def _adapter(tmp_path: Path, podman: Podman, workspace: Path, row: Row) -> tuple[str, PodmanRuns]:
    if row.plan is None:
        executable = str(tmp_path / "nowhere")
    else:
        executable = str(podman.path)
        podman.plan(row.plan)
    if row.time_limit is None:
        return executable, PodmanRuns(executable, IMAGE, workspace)
    return executable, PodmanRuns(executable, IMAGE, workspace, time_limit=row.time_limit)


def _check_fault(raised: ContainerError, command: str, fault: Fault) -> None:
    assert raised.command == command
    if fault.prefix:
        assert raised.detail.startswith(fault.detail)
    else:
        assert raised.detail == fault.detail


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(
            Row(PodmanPlan(stdout="podman version 4.9.3\n"), "podman version 4.9.3"),
            id="version",
        ),
        pytest.param(Row(PodmanPlan(), Fault("printed nothing")), id="printed-nothing"),
        pytest.param(
            Row(
                PodmanPlan(exit_status=1, stderr="podman: command not found\n"),
                Fault("podman: command not found"),
            ),
            id="failed-with-a-line",
        ),
        pytest.param(Row(PodmanPlan(exit_status=2), Fault("exit status 2")), id="failed-silently"),
        pytest.param(
            Row(
                PodmanPlan(wait_seconds=60),
                Fault("no end within 1 s"),
                time_limit=timedelta(seconds=1),
                at_least_seconds=1,
            ),
            id="time-limit",
        ),
        pytest.param(Row(None, Fault("[Errno 2]", prefix=True)), id="cannot-start"),
    ],
)
def test_version_is_the_first_line_podman_prints(
    tmp_path: Path, podman: Podman, workspace: Path, row: Row
) -> None:
    executable, runs = _adapter(tmp_path, podman, workspace, row)
    started = time.monotonic()

    if isinstance(row.expected, Fault):
        with pytest.raises(ContainerError) as raised:
            runs.version()
        _check_fault(raised.value, f"{executable} --version", row.expected)
    else:
        assert runs.version() == row.expected
        assert [call.arguments for call in podman.calls()] == [["--version"]]
        assert [call.working_directory for call in podman.calls()] == [workspace]

    elapsed = time.monotonic() - started
    assert row.at_least_seconds <= elapsed < ROOMY_BOUND_SECONDS


def test_version_runs_under_two_minutes_by_default(
    runs: PodmanRuns, podman_recorder: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(process, "run_process", podman_recorder)
    podman_recorder.results.append(
        ProcessResult(
            exit_status=0,
            stdout="podman version 4.9.3\n",
            stderr="",
            timed_out=False,
            duration=timedelta(seconds=1),
        )
    )

    runs.version()

    assert timedelta(minutes=2) == PODMAN_TIME_LIMIT
    [request] = podman_recorder.requests
    assert request.time_limit == timedelta(minutes=2)


@pytest.mark.parametrize(
    "row",
    [
        pytest.param(Row(PodmanPlan(), True), id="exists"),
        pytest.param(Row(PodmanPlan(exit_status=1), False), id="missing"),
        pytest.param(
            Row(
                PodmanPlan(exit_status=125, stderr="Error: cannot connect\n"),
                Fault("Error: cannot connect"),
            ),
            id="failed-with-a-line",
        ),
        pytest.param(Row(PodmanPlan(exit_status=2), Fault("exit status 2")), id="failed-silently"),
        pytest.param(
            Row(
                PodmanPlan(wait_seconds=60),
                Fault("no end within 2 s"),
                time_limit=timedelta(seconds=1.5),
                at_least_seconds=1.5,
            ),
            id="time-limit",
        ),
        pytest.param(Row(None, Fault("[Errno 2]", prefix=True)), id="cannot-start"),
    ],
)
def test_image_exists_reads_podman_s_exit_status(
    tmp_path: Path, podman: Podman, workspace: Path, row: Row
) -> None:
    executable, runs = _adapter(tmp_path, podman, workspace, row)
    started = time.monotonic()

    if isinstance(row.expected, Fault):
        with pytest.raises(ContainerError) as raised:
            runs.image_exists()
        _check_fault(raised.value, f"{executable} image exists {IMAGE}", row.expected)
    else:
        assert runs.image_exists() is row.expected
        assert [call.arguments for call in podman.calls()] == [["image", "exists", IMAGE]]
        assert [call.working_directory for call in podman.calls()] == [workspace]

    elapsed = time.monotonic() - started
    assert row.at_least_seconds <= elapsed < ROOMY_BOUND_SECONDS
