"""The git wrapper's history and work-tree operations, against real local repositories."""

import os
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
from factory.application.git import Git
from factory.domain.errors import GitError
from factory.domain.git import ChangedPath, CommitInfo
from git_support import TEST_IDENTITY, commit_all, run_git, write_files


def _git(directory: Path) -> Git:
    return GitCli(directory)


def _repository(tmp_path: Path, branch: str = "main") -> Path:
    run_git(tmp_path, "init", "-q", f"--initial-branch={branch}", "work")
    return tmp_path / "work"


def _commit(work: Path, files: dict[str, str], message: str) -> str:
    write_files(work, files)
    return commit_all(work, message)


def _remove(work: Path, *names: str) -> None:
    for name in names:
        (work / name).unlink()


def _pairs(changes: list[ChangedPath]) -> list[tuple[str, str]]:
    return [(change.path, change.change) for change in changes]


def _ids(commits: list[CommitInfo]) -> list[str]:
    return [commit.commit for commit in commits]


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """Return a repository on `main` without commits."""
    return _repository(tmp_path)


def test_log_returns_the_commits_newest_first_as_git_reports_them(work: Path) -> None:
    for number in (1, 2, 3):
        _commit(work, {"file.txt": f"{number}\n"}, f"commit {number}")
    reported = run_git(work, "log", "--format=%H|%P|%s").splitlines()

    commits = _git(work).log("HEAD")

    assert len(commits) == 3
    assert [
        f"{commit.commit}|{' '.join(commit.parents)}|{commit.subject}" for commit in commits
    ] == reported
    assert [commit.subject for commit in commits] == ["commit 3", "commit 2", "commit 1"]
    assert commits[2].parents == []
    assert [commit.author for commit in commits] == ["Test Author"] * 3


def test_subject_is_only_the_first_line_of_the_message(work: Path) -> None:
    _commit(work, {"file.txt": "1\n"}, "The subject\n\nThe body,\nover two lines.")

    commits = _git(work).log("HEAD")

    assert [commit.subject for commit in commits] == ["The subject"]


def test_committed_at_is_the_committer_date_in_utc(work: Path) -> None:
    write_files(work, {"file.txt": "1\n"})
    run_git(work, "add", "-A")
    environment = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": TEST_IDENTITY.name,
        "GIT_AUTHOR_EMAIL": TEST_IDENTITY.email,
        "GIT_COMMITTER_NAME": TEST_IDENTITY.name,
        "GIT_COMMITTER_EMAIL": TEST_IDENTITY.email,
        "GIT_COMMITTER_DATE": "2026-03-04T10:00:00+02:00",
    }
    result = run_process(
        ProcessRequest(argv=["git", "commit", "-q", "-m", "dated"], cwd=work, env=environment)
    )
    assert result.exit_status == 0
    reported = int(run_git(work, "log", "-1", "--format=%ct").strip())

    commits = _git(work).log("HEAD")

    assert commits[0].committed_at.utcoffset() == timedelta(0)
    assert commits[0].committed_at.timestamp() == reported


def test_log_since_another_ref_returns_only_the_commits_not_reachable_from_it(
    work: Path,
) -> None:
    _commit(work, {"base.txt": "base\n"}, "base")
    run_git(work, "checkout", "-q", "-b", "feature")
    first = _commit(work, {"feature.txt": "1\n"}, "feature 1")
    second = _commit(work, {"feature.txt": "2\n"}, "feature 2")
    run_git(work, "checkout", "-q", "main")
    _commit(work, {"main.txt": "main\n"}, "main only")
    git = _git(work)

    assert _ids(git.log("feature", since="main")) == [second, first]
    assert git.log("main", since="main") == []


def test_log_for_a_path_returns_only_the_commits_that_changed_it(work: Path) -> None:
    first = _commit(work, {"docs/a.md": "1\n"}, "add a")
    _commit(work, {"other.txt": "1\n"}, "add other")
    third = _commit(work, {"docs/a.md": "2\n"}, "change a")
    fourth = _commit(work, {"docs/b.md": "1\n"}, "add b")
    git = _git(work)

    assert _ids(git.log("HEAD", path="docs/a.md")) == [third, first]
    assert _ids(git.log("HEAD", path="docs")) == [fourth, third, first]


def test_log_puts_a_merge_commit_with_two_parents_before_both(work: Path) -> None:
    _commit(work, {"base.txt": "base\n"}, "base")
    run_git(work, "checkout", "-q", "-b", "side")
    side = _commit(work, {"side.txt": "side\n"}, "on side")
    run_git(work, "checkout", "-q", "main")
    main = _commit(work, {"main.txt": "main\n"}, "on main")
    run_git(work, "merge", "-q", "--no-ff", "-m", "merge side", "side")
    merge = run_git(work, "rev-parse", "HEAD").strip()

    commits = _git(work).log("HEAD")
    ids = _ids(commits)

    assert commits[0].commit == merge
    assert commits[0].parents == [main, side]
    assert ids.index(merge) < ids.index(main)
    assert ids.index(merge) < ids.index(side)


@pytest.mark.parametrize(
    "operation",
    [
        lambda git: git.log("missing"),
        lambda git: git.log("HEAD", since="missing"),
        lambda git: git.changed_paths("missing"),
    ],
    ids=["log-ref", "log-since", "changed_paths-since"],
)
def test_a_ref_that_does_not_exist_is_a_git_error(
    work: Path, operation: Callable[[Git], object]
) -> None:
    _commit(work, {"file.txt": "1\n"}, "first")

    with pytest.raises(GitError):
        operation(_git(work))


def test_changed_paths_lists_committed_additions_changes_and_deletions(work: Path) -> None:
    since = _commit(work, {"old.txt": "old\n", "gone.txt": "gone\n"}, "base")
    _commit(work, {"new.txt": "new\n", "old.txt": "changed\n"}, "add and change")
    _remove(work, "gone.txt")
    commit_all(work, "delete")

    changes = _git(work).changed_paths(since)

    assert _pairs(changes) == [
        ("gone.txt", "deleted"),
        ("new.txt", "added"),
        ("old.txt", "modified"),
    ]


def test_changed_paths_lists_staged_unstaged_and_untracked_but_not_ignored(
    work: Path,
) -> None:
    since = _commit(work, {".gitignore": "ignored.txt\n", "tracked.txt": "1\n"}, "base")
    write_files(work, {"staged.txt": "staged\n"})
    run_git(work, "add", "staged.txt")
    write_files(work, {"tracked.txt": "2\n", "untracked.txt": "new\n", "ignored.txt": "x\n"})

    changes = _git(work).changed_paths(since)

    assert _pairs(changes) == [
        ("staged.txt", "added"),
        ("tracked.txt", "modified"),
        ("untracked.txt", "added"),
    ]


def _rename_with_git_mv(work: Path) -> None:
    run_git(work, "mv", "old.txt", "new.txt")


def _rename_with_git_mv_and_commit(work: Path) -> None:
    run_git(work, "mv", "old.txt", "new.txt")
    run_git(work, "commit", "-q", "-m", "rename")


def _delete_and_recreate(work: Path) -> None:
    text = (work / "old.txt").read_text(encoding="utf-8")
    _remove(work, "old.txt")
    write_files(work, {"new.txt": text})


RENAMES = pytest.mark.parametrize(
    "rename",
    [_rename_with_git_mv, _rename_with_git_mv_and_commit, _delete_and_recreate],
    ids=["git-mv", "git-mv-committed", "delete-and-recreate"],
)


@RENAMES
def test_changed_paths_shows_a_rename_as_a_deletion_and_an_addition(
    work: Path, rename: Callable[[Path], None]
) -> None:
    since = _commit(work, {"old.txt": "the same content\nover lines\n"}, "base")

    rename(work)

    assert _pairs(_git(work).changed_paths(since)) == [
        ("new.txt", "added"),
        ("old.txt", "deleted"),
    ]


def test_changed_paths_leaves_out_what_is_back_to_its_state_at_since(work: Path) -> None:
    since = _commit(work, {"old.txt": "old\n"}, "base")
    _commit(work, {"temporary.txt": "x\n"}, "add temporary")
    _remove(work, "temporary.txt")
    commit_all(work, "delete temporary")
    _commit(work, {"old.txt": "changed\n"}, "change old")
    write_files(work, {"old.txt": "old\n"})

    assert _git(work).changed_paths(since) == []


UNUSUAL_NAMES = ["é.txt", "a.txt", "a b/é.txt", "B.txt", "ab.txt"]


def test_paths_with_spaces_and_non_ascii_come_back_exactly_in_plain_order(work: Path) -> None:
    since = _commit(work, {"base.txt": "base\n"}, "base")
    write_files(work, {name: f"{name}\n" for name in UNUSUAL_NAMES})
    expected = [(name, "added") for name in sorted(UNUSUAL_NAMES)]
    git = _git(work)

    assert _pairs(git.changed_paths(since)) == expected
    assert _pairs(git.status().changes) == expected


def test_status_of_a_clean_checkout_names_the_branch_and_head(work: Path) -> None:
    head = _commit(work, {"file.txt": "1\n"}, "first")

    status = _git(work).status()

    assert status.branch == "main"
    assert status.head == head
    assert status.changes == []


def test_status_lists_untracked_edited_staged_and_deleted_files(work: Path) -> None:
    _commit(
        work,
        {"edited.txt": "1\n", "gone.txt": "gone\n", "removed.txt": "removed\n"},
        "base",
    )
    write_files(work, {"untracked.txt": "new\n", "edited.txt": "2\n", "staged.txt": "s\n"})
    run_git(work, "add", "staged.txt")
    _remove(work, "gone.txt")
    run_git(work, "rm", "-q", "removed.txt")

    status = _git(work).status()

    assert _pairs(status.changes) == [
        ("edited.txt", "modified"),
        ("gone.txt", "deleted"),
        ("removed.txt", "deleted"),
        ("staged.txt", "added"),
        ("untracked.txt", "added"),
    ]


def test_status_lists_a_file_changed_staged_and_changed_again_once_as_modified(
    work: Path,
) -> None:
    _commit(work, {"file.txt": "1\n"}, "base")
    write_files(work, {"file.txt": "2\n"})
    run_git(work, "add", "file.txt")
    write_files(work, {"file.txt": "3\n"})

    assert _pairs(_git(work).status().changes) == [("file.txt", "modified")]


def test_status_lists_a_new_file_staged_and_edited_again_once_as_added(work: Path) -> None:
    _commit(work, {"file.txt": "1\n"}, "base")
    write_files(work, {"new.txt": "1\n"})
    run_git(work, "add", "new.txt")
    write_files(work, {"new.txt": "2\n"})

    assert _pairs(_git(work).status().changes) == [("new.txt", "added")]


def test_status_shows_a_rename_as_a_deletion_and_an_addition(work: Path) -> None:
    _commit(work, {"old.txt": "the same content\nover lines\n"}, "base")
    run_git(work, "mv", "old.txt", "new.txt")

    assert _pairs(_git(work).status().changes) == [
        ("new.txt", "added"),
        ("old.txt", "deleted"),
    ]


def test_status_with_a_detached_head_has_no_branch_and_names_the_commit(work: Path) -> None:
    first = _commit(work, {"file.txt": "1\n"}, "first")
    _commit(work, {"file.txt": "2\n"}, "second")
    run_git(work, "checkout", "-q", "--detach", first)

    status = _git(work).status()

    assert status.branch is None
    assert status.head == first


def test_status_without_commits_has_no_head_and_names_the_unborn_branch(
    tmp_path: Path,
) -> None:
    work = _repository(tmp_path, branch="trunk")
    write_files(work, {"a.txt": "1\n"})

    status = _git(work).status()

    assert status.head is None
    assert status.branch == "trunk"
    assert _pairs(status.changes) == [("a.txt", "added")]


def test_status_does_not_list_an_ignored_path(work: Path) -> None:
    _commit(work, {".gitignore": "ignored.txt\n", "file.txt": "1\n"}, "base")
    write_files(work, {"ignored.txt": "x\n"})

    assert _git(work).status().changes == []
