"""The fake container runs: a child process on the host, the mounts' paths mapped to folders."""

import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_containers import FakeContainerRuns
from factory.domain.containers import ContainerCall, ContainerResult, Mount
from factory.domain.errors import ContainerError
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

SHELL_PREFIX = ["/bin/sh", "-c", 'cd "$1" && shift && exec "$@"', "fake-container"]


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    (workspace / "checkout").mkdir(parents=True)
    return workspace


@pytest.fixture
def runs(workspace: Path) -> FakeContainerRuns:
    return FakeContainerRuns(workspace)


def _launch_word(runs: FakeContainerRuns, word: str, mounts: list[Mount]) -> str:
    launch = runs.launch(
        ["/bin/echo", word],
        mounts=mounts,
        environment={},
        time_limit=ROOMY_LIMIT,
        working_directory="/work",
    )
    return launch.argv[-1]


def test_launch_maps_the_words_environment_and_working_directory(
    runs: FakeContainerRuns, workspace: Path, tmp_path: Path
) -> None:
    launch = runs.launch(
        ["/bin/sh", "-c", 'echo "$1" "$HOME"', "x", "/work/checkout/src"],
        mounts=[
            Mount(
                source=tmp_path / "state" / "runs" / "i.md",
                target="/state/runs/i.md",
                read_only=True,
            )
        ],
        environment={"HOME": "/work/home", "PATH": "/usr/bin:/bin"},
        time_limit=timedelta(seconds=10),
        working_directory="/work/checkout",
    )

    assert launch.argv == [
        *SHELL_PREFIX,
        f"{workspace}/checkout",
        "/bin/sh",
        "-c",
        'echo "$1" "$HOME"',
        "x",
        f"{workspace}/checkout/src",
    ]
    assert launch.env == {"HOME": f"{workspace}/home", "PATH": "/usr/bin:/bin"}
    assert launch.time_limit == timedelta(seconds=10)


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        pytest.param("/state/runs/i.md", "{tmp}/state/runs/i.md", id="mount-target"),
        pytest.param("/workspace", "/workspace", id="not-under-work"),
        pytest.param("/work", "{workspace}", id="work-alone"),
    ],
)
def test_a_word_maps_only_to_a_mount_it_equals_or_lies_under(
    runs: FakeContainerRuns, workspace: Path, tmp_path: Path, word: str, expected: str
) -> None:
    mounts = [Mount(source=tmp_path / "state" / "runs" / "i.md", target="/state/runs/i.md")]

    assert _launch_word(runs, word, mounts) == expected.format(tmp=tmp_path, workspace=workspace)


def test_an_environment_key_is_never_mapped(runs: FakeContainerRuns, workspace: Path) -> None:
    launch = runs.launch(
        ["/bin/true"],
        mounts=[],
        environment={"/work": "/work"},
        time_limit=ROOMY_LIMIT,
        working_directory="/work",
    )

    assert launch.env == {"/work": str(workspace)}


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        pytest.param("/mnt/deep/x", "{tmp}/deep/x", id="deep"),
        pytest.param("/mnt/other", "{tmp}/shallow/other", id="shallow"),
        pytest.param("/mnt/deeper", "{tmp}/shallow/deeper", id="no-slash-after-deep"),
    ],
)
def test_the_longer_mount_target_wins(
    runs: FakeContainerRuns, tmp_path: Path, word: str, expected: str
) -> None:
    mounts = [
        Mount(source=tmp_path / "shallow", target="/mnt"),
        Mount(source=tmp_path / "deep", target="/mnt/deep"),
    ]

    assert _launch_word(runs, word, mounts) == expected.format(tmp=tmp_path)


def _run(
    runs: FakeContainerRuns,
    command: list[str],
    time_limit: timedelta = ROOMY_LIMIT,
    working_directory: str = "/work/checkout",
) -> ContainerResult:
    return runs.run(
        command,
        mounts=[],
        environment={"HOME": "/work/home"},
        time_limit=time_limit,
        working_directory=working_directory,
    )


@pytest.mark.parametrize(
    ("command", "time_limit", "exit_status", "timed_out", "lines"),
    [
        pytest.param(
            [
                "/bin/sh",
                "-c",
                'pwd; printf "%s\\n" "$HOME"; echo "$1"; echo err >&2',
                "x",
                "/work/checkout",
            ],
            ROOMY_LIMIT,
            0,
            False,
            ["{workspace}/checkout", "{workspace}/home", "{workspace}/checkout", "err"],
            id="success",
        ),
        pytest.param(["/bin/sh", "-c", "exit 3"], ROOMY_LIMIT, 3, False, None, id="failure"),
        pytest.param(
            ["/bin/sh", "-c", "sleep 30"], timedelta(seconds=1), None, True, None, id="time-limit"
        ),
    ],
)
def test_run_returns_the_status_the_merged_output_and_the_end(
    runs: FakeContainerRuns,
    workspace: Path,
    *,
    command: list[str],
    time_limit: timedelta,
    exit_status: int | None,
    timed_out: bool,
    lines: list[str] | None,
) -> None:
    start = time.monotonic()
    result = _run(runs, command, time_limit)
    elapsed = time.monotonic() - start

    assert result.exit_status == exit_status
    assert result.timed_out is timed_out
    assert result.duration > timedelta(0)
    if lines is not None:
        assert result.output.splitlines() == [line.format(workspace=workspace) for line in lines]
    if timed_out:
        assert 1 <= elapsed < ROOMY_BOUND_SECONDS
        assert timedelta(seconds=1) <= result.duration < timedelta(seconds=ROOMY_BOUND_SECONDS)


def test_a_program_the_shell_cannot_find_is_a_result_with_status_127(
    runs: FakeContainerRuns,
) -> None:
    result = _run(runs, ["/nowhere/program"])

    assert result.exit_status == 127
    assert result.timed_out is False
    assert "/nowhere/program" in result.output


def test_a_missing_working_directory_is_a_container_error(runs: FakeContainerRuns) -> None:
    with pytest.raises(ContainerError) as raised:
        _run(runs, ["/bin/sh", "-c", "true"], working_directory="/work/missing")

    assert raised.value.command == "/bin/sh"
    assert raised.value.detail.startswith("[Errno 2]")


Operation = Callable[[FakeContainerRuns, list[str], list[Mount]], object]


def _launch(runs: FakeContainerRuns, command: list[str], mounts: list[Mount]) -> object:
    return runs.launch(
        command,
        mounts=mounts,
        environment={},
        time_limit=ROOMY_LIMIT,
        working_directory="/work/checkout",
    )


def _run_with(runs: FakeContainerRuns, command: list[str], mounts: list[Mount]) -> object:
    return runs.run(
        command,
        mounts=mounts,
        environment={},
        time_limit=ROOMY_LIMIT,
        working_directory="/work/checkout",
    )


@pytest.mark.parametrize(
    "operation",
    [pytest.param(_launch, id="launch"), pytest.param(_run_with, id="run")],
)
@pytest.mark.parametrize(
    ("command", "target", "accepted"),
    [
        pytest.param(["/bin/sh", "-c", "true"], "/work", False, id="work"),
        pytest.param(["/bin/sh", "-c", "true"], "/work/checkout", False, id="under-work"),
        pytest.param([], "/elsewhere", False, id="no-command"),
        pytest.param(["/bin/sh", "-c", "true"], "/workspace", True, id="workspace"),
    ],
)
def test_a_mount_on_work_and_an_empty_command_are_refused_and_not_recorded(
    runs: FakeContainerRuns,
    tmp_path: Path,
    *,
    operation: Operation,
    command: list[str],
    target: str,
    accepted: bool,
) -> None:
    mounts = [Mount(source=tmp_path / "other", target=target)]

    if accepted:
        operation(runs, command, mounts)
        assert [(call.command, call.mounts) for call in runs.calls] == [(command, mounts)]
    else:
        with pytest.raises(ValueError):  # noqa: PT011 - the interface names no message
            operation(runs, command, mounts)
        assert runs.calls == []


def test_calls_records_each_accepted_call_as_given_in_order(
    runs: FakeContainerRuns, tmp_path: Path
) -> None:
    mounts = [Mount(source=tmp_path / "login", target="/login", read_only=True)]
    runs.launch(
        ["/bin/echo", "/work/checkout"],
        mounts=mounts,
        environment={"HOME": "/work/home"},
        time_limit=timedelta(seconds=7),
        working_directory="/work",
    )
    runs.run(
        ["/bin/sh", "-c", "true"],
        mounts=[],
        environment={},
        time_limit=ROOMY_LIMIT,
        working_directory="/work/checkout",
    )

    assert runs.calls == [
        ContainerCall(
            command=["/bin/echo", "/work/checkout"],
            mounts=mounts,
            environment={"HOME": "/work/home"},
            time_limit=timedelta(seconds=7),
            working_directory="/work",
        ),
        ContainerCall(
            command=["/bin/sh", "-c", "true"],
            mounts=[],
            environment={},
            time_limit=ROOMY_LIMIT,
            working_directory="/work/checkout",
        ),
    ]
