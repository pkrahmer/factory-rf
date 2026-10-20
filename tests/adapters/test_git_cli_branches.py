"""The git wrapper's branch operations, against a real bare remote and its clones."""

import shutil
import sys
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError
from factory.domain.kill_points import KillPoint, KillPoints
from git_support import (
    CHECKOUT,
    TEST_IDENTITY,
    clone,
    commit_all,
    remote_commit,
    run_git,
    write_files,
)
from human_clone import HumanClone

BRANCH = "work-item/F0001-S0001"
FEATURE = "factory/features/F0001-example/feature.md"


def _head(directory: Path, ref: str = "HEAD") -> str:
    return run_git(directory, "rev-parse", ref).strip()


def _refs(directory: Path, pattern: str = "refs/") -> list[str]:
    return run_git(
        directory, "for-each-ref", "--format=%(refname) %(objectname)", pattern
    ).splitlines()


def _status(directory: Path) -> str:
    return run_git(directory, "status", "--porcelain", "--untracked-files=all")


def _parents(directory: Path) -> list[str]:
    return run_git(directory, "log", "-1", "--format=%P").split()


def _identities(directory: Path) -> list[str]:
    return run_git(directory, "log", "-1", "--format=%an%n%ae%n%cn%n%ce").splitlines()


def _branch_with_commit(directory: Path, branch: str, files: dict[str, str]) -> str:
    run_git(directory, "checkout", "-q", "-B", branch, "origin/main")
    write_files(directory, files)
    return commit_all(directory, f"on {branch}")


def _pushed_branch(directory: Path, branch: str) -> str:
    commit = _branch_with_commit(directory, branch, {"pushed.txt": "pushed\n"})
    run_git(directory, "push", "-q", "origin", branch)
    run_git(directory, "checkout", "-q", "main")
    return commit


def _diverge(directory: Path, other: dict[str, str], main: dict[str, str]) -> tuple[str, str]:
    """Commit `other` on branch `other` and `main` on `main`; return both commits, main first."""
    other_commit = _branch_with_commit(directory, "other", other)
    run_git(directory, "checkout", "-q", "main")
    write_files(directory, main)
    return commit_all(directory, "on main"), other_commit


def test_delete_remote_branch_removes_it_from_the_remote_and_the_tracking_ref(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    _pushed_branch(directory, BRANCH)

    assert checkout.delete_remote_branch(BRANCH) == "pushed"

    assert remote_commit(remote, BRANCH) is None
    assert _refs(directory, f"refs/remotes/origin/{BRANCH}") == []


def test_delete_remote_branch_already_gone_is_pushed_and_drops_the_stale_tracking_ref(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    _pushed_branch(directory, BRANCH)
    other = clone(remote, tmp_path / "other")
    run_git(other, "push", "-q", "origin", "--delete", BRANCH)
    assert _refs(directory, f"refs/remotes/origin/{BRANCH}") != []
    remote_before = _refs(remote)

    assert checkout.delete_remote_branch(BRANCH) == "pushed"

    assert _refs(remote) == remote_before
    assert _refs(directory, f"refs/remotes/origin/{BRANCH}") == []


def test_delete_remote_branch_declined_by_a_remote_hook_is_rejected(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    commit = _pushed_branch(directory, BRANCH)
    hook = remote / "hooks" / "pre-receive"
    hook.write_text(f"#!{sys.executable} -B\nimport sys\nsys.exit(1)\n", encoding="utf-8")
    hook.chmod(0o755)

    assert checkout.delete_remote_branch(BRANCH) == "rejected"

    assert remote_commit(remote, BRANCH) == commit


def test_delete_remote_branch_on_a_removed_remote_is_unreachable(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    _pushed_branch(tmp_path / CHECKOUT, BRANCH)
    shutil.rmtree(remote)

    assert checkout.delete_remote_branch(BRANCH) == "unreachable"


def test_delete_remote_branch_of_an_invalid_ref_name_raises(remote: Path, checkout: GitCli) -> None:
    before = _refs(remote)

    with pytest.raises(ValueError):
        checkout.delete_remote_branch("a..b")

    assert _refs(remote) == before


def test_delete_remote_branch_reaches_no_kill_point(
    tmp_path: Path, remote: Path, checkout: GitCli, kill_points: KillPoints
) -> None:
    _pushed_branch(tmp_path / CHECKOUT, BRANCH)
    kill_points.arm(KillPoint.BEFORE_PUSH)
    kill_points.arm(KillPoint.AFTER_PUSH)

    assert checkout.delete_remote_branch(BRANCH) == "pushed"

    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 0
    assert kill_points.reached(KillPoint.AFTER_PUSH) == 0
    assert remote_commit(remote, BRANCH) is None


def test_delete_branch_removes_an_unmerged_local_branch(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    _branch_with_commit(directory, "other", {"other.txt": "other\n"})
    run_git(directory, "checkout", "-q", "main")

    checkout.delete_branch("other")

    assert _refs(directory, "refs/heads/other") == []


def test_delete_branch_of_the_checked_out_branch_raises_and_keeps_it(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, "other", {"other.txt": "other\n"})

    with pytest.raises(GitError):
        checkout.delete_branch("other")

    assert _head(directory, "refs/heads/other") == commit


def test_delete_branch_of_a_missing_branch_changes_nothing(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    before = _refs(directory)

    checkout.delete_branch("nope")

    assert _refs(directory) == before


@pytest.mark.parametrize("fast_forward_only", [False, True], ids=["merge", "fast-forward-only"])
def test_merge_of_a_contained_ref_is_up_to_date_and_keeps_head(
    tmp_path: Path, checkout: GitCli, fast_forward_only: bool
) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {"local.txt": "local\n"})
    before = commit_all(directory, "local")

    assert checkout.merge("origin/main", fast_forward_only=fast_forward_only) == "up_to_date"

    assert _head(directory) == before


@pytest.mark.parametrize("fast_forward_only", [False, True], ids=["merge", "fast-forward-only"])
def test_merge_of_a_descendant_fast_forwards_without_a_merge_commit(
    tmp_path: Path, checkout: GitCli, fast_forward_only: bool
) -> None:
    directory = tmp_path / CHECKOUT
    before = _head(directory)
    ahead = _branch_with_commit(directory, "ahead", {"ahead.txt": "ahead\n"})
    run_git(directory, "checkout", "-q", "main")

    assert checkout.merge("ahead", fast_forward_only=fast_forward_only) == "fast_forwarded"

    assert _head(directory) == ahead
    assert _head(directory, "refs/heads/main") == ahead
    assert _parents(directory) == [before]


def test_merge_of_a_diverged_branch_makes_a_merge_commit_with_both_parents(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    main, other = _diverge(directory, {"other.txt": "other\n"}, {"main.txt": "main\n"})

    assert checkout.merge("other") == "merged"

    assert _parents(directory) == [main, other]
    assert (directory / "other.txt").read_text(encoding="utf-8") == "other\n"
    assert (directory / "main.txt").read_text(encoding="utf-8") == "main\n"
    assert run_git(directory, "log", "-1", "--format=%s").strip() == "Merge branch 'other'"
    assert _status(directory) == ""


def test_merge_fast_forward_only_of_a_diverged_ref_changes_nothing(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    main, _ = _diverge(directory, {"other.txt": "other\n"}, {"main.txt": "main\n"})

    assert checkout.merge("other", fast_forward_only=True) == "not_fast_forward"

    assert _head(directory) == main
    assert not (directory / "other.txt").exists()
    assert _status(directory) == ""


def test_merge_with_a_conflict_is_aborted_and_leaves_everything_as_it_was(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    main, _ = _diverge(directory, {FEATURE: "# Other side\n"}, {FEATURE: "# Main side\n"})

    assert checkout.merge("other") == "conflict"

    assert _head(directory) == main
    assert _status(directory) == ""
    assert (directory / FEATURE).read_text(encoding="utf-8") == "# Main side\n"
    assert not (directory / ".git" / "MERGE_HEAD").exists()


def test_merge_of_an_unknown_ref_raises(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    before = _head(directory)

    with pytest.raises(GitError):
        checkout.merge("origin/nope")

    assert _head(directory) == before


def test_merge_that_would_overwrite_a_local_change_raises_and_keeps_the_change(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    main, _ = _diverge(directory, {FEATURE: "# Other side\n"}, {"main.txt": "main\n"})
    write_files(directory, {FEATURE: "# Local edit\n"})

    with pytest.raises(GitError):
        checkout.merge("other")

    assert _head(directory) == main
    assert (directory / FEATURE).read_text(encoding="utf-8") == "# Local edit\n"
    assert not (directory / ".git" / "MERGE_HEAD").exists()


def test_merge_commit_carries_the_identity_of_the_options(
    tmp_path: Path, checkout: GitCli, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / CHECKOUT
    _diverge(directory, {"other.txt": "other\n"}, {"main.txt": "main\n"})
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Intruder")

    assert checkout.merge("other") == "merged"

    assert _identities(directory) == [
        TEST_IDENTITY.name,
        TEST_IDENTITY.email,
        TEST_IDENTITY.name,
        TEST_IDENTITY.email,
    ]


@pytest.mark.usefixtures("checkout")
def test_merge_commit_without_options_carries_the_default_identity(tmp_path: Path) -> None:
    directory = tmp_path / CHECKOUT
    _diverge(directory, {"other.txt": "other\n"}, {"main.txt": "main\n"})

    assert GitCli(directory).merge("other") == "merged"

    assert _identities(directory) == [
        "factory",
        "factory@noreply.invalid",
        "factory",
        "factory@noreply.invalid",
    ]


def test_push_of_a_local_tag_without_a_local_branch_raises_and_pushes_nothing(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    run_git(tmp_path / CHECKOUT, "tag", "v1")

    with pytest.raises(GitError):
        checkout.push("v1")

    assert _refs(remote, "refs/heads/v1") == []
    assert _refs(remote, "refs/tags/v1") == []


@pytest.mark.usefixtures("human")
def test_delete_remote_branch_leaves_a_remote_tag_of_the_same_name(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    run_git(tmp_path / "human", "tag", "v1")
    run_git(tmp_path / "human", "push", "-q", "origin", "v1")
    tag = _refs(remote, "refs/tags/v1")
    assert tag != []

    assert checkout.delete_remote_branch("v1") == "pushed"

    assert _refs(remote, "refs/tags/v1") == tag


def test_push_of_a_new_branch_tracks_it_as_its_upstream(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, BRANCH, {"work.txt": "work\n"})

    assert checkout.push(BRANCH) == "pushed"

    assert _head(directory, f"origin/{BRANCH}") == commit
    upstream = run_git(directory, "rev-parse", "--abbrev-ref", f"{BRANCH}@{{upstream}}")
    assert upstream.strip() == f"origin/{BRANCH}"
    assert remote_commit(remote, BRANCH) == commit


def test_delete_remote_branch_removes_a_branch_the_human_pushed(
    tmp_path: Path, remote: Path, checkout: GitCli, human: HumanClone
) -> None:
    directory = tmp_path / CHECKOUT
    human.push_file("keep", "keep.txt", "keep\n")
    checkout.fetch()
    assert _refs(directory, "refs/remotes/origin/keep") != []

    assert checkout.delete_remote_branch("keep") == "pushed"

    assert remote_commit(remote, "keep") is None
    assert _refs(directory, "refs/remotes/origin/keep") == []
