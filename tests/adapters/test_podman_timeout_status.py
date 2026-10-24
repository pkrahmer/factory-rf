"""A podman run that ends with podman's timeout status at its limit is a timed-out run."""

import time
from pathlib import Path

import pytest

from factory.adapters.podman_runs import PodmanRuns
from podman_support import IMAGE, Podman, PodmanPlan
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

ROOMY_SECONDS = ROOMY_LIMIT.total_seconds()


@pytest.mark.parametrize(
    ("plan", "timed_out", "exit_status"),
    [
        pytest.param(
            PodmanPlan(exit_status=255, wait_seconds=ROOMY_SECONDS),
            True,
            None,
            id="255-at-the-limit",
        ),
        pytest.param(PodmanPlan(exit_status=255), False, 255, id="255-before-the-limit"),
        pytest.param(
            PodmanPlan(exit_status=137, wait_seconds=ROOMY_SECONDS),
            True,
            None,
            id="137-at-the-limit",
        ),
    ],
)
def test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run(
    tmp_path: Path,
    podman: Podman,
    *,
    plan: PodmanPlan,
    timed_out: bool,
    exit_status: int | None,
) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    podman.plan(plan)
    runs = PodmanRuns(str(podman.path), IMAGE, workspace)
    started = time.monotonic()

    result = runs.run(
        ["/bin/true"],
        mounts=[],
        environment={},
        time_limit=ROOMY_LIMIT,
        working_directory="/work",
    )

    assert time.monotonic() - started < ROOMY_BOUND_SECONDS
    assert result.timed_out is timed_out
    assert result.exit_status == exit_status
