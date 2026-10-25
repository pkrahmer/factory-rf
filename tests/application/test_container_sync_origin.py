"""The sync container gives the dataset's checkout `origin/<branch>` for every host branch."""

from pathlib import Path

import pytest

from container_support import (
    FIVE_MINUTES,
    Dataset,
    container_dataset,
    dataset_git,
    push_main,
    sync_makefile,
)
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import _SYNC_SCRIPT, ContainerEnvironment
from factory.domain.git import CommitId
from git_support import install_agents, run_git, write_files
from human_clone import HumanClone
from undo_support import BRANCH

AGENT = "tester"
GONE = "gone"


@pytest.fixture
def dataset(boundaries: Boundaries, tmp_path: Path) -> Dataset:
    """An empty dataset with an empty base, its fakes set in the boundaries."""
    return container_dataset(boundaries, tmp_path)


@pytest.fixture
def main_commit(boundaries: Boundaries, human: HumanClone, agent_home: Path) -> CommitId:
    """Push the sync Makefile to `main`, install an agent and return the host's `main` commit."""
    commit = push_main(boundaries, human, {"Makefile": sync_makefile()})
    install_agents(agent_home, [AGENT])
    return commit


@pytest.fixture
def branch_commit(boundaries: Boundaries, main_commit: CommitId) -> CommitId:
    """Give the host the work item's branch, made from `main` with one commit of its own."""
    git = boundaries.git
    git.checkout(BRANCH, start_point=main_commit)
    write_files(boundaries.checkout, {"src/branch.txt": "the branch's\n"})
    return git.commit("the branch's own commit")


def _environment(dataset: Dataset) -> ContainerEnvironment:
    return ContainerEnvironment(dataset.boundaries, dataset.snapshots, dataset.containers)


def _host_commit(boundaries: Boundaries, ref: str) -> str:
    return run_git(boundaries.checkout, "rev-parse", f"refs/heads/{ref}").strip()


@pytest.mark.parametrize(
    ("dataset_ref", "host_branch"),
    [
        pytest.param("origin/main", "main", id="origin-main"),
        pytest.param(f"origin/{BRANCH}", BRANCH, id="origin-branch"),
        pytest.param("main", "main", id="local-main"),
    ],
)
def test_the_dataset_checkout_holds_the_host_branches_as_origin_refs(
    dataset: Dataset,
    boundaries: Boundaries,
    main_commit: CommitId,
    branch_commit: CommitId,
    *,
    dataset_ref: str,
    host_branch: str,
) -> None:
    assert main_commit != branch_commit

    _environment(dataset).prepare(branch_commit, BRANCH, sync_time_limit=FIVE_MINUTES)

    expected = _host_commit(boundaries, host_branch)
    assert dataset_git(dataset, "rev-parse", "--verify", dataset_ref).strip() == expected


def test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs(
    dataset: Dataset, boundaries: Boundaries, main_commit: CommitId
) -> None:
    run_git(boundaries.checkout, "branch", GONE)
    environment = _environment(dataset)
    environment.prepare(main_commit, "main", sync_time_limit=FIVE_MINUTES)
    refs = (f"refs/heads/{GONE}", f"refs/remotes/origin/{GONE}")
    listed = dataset_git(dataset, "for-each-ref", "--format=%(refname)", *refs).split()
    assert sorted(listed) == sorted(refs)
    run_git(boundaries.checkout, "branch", "-D", GONE)

    environment.prepare(main_commit, "main", sync_time_limit=FIVE_MINUTES)

    assert dataset_git(dataset, "for-each-ref", "--format=%(refname)", *refs).split() == []


def test_the_merge_base_of_head_and_origin_main_is_the_host_main_commit(
    dataset: Dataset, main_commit: CommitId, branch_commit: CommitId
) -> None:
    _environment(dataset).prepare(branch_commit, BRANCH, sync_time_limit=FIVE_MINUTES)

    assert dataset_git(dataset, "merge-base", "HEAD", "origin/main").strip() == main_commit


def test_the_sync_script_fetches_both_refspecs_on_one_line_and_names_no_container_path() -> None:
    fetches = [line for line in _SYNC_SCRIPT.splitlines() if line.lstrip().startswith("git fetch")]

    assert len(fetches) == 1
    assert "'+refs/heads/*:refs/heads/*'" in fetches[0]
    assert "'+refs/heads/*:refs/remotes/origin/*'" in fetches[0]
    for path in ("/work", "/upstream"):
        assert path not in _SYNC_SCRIPT
