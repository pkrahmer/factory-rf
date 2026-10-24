"""The probe of the agent run prepares the stage environment for `main` before it runs."""

from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from container_support import (
    SYNC_MARKER,
    Dataset,
    container_dataset,
    container_instance_settings,
    dataset_git,
    push_main,
    sync_makefile,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.preflight import PROBE_PROMPT, agent_run_probe_item
from factory.domain.git import GitOptions
from factory.domain.settings import InstanceSettings
from git_support import TEST_IDENTITY, clone, install_agents, run_git
from human_clone import HumanClone
from probe_support import COMPLETED, ENVIRONMENT


@pytest.fixture
def container_settings(tmp_path: Path, agent_home: Path) -> InstanceSettings:
    """Settings of a container instance whose agents are in the test's agent home."""
    return container_instance_settings(tmp_path, agent_home)


@pytest.fixture
def coder(agent_home: Path) -> None:
    """Install the agent `coder` into the test's agent home."""
    install_agents(agent_home, ["coder"])


@pytest.mark.usefixtures("coder")
def test_the_probe_runs_after_the_dataset_is_prepared_for_main(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    human: HumanClone,
    agent_runtime: FakeAgentRuntime,
    container_settings: InstanceSettings,
) -> None:
    dataset = container_dataset(boundaries, tmp_path)
    main = push_main(boundaries, human, {"Makefile": sync_makefile()})
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(dataset.boundaries, container_settings, ENVIRONMENT)

    assert item.passed
    assert dataset_git(dataset, "rev-parse", "HEAD").strip() == main
    assert dataset_git(dataset, "symbolic-ref", "--short", "HEAD").strip() == "main"
    assert (dataset.workspace / "checkout" / SYNC_MARKER).is_file()
    assert dataset.snapshots.changed_paths() == []
    [request] = agent_runtime.requests()
    assert request.prompt == PROBE_PROMPT
    assert request.allowed_decisions == ["question"]
    assert request.agent.budget_usd == Decimal("0.10")


def _without_main(boundaries: Boundaries, _human: HumanClone, tmp_path: Path) -> Dataset:
    empty = tmp_path / "empty.git"
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", empty.name)
    directory = clone(empty, tmp_path / "empty-checkout")
    git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
    return container_dataset(replace(boundaries, git=git, checkout=directory), tmp_path)


def _without_base(boundaries: Boundaries, human: HumanClone, tmp_path: Path) -> Dataset:
    push_main(boundaries, human, {"Makefile": sync_makefile()})
    return container_dataset(boundaries, tmp_path, with_base=False)


def _failing_sync(boundaries: Boundaries, human: HumanClone, tmp_path: Path) -> Dataset:
    push_main(boundaries, human, {"Makefile": sync_makefile("@echo boom; exit 1")})
    return container_dataset(boundaries, tmp_path)


@pytest.mark.usefixtures("coder")
@pytest.mark.parametrize(
    ("arrange", "detail"),
    [
        pytest.param(
            _without_main,
            lambda _dataset: "no origin/main to prepare the stage environment from",
            id="no-main",
        ),
        pytest.param(
            _without_base,
            lambda dataset: f"snapshot command reset failed: no base at {dataset.base}",
            id="no-base",
        ),
        pytest.param(
            _failing_sync, lambda _dataset: "container command sync failed: boom", id="sync-fails"
        ),
    ],
)
def test_a_fault_of_preparing_the_environment_fails_the_probe_before_any_run(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    human: HumanClone,
    agent_runtime: FakeAgentRuntime,
    container_settings: InstanceSettings,
    arrange: Callable[[Boundaries, HumanClone, Path], Dataset],
    detail: Callable[[Dataset], str],
) -> None:
    dataset = arrange(boundaries, human, tmp_path)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    item = agent_run_probe_item(dataset.boundaries, container_settings, ENVIRONMENT)

    assert item.name == "agent-run-probe"
    assert not item.passed
    assert item.detail == detail(dataset)
    assert agent_runtime.requests() == []
