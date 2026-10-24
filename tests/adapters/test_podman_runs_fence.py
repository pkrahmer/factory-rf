"""The podman adapter's fence: every container runs without rights and within limits."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import podman_runs
from factory.adapters.podman_runs import MEMORY_LIMIT, PIDS_LIMIT, PodmanRuns
from factory.domain.containers import Mount
from podman_support import IMAGE, Podman

FENCE = [
    "--cap-drop=all",
    "--security-opt=no-new-privileges",
    "--pids-limit=4096",
    "--memory=4g",
]


def test_launch_drops_every_right_and_limits_the_container(
    runs: PodmanRuns, podman: Podman
) -> None:
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
        *FENCE,
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
    assert not [word for word in launch.argv if word.startswith("--network")]


def test_a_run_starts_its_container_without_rights_and_within_limits(
    tmp_path: Path, podman: Podman
) -> None:
    runs = PodmanRuns(str(podman.path), IMAGE, tmp_path)

    runs.run(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=10),
        working_directory="/work",
    )

    [call] = podman.calls()
    after_timeout = call.arguments.index("--timeout") + 2
    assert call.arguments[after_timeout : after_timeout + len(FENCE)] == FENCE


def test_the_limits_are_built_from_the_constants(
    runs: PodmanRuns, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert PIDS_LIMIT == 4096
    assert MEMORY_LIMIT == "4g"
    monkeypatch.setattr(podman_runs, "PIDS_LIMIT", 64)
    monkeypatch.setattr(podman_runs, "MEMORY_LIMIT", "64m")

    argv = runs.launch(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=5),
        working_directory="/work",
    ).argv

    after_timeout = argv.index("--timeout") + 2
    assert argv[after_timeout : after_timeout + 4] == [
        *FENCE[:2],
        "--pids-limit=64",
        "--memory=64m",
    ]
