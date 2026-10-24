"""The preflight's probe on `main` prepares the stage environment before its `lint`."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from container_support import Dataset, container_dataset, push_main, sync_makefile
from factory.adapters.make_commands import ContainerMakeCommands
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks, Preflight
from factory.application.stops import StopService
from factory.domain.settings import InstanceSettings
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from wiring_support import every_tool

IMAGE = "build-7"
LINT = "\n.PHONY: lint\n\nlint:\n\ttrue\n"
FAILING_SYNC = "@echo boom; exit 1"


def _on_dataset(boundaries: Boundaries, tmp_path: Path, *, with_base: bool) -> Dataset:
    dataset = container_dataset(boundaries, tmp_path, with_base=with_base)
    commands = ContainerMakeCommands(
        dataset.snapshots, dataset.containers, boundaries.git, checkout=boundaries.checkout
    )
    return replace(dataset, boundaries=replace(dataset.boundaries, project_commands=commands))


@pytest.mark.parametrize(
    ("sync_recipe", "with_base", "detail"),
    [
        pytest.param(None, True, None, id="passes"),
        pytest.param(
            FAILING_SYNC,
            True,
            lambda _dataset: "container command sync failed: boom",
            id="sync-fails",
        ),
        pytest.param(
            None,
            False,
            lambda dataset: f"snapshot command reset failed: no base at {dataset.base}",
            id="no-base",
        ),
    ],
)
def test_the_lint_probe_runs_in_a_check_container_after_the_environment_is_prepared(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    human: HumanClone,
    agent_home: Path,
    sync_recipe: str | None,
    with_base: bool,
    detail: Callable[[Dataset], str] | None,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    makefile = (sync_makefile() if sync_recipe is None else sync_makefile(sync_recipe)) + LINT
    main = push_main(boundaries, human, {"Makefile": makefile})
    dataset = _on_dataset(boundaries, tmp_path, with_base=with_base)
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
        stage_environment="container",
        dataset="tank/factory/vm",
        workspace=dataset.workspace,
        stage_image="factory-stage:1",
    )
    stamps = JsonPreflightStampFile(tmp_path / "state" / "preflight-stamp.json")
    checks = MachineChecks(dataset.boundaries, settings, every_tool)
    preflight = Preflight(
        dataset.boundaries, checks, stamps, StopService(dataset.boundaries), IMAGE
    )

    reason = preflight.run()

    calls = dataset.containers.calls
    checked = [call for call in calls if "factory-check" in call.command]
    if detail is None:
        assert reason is None
        sync, check = calls
        assert "factory-sync" in sync.command
        assert "factory-check" in check.command
        assert check.command[-1] == "lint"
        stamp = stamps.read()
        assert stamp is not None
        assert stamp.main_probed == main
        return
    assert reason == "preflight_failed"
    [stop] = [stop for stop in boundaries.health.read().stops if stop.reason == reason]
    assert stop.detail == f"the probe on main could not run: {detail(dataset)}"
    assert checked == []
