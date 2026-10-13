"""The human's clone: starting a story, pushing a file and merging by each method."""

from pathlib import Path
from typing import Literal

import pytest

from git_support import remote_commit, run_git
from human_clone import HumanClone

BRANCH = "feature-x"
FEATURE_FOLDER = "factory/features/F0001-example"


def _parents(remote: Path, commit: str) -> list[str]:
    return run_git(remote, "rev-list", "--parents", "-n", "1", commit).split()[1:]


@pytest.mark.parametrize(
    ("method", "expected"),
    [("merge", (1, 1, True)), ("squash", (0, 1, False)), ("rebase", (0, 2, False))],
    ids=["merge", "squash", "rebase"],
)
def test_merge_brings_the_branch_into_main_by_the_method(
    remote: Path,
    human: HumanClone,
    method: Literal["merge", "squash", "rebase"],
    expected: tuple[int, int, bool],
) -> None:
    merges, first_parent_commits, tip_on_main = expected
    human.push_file(BRANCH, "one.txt", "one\n")
    human.push_file(BRANCH, "two.txt", "two\n")
    human.push_file("main", "main.txt", "main\n")
    before = remote_commit(remote, "main")
    tip = remote_commit(remote, BRANCH)
    assert before is not None
    assert tip is not None

    human.merge(BRANCH, method)

    after = remote_commit(remote, "main")
    assert after is not None
    span = f"{before}..{after}"
    run_git(remote, "merge-base", "--is-ancestor", before, after)
    assert int(run_git(remote, "rev-list", "--count", "--merges", span)) == merges
    assert int(run_git(remote, "rev-list", "--count", "--first-parent", span)) == (
        first_parent_commits
    )
    assert len(_parents(remote, after)) == merges + 1
    if not merges:
        oldest = run_git(remote, "rev-list", "--reverse", span).split()[0]
        assert _parents(remote, oldest) == [before]
    is_ancestor = run_git(remote, "branch", "--contains", tip, "--list", "main").strip() != ""
    assert is_ancestor is tip_on_main
    for name, text in (("one.txt", "one\n"), ("two.txt", "two\n"), ("main.txt", "main\n")):
        assert run_git(remote, "show", f"main:{name}") == text


def test_start_moves_the_story_and_push_file_writes_the_branch(
    remote: Path, human: HumanClone
) -> None:
    human.start(f"{FEATURE_FOLDER}/backlog/F0001-S0001-first.md")
    human.push_file(BRANCH, "notes/hello.txt", "hello\n")

    files = run_git(remote, "ls-tree", "-r", "--name-only", "main", "--", FEATURE_FOLDER)
    assert f"{FEATURE_FOLDER}/in-progress/F0001-S0001-first.md" in files.splitlines()
    assert f"{FEATURE_FOLDER}/backlog/F0001-S0001-first.md" not in files.splitlines()
    assert run_git(remote, "show", f"{BRANCH}:notes/hello.txt") == "hello\n"
