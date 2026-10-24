"""Shared helpers of the container environment tests: a dataset beside the host and its fakes."""

from dataclasses import dataclass, replace
from pathlib import Path

from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.application.boundaries import Boundaries
from factory.domain.git import CommitId
from git_support import run_git
from human_clone import HumanClone

SYNC_MARKER = ".synced"
SYNC_RECIPE = f"@echo synced > {SYNC_MARKER}"
TIMING_PREFIX = "stage environment:"


def sync_makefile(recipe: str = SYNC_RECIPE) -> str:
    """A Makefile whose `sync` runs `recipe`; by default it writes the marker `.synced`."""
    return f".PHONY: sync\n\nsync:\n\t{recipe}\n"


@dataclass(frozen=True)
class Dataset:
    """The boundaries with the two fakes set, the fakes, and the dataset's folder and base."""

    boundaries: Boundaries
    snapshots: FakeSnapshots
    containers: FakeContainerRuns
    workspace: Path
    base: Path


def container_dataset(boundaries: Boundaries, tmp_path: Path, *, with_base: bool = True) -> Dataset:
    """An empty dataset at `<tmp_path>/workspace`; its empty base beside it when `with_base`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = tmp_path / "base"
    if with_base:
        base.mkdir()
    snapshots = FakeSnapshots(workspace, base)
    containers = FakeContainerRuns(workspace)
    return Dataset(
        boundaries=replace(boundaries, snapshots=snapshots, containers=containers),
        snapshots=snapshots,
        containers=containers,
        workspace=workspace,
        base=base,
    )


def push_main(boundaries: Boundaries, human: HumanClone, files: dict[str, str]) -> CommitId:
    """Push `files` to `main`, bring the host's `main` to it and return its commit."""
    human.push_files("main", files)
    git = boundaries.git
    git.fetch()
    git.checkout("main", start_point="origin/main")
    commit = git.resolve("main")
    assert commit is not None
    return commit


def dataset_git(dataset: Dataset, *args: str) -> str:
    """Run git in the dataset's checkout and return its output."""
    return run_git(dataset.workspace / "checkout", *args)


def local_branches(dataset: Dataset) -> list[str]:
    """The local branches of the dataset's repository, by name."""
    return dataset_git(dataset, "branch", "--format=%(refname:short)").split()


def timing_lines(boundaries: Boundaries) -> list[str]:
    """The lines of the factory log that carry the stage environment's timing."""
    log = boundaries.settings.state_directory / "factory.log"
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if TIMING_PREFIX in line]
