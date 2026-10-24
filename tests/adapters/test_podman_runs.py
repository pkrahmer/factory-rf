"""The podman adapter's command line: the words that start one throwaway container."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.podman_runs import PodmanRuns
from factory.application.containers import ContainerRuns
from factory.domain.containers import Mount
from podman_support import Podman

IMAGE = "factory-stage:1"


@pytest.fixture
def runs(podman: Podman) -> PodmanRuns:
    return PodmanRuns(str(podman.path), IMAGE, Path("/srv/factory/vm/work"))


def test_launch_pins_the_podman_command_line(runs: PodmanRuns, podman: Podman) -> None:
    launch = runs.launch(
        ["/bin/sh", "-c", "make sync"],
        mounts=[
            Mount(source=Path("/srv/factory/vm/repo/.git"), target="/upstream", read_only=True),
            Mount(
                source=Path("/home/factory/.claude-token"),
                target="/home/factory/.claude-token",
                read_only=True,
            ),
            Mount(
                source=Path("/state/runs/instructions-1.md"),
                target="/state/runs/instructions-1.md",
            ),
        ],
        environment={"HOME": "/work/home", "PATH": "/usr/local/bin:/usr/bin:/bin"},
        time_limit=timedelta(minutes=40),
        working_directory="/work/checkout",
    )

    assert launch.argv == [
        str(podman.path),
        "run",
        "--rm",
        "--userns=keep-id",
        "--timeout",
        "2400",
        "--env",
        "HOME=/work/home",
        "--env",
        "PATH=/usr/local/bin:/usr/bin:/bin",
        "--volume",
        "/srv/factory/vm/work:/work",
        "--volume",
        "/srv/factory/vm/repo/.git:/upstream:ro",
        "--volume",
        "/home/factory/.claude-token:/home/factory/.claude-token:ro",
        "--volume",
        "/state/runs/instructions-1.md:/state/runs/instructions-1.md",
        "--workdir",
        "/work/checkout",
        IMAGE,
        "/bin/sh",
        "-c",
        "make sync",
    ]
    assert launch.env is None
    assert launch.time_limit == timedelta(minutes=40, seconds=30)


@pytest.mark.parametrize(
    ("time_limit", "seconds"),
    [
        pytest.param(timedelta(seconds=30), "30", id="whole-seconds"),
        pytest.param(timedelta(seconds=1.5), "2", id="fraction-rounds-up"),
        pytest.param(timedelta(minutes=40), "2400", id="forty-minutes"),
    ],
)
def test_timeout_is_the_time_limit_in_whole_seconds_rounded_up(
    runs: PodmanRuns, time_limit: timedelta, seconds: str
) -> None:
    argv = runs.launch(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=time_limit,
        working_directory="/work",
    ).argv

    assert argv[argv.index("--timeout") + 1] == seconds
    assert argv.count("--volume") == 1
    assert argv[argv.index("--volume") + 1] == "/srv/factory/vm/work:/work"
    assert "--env" not in argv


def _call(runs: PodmanRuns, method: str, command: list[str], mounts: list[Mount]) -> object:
    if method == "launch":
        return runs.launch(
            command,
            mounts=mounts,
            environment={},
            time_limit=timedelta(seconds=10),
            working_directory="/work",
        )
    return runs.run(
        command,
        mounts=mounts,
        environment={},
        time_limit=timedelta(seconds=10),
        working_directory="/work",
    )


@pytest.mark.parametrize("method", ["launch", "run"])
@pytest.mark.parametrize(
    ("command", "target", "refused"),
    [
        pytest.param(["/bin/true"], "/work", True, id="mount-at-work"),
        pytest.param(["/bin/true"], "/work/checkout", True, id="mount-under-work"),
        pytest.param([], None, True, id="no-command"),
        pytest.param(["/bin/true"], "/workspace", False, id="mount-at-workspace"),
    ],
)
def test_a_mount_on_the_dataset_or_no_command_is_refused(
    tmp_path: Path,
    podman: Podman,
    *,
    method: str,
    command: list[str],
    target: str | None,
    refused: bool,
) -> None:
    runs = PodmanRuns(str(podman.path), IMAGE, tmp_path)
    mounts = [] if target is None else [Mount(source=tmp_path / "source", target=target)]

    if refused:
        with pytest.raises(ValueError):  # noqa: PT011 - the interface names no message
            _call(runs, method, command, mounts)
    else:
        _call(runs, method, command, mounts)


def test_podman_runs_are_container_runs(runs: PodmanRuns) -> None:
    assert isinstance(runs, ContainerRuns)
