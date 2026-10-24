"""The boundaries choose the environment: containers with snapshots and containers, else inline."""

from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import (
    ContainerEnvironment,
    InlineEnvironment,
    StageEnvironment,
    stage_environment_of,
)


@pytest.mark.parametrize(
    ("with_snapshots", "with_containers", "expected"),
    [
        pytest.param(True, True, ContainerEnvironment, id="both"),
        pytest.param(True, False, InlineEnvironment, id="snapshots-only"),
        pytest.param(False, True, InlineEnvironment, id="containers-only"),
        pytest.param(False, False, InlineEnvironment, id="neither"),
    ],
)
def test_the_container_environment_needs_both_snapshots_and_containers(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    with_snapshots: bool,
    with_containers: bool,
    expected: type[StageEnvironment],
) -> None:
    workspace = tmp_path / "workspace"
    snapshots = FakeSnapshots(workspace, tmp_path / "base") if with_snapshots else None
    containers = FakeContainerRuns(workspace) if with_containers else None

    environment = stage_environment_of(
        replace(boundaries, snapshots=snapshots, containers=containers)
    )

    assert type(environment) is expected
