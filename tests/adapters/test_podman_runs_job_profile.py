"""The podman adapter's job profile: root in a managed sandbox, podman's global options first."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import podman_runs
from factory.adapters.podman_runs import PodmanRuns
from factory.adapters.process import ProcessResult
from factory.domain.containers import Mount
from factory.domain.errors import ContainerError
from podman_support import IMAGE, Podman, PodmanPlan
from run_process_recorder import Recorder

WORKSPACE = Path("/srv/factory/vm/work")
JOB_WORDS = [
    "--runtime=runc",
    "--cgroup-manager=cgroupfs",
    "--storage-driver=overlay",
    "--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs",
]


@pytest.fixture
def job_runs(podman: Podman) -> PodmanRuns:
    """A `PodmanRuns` of the job profile over the stand-in `podman`."""
    return PodmanRuns(str(podman.path), IMAGE, WORKSPACE, profile="job")


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    recording = Recorder()
    monkeypatch.setattr(podman_runs, "run_process", recording)
    return recording


def _launch_words(runs: PodmanRuns, command: list[str], mounts: list[Mount]) -> list[str]:
    return runs.launch(
        command,
        mounts=mounts,
        environment={"A": "1"},
        time_limit=timedelta(seconds=90),
        working_directory="/work/checkout",
    ).argv


def test_the_default_profile_launches_as_the_rootless_one(podman: Podman) -> None:
    mounts = [Mount(source=Path("/srv/upstream"), target="/upstream", read_only=True)]
    default = PodmanRuns(str(podman.path), IMAGE, WORKSPACE)
    rootless = PodmanRuns(str(podman.path), IMAGE, WORKSPACE, profile="rootless")

    assert _launch_words(default, ["make", "check"], mounts) == _launch_words(
        rootless, ["make", "check"], mounts
    )


def test_a_job_launch_puts_the_global_options_first_and_runs_on_the_host_network(
    job_runs: PodmanRuns, podman: Podman
) -> None:
    launch = job_runs.launch(
        ["make", "check"],
        mounts=[
            Mount(source=Path("/state/runs/record"), target="/state/runs/record"),
            Mount(source=Path("/srv/upstream"), target="/upstream", read_only=True),
        ],
        environment={"A": "1"},
        time_limit=timedelta(seconds=90),
        working_directory="/work/checkout",
    )

    assert launch.argv == [
        str(podman.path),
        *JOB_WORDS,
        "run",
        "--rm",
        "--http-proxy=false",
        "--network=host",
        "--timeout",
        "90",
        "--cap-drop=all",
        "--security-opt=no-new-privileges",
        "--pids-limit=4096",
        "--memory=4g",
        "--env",
        "A=1",
        "--volume",
        "/srv/factory/vm/work:/work",
        "--volume",
        "/state/runs/record:/state/runs/record",
        "--volume",
        "/srv/upstream:/upstream:ro",
        "--workdir",
        "/work/checkout",
        IMAGE,
        "make",
        "check",
    ]
    assert launch.time_limit == timedelta(seconds=90) + podman_runs.CONTAINER_GRACE
    assert launch.env is None


def test_a_job_launch_maps_no_user(job_runs: PodmanRuns) -> None:
    words = _launch_words(job_runs, ["make", "check"], [])

    assert "--userns=keep-id" not in words
    assert "--user" not in words


@pytest.mark.parametrize(
    ("command", "target"),
    [
        pytest.param([], None, id="no-command"),
        pytest.param(["/bin/true"], "/work", id="mount-at-work"),
        pytest.param(["/bin/true"], "/work/x", id="mount-under-work"),
    ],
)
def test_a_job_launch_refuses_no_command_or_a_mount_on_the_dataset(
    job_runs: PodmanRuns, tmp_path: Path, command: list[str], target: str | None
) -> None:
    mounts = [] if target is None else [Mount(source=tmp_path / "source", target=target)]

    with pytest.raises(ValueError):  # noqa: PT011 - the interface names no message
        _launch_words(job_runs, command, mounts)


def _version(runs: PodmanRuns) -> object:
    return runs.version()


def _image_exists(runs: PodmanRuns) -> object:
    return runs.image_exists()


@pytest.mark.parametrize(
    ("query", "arguments", "plan", "expected"),
    [
        pytest.param(
            _version,
            ["--version"],
            PodmanPlan(stdout="podman version 5.4.2\n"),
            "podman version 5.4.2",
            id="version",
        ),
        pytest.param(_version, ["--version"], PodmanPlan(exit_status=2), None, id="version-fault"),
        pytest.param(_image_exists, ["image", "exists", IMAGE], PodmanPlan(), True, id="exists"),
        pytest.param(
            _image_exists,
            ["image", "exists", IMAGE],
            PodmanPlan(exit_status=1),
            False,
            id="missing",
        ),
        pytest.param(
            _image_exists,
            ["image", "exists", IMAGE],
            PodmanPlan(exit_status=125),
            None,
            id="exists-fault",
        ),
    ],
)
def test_a_job_runner_s_queries_carry_the_global_options(
    job_runs: PodmanRuns,
    podman: Podman,
    *,
    query: Callable[[PodmanRuns], object],
    arguments: list[str],
    plan: PodmanPlan,
    expected: object,
) -> None:
    podman.plan(plan)

    if expected is None:
        with pytest.raises(ContainerError):
            query(job_runs)
    else:
        assert query(job_runs) == expected
    assert [call.arguments for call in podman.calls()] == [[*JOB_WORDS, *arguments]]


@pytest.mark.parametrize(
    ("exit_status", "seconds", "timed_out", "expected_status"),
    [
        pytest.param(255, 90, True, None, id="255-at-the-limit"),
        pytest.param(255, 91, True, None, id="255-after-the-limit"),
        pytest.param(255, 89, False, 255, id="255-before-the-limit"),
        pytest.param(125, 1, False, 125, id="podman-s-own-fault"),
    ],
)
def test_a_job_run_reads_its_end_as_the_rootless_one(
    job_runs: PodmanRuns,
    recorder: Recorder,
    *,
    exit_status: int,
    seconds: int,
    timed_out: bool,
    expected_status: int | None,
) -> None:
    recorder.results.append(
        ProcessResult(
            exit_status=exit_status,
            stdout="",
            stderr="",
            timed_out=False,
            duration=timedelta(seconds=seconds),
        )
    )

    result = job_runs.run(
        ["make", "check"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=90),
        working_directory="/work/checkout",
    )

    assert result.timed_out is timed_out
    assert result.exit_status == expected_status
    [request] = recorder.requests
    assert request.argv[1:5] == JOB_WORDS
