"""The instance's label on every container the podman adapter starts."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.machine.adapters.podman_runs import PodmanRuns
from podman_support import IMAGE, Podman, launch_words


def _run_words(runs: PodmanRuns, podman: Podman) -> list[str]:
    runs.run(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=30),
        working_directory="/work/checkout",
    )
    return podman.calls()[0].arguments


@pytest.mark.parametrize(
    ("instance", "start"),
    [
        pytest.param("vm", lambda runs, _: launch_words(runs, ["/bin/true"], []), id="launch-vm"),
        pytest.param(
            "night", lambda runs, _: launch_words(runs, ["/bin/true"], []), id="launch-night"
        ),
        pytest.param("vm", _run_words, id="run-vm"),
    ],
)
def test_a_container_start_carries_the_instance_label_after_rm(
    tmp_path: Path, podman: Podman, instance: str, start: Callable[[PodmanRuns, Podman], list[str]]
) -> None:
    runs = PodmanRuns(str(podman.path), IMAGE, tmp_path, instance=instance)

    argv = start(runs, podman)

    assert "--label" in argv
    label = argv.index("--label")
    assert argv[label + 1] == f"factory.instance={instance}"
    assert argv.index("--rm") < label
