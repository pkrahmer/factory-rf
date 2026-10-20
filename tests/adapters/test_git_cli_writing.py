"""The git wrapper's writing operations, against a real bare remote and its clones."""

import shutil
import sys
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.errors import GitError, NothingToCommit
from factory.domain.git import GitIdentity, GitOptions
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from git_support import (
    CHECKOUT,
    REMOTE_FILES,
    clone,
    commit_all,
    remote_commit,
    run_git,
    write_files,
)

BRANCH = "work-item/F0001-S0001"
STORY = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
FEATURE = "factory/features/F0001-example/feature.md"
CHOSEN = GitIdentity(name="Chosen Name", email="chosen@example.invalid")


def _current_branch(directory: Path) -> str:
    return run_git(directory, "rev-parse", "--abbrev-ref", "HEAD").strip()


def _head(directory: Path, ref: str = "HEAD") -> str:
    return run_git(directory, "rev-parse", ref).strip()


def _identities(directory: Path) -> list[str]:
    return run_git(directory, "log", "-1", "--format=%an%n%ae%n%cn%n%ce").splitlines()


def _branch_with_commit(directory: Path, branch: str, files: dict[str, str]) -> str:
    run_git(directory, "checkout", "-q", "-B", branch, "origin/main")
    write_files(directory, files)
    return commit_all(directory, f"on {branch}")


def _ignore_logs(directory: Path) -> None:
    write_files(directory, {".gitignore": "*.log\n"})
    commit_all(directory, "ignore logs")


def test_clone_creates_a_missing_directory_and_its_missing_parent(
    tmp_path: Path, remote: Path
) -> None:
    directory = tmp_path / "parent" / "clone"

    GitCli(directory).clone(str(remote))

    for name, text in REMOTE_FILES.items():
        assert (directory / name).read_text(encoding="utf-8") == text
    assert _current_branch(directory) == "main"
    assert run_git(directory, "remote", "get-url", "origin").strip() == str(remote)


def test_clone_works_into_an_empty_directory_and_refuses_one_with_a_file(
    tmp_path: Path, remote: Path
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("keep\n", encoding="utf-8")

    GitCli(empty).clone(str(remote))
    with pytest.raises(GitError):
        GitCli(occupied).clone(str(remote))

    assert _current_branch(empty) == "main"
    assert [path.name for path in occupied.iterdir()] == ["keep.txt"]
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "keep\n"


def test_clone_of_a_missing_url_raises(tmp_path: Path) -> None:
    with pytest.raises(GitError):
        GitCli(tmp_path / "clone").clone(str(tmp_path / "missing.git"))


def test_checkout_switches_to_an_existing_local_branch(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, "other", {"other.txt": "other\n"})
    run_git(directory, "checkout", "-q", "main")

    checkout.checkout("other")

    assert _current_branch(directory) == "other"
    assert _head(directory) == commit
    assert (directory / "other.txt").read_text(encoding="utf-8") == "other\n"


def test_checkout_with_a_start_point_creates_and_then_resets_the_branch(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    main = _head(directory, "origin/main")

    checkout.checkout(BRANCH, start_point="origin/main")
    assert _current_branch(directory) == BRANCH
    assert _head(directory) == main

    write_files(directory, {"more.txt": "more\n"})
    commit_all(directory, "more")
    checkout.checkout(BRANCH, start_point="origin/main")

    assert _current_branch(directory) == BRANCH
    assert _head(directory, BRANCH) == main


def test_checkout_of_a_branch_only_on_the_remote_creates_it_at_the_remote_commit(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    other = clone(remote, tmp_path / "other")
    commit = _branch_with_commit(other, "remote-only", {"remote.txt": "remote\n"})
    run_git(other, "push", "-q", "origin", "remote-only")
    run_git(directory, "fetch", "-q", "origin")

    checkout.checkout("remote-only")

    assert _current_branch(directory) == "remote-only"
    assert _head(directory, "refs/heads/remote-only") == commit


@pytest.mark.parametrize(
    ("branch", "start_point"),
    [("nope", None), ("x", "origin/nope")],
    ids=["unknown-branch", "unknown-start-point"],
)
def test_checkout_of_an_unknown_branch_or_start_point_raises_and_stays(
    tmp_path: Path, checkout: GitCli, branch: str, start_point: str | None
) -> None:
    directory = tmp_path / CHECKOUT

    with pytest.raises(GitError):
        checkout.checkout(branch, start_point=start_point)

    assert _current_branch(directory) == "main"


def test_checkout_blocked_by_an_uncommitted_edit_raises_and_keeps_the_edit(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    _branch_with_commit(directory, "other", {FEATURE: "# Other feature\n"})
    run_git(directory, "checkout", "-q", "main")
    write_files(directory, {FEATURE: "# Edited feature\n"})

    with pytest.raises(GitError):
        checkout.checkout("other")

    assert _current_branch(directory) == "main"
    assert (directory / FEATURE).read_text(encoding="utf-8") == "# Edited feature\n"


def test_commit_records_new_changed_and_deleted_files_but_not_ignored_ones(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    _ignore_logs(directory)
    write_files(directory, {"new.txt": "new\n", FEATURE: "# Changed\n", "debug.log": "noise\n"})
    (directory / STORY).unlink()

    commit = checkout.commit("three changes")

    assert commit == _head(directory)
    changes = run_git(directory, "diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD")
    assert sorted(changes.splitlines()) == sorted(["A\tnew.txt", f"M\t{FEATURE}", f"D\t{STORY}"])


def test_commit_stores_the_message_as_given(tmp_path: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {"new.txt": "new\n"})

    checkout.commit("Subject line\n\nBody line")

    message = run_git(directory, "log", "-1", "--format=%B")
    assert message.rstrip("\n") == "Subject line\n\nBody line"


GLOBAL_CONFIG = (
    "[user]\n\tname = Intruder\n\temail = intruder@example.invalid\n[commit]\n\tgpgsign = true\n"
)


@pytest.mark.parametrize(
    ("process_environment", "options_environment", "global_config"),
    [
        ({"GIT_AUTHOR_NAME": "Intruder"}, {}, False),
        (
            {},
            {"GIT_AUTHOR_NAME": "Intruder", "GIT_COMMITTER_EMAIL": "intruder@example.invalid"},
            False,
        ),
        ({}, {}, True),
    ],
    ids=["process-environment", "options-environment", "global-configuration"],
)
@pytest.mark.usefixtures("checkout")
def test_commit_carries_the_identity_of_the_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    process_environment: dict[str, str],
    options_environment: dict[str, str],
    global_config: bool,
) -> None:
    directory = tmp_path / CHECKOUT
    for key, value in process_environment.items():
        monkeypatch.setenv(key, value)
    if global_config:
        config = tmp_path / "global.gitconfig"
        config.write_text(GLOBAL_CONFIG, encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    cli = GitCli(directory, GitOptions(identity=CHOSEN, environment=options_environment))
    write_files(directory, {"new.txt": "new\n"})

    cli.commit("chosen")

    assert _identities(directory) == [CHOSEN.name, CHOSEN.email, CHOSEN.name, CHOSEN.email]


@pytest.mark.usefixtures("checkout")
def test_commit_without_options_carries_the_default_identity(tmp_path: Path) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, {"new.txt": "new\n"})

    GitCli(directory).commit("default")

    assert _identities(directory) == [
        "factory",
        "factory@noreply.invalid",
        "factory",
        "factory@noreply.invalid",
    ]


@pytest.mark.parametrize("only_ignored", [False, True], ids=["clean", "only-ignored"])
def test_commit_with_nothing_to_commit_raises_and_keeps_head(
    tmp_path: Path, checkout: GitCli, only_ignored: bool
) -> None:
    directory = tmp_path / CHECKOUT
    if only_ignored:
        _ignore_logs(directory)
        write_files(directory, {"debug.log": "noise\n"})
    before = _head(directory)

    with pytest.raises(NothingToCommit):
        checkout.commit("nothing")

    assert _head(directory) == before


def test_push_of_a_new_branch_is_pushed(tmp_path: Path, remote: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, BRANCH, {"new.txt": "new\n"})

    assert checkout.push(BRANCH) == "pushed"

    assert remote_commit(remote, BRANCH) == commit
    assert _head(directory, f"origin/{BRANCH}") == commit


def test_push_behind_another_clone_is_rejected(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    other = clone(remote, tmp_path / "other")
    first = _branch_with_commit(other, BRANCH, {"first.txt": "first\n"})
    run_git(other, "push", "-q", "origin", BRANCH)
    _branch_with_commit(directory, BRANCH, {"second.txt": "second\n"})

    assert checkout.push(BRANCH) == "rejected"

    assert remote_commit(remote, BRANCH) == first


def test_push_declined_by_a_remote_hook_is_rejected(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    hook = remote / "hooks" / "pre-receive"
    hook.write_text(f"#!{sys.executable} -B\nimport sys\nsys.exit(1)\n", encoding="utf-8")
    hook.chmod(0o755)
    _branch_with_commit(directory, BRANCH, {"new.txt": "new\n"})

    assert checkout.push(BRANCH) == "rejected"

    assert remote_commit(remote, BRANCH) is None


def test_push_to_a_removed_remote_is_unreachable(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    _branch_with_commit(directory, BRANCH, {"new.txt": "new\n"})
    shutil.rmtree(remote)

    assert checkout.push(BRANCH) == "unreachable"


def test_push_of_an_unknown_local_branch_raises(checkout: GitCli) -> None:
    with pytest.raises(GitError):
        checkout.push("nope")


def test_kill_before_push_leaves_the_remote_untouched(
    tmp_path: Path, remote: Path, checkout: GitCli, kill_points: KillPoints
) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, BRANCH, {"new.txt": "new\n"})
    kill_points.arm(KillPoint.BEFORE_PUSH)

    with pytest.raises(InjectedKill) as raised:
        checkout.push(BRANCH)

    assert raised.value.point is KillPoint.BEFORE_PUSH
    assert _head(directory, f"refs/heads/{BRANCH}") == commit
    assert remote_commit(remote, BRANCH) is None


def test_kill_after_push_comes_after_the_remote_has_the_commit(
    tmp_path: Path, remote: Path, checkout: GitCli, kill_points: KillPoints
) -> None:
    directory = tmp_path / CHECKOUT
    commit = _branch_with_commit(directory, BRANCH, {"new.txt": "new\n"})
    kill_points.arm(KillPoint.AFTER_PUSH)

    with pytest.raises(InjectedKill) as raised:
        checkout.push(BRANCH)

    assert raised.value.point is KillPoint.AFTER_PUSH
    assert remote_commit(remote, BRANCH) == commit


def test_push_reaches_before_push_every_time_and_after_push_only_when_pushed(
    tmp_path: Path, remote: Path, checkout: GitCli, kill_points: KillPoints
) -> None:
    directory = tmp_path / CHECKOUT
    other = clone(remote, tmp_path / "other")
    _branch_with_commit(other, BRANCH, {"first.txt": "first\n"})
    run_git(other, "push", "-q", "origin", BRANCH)
    _branch_with_commit(directory, BRANCH, {"second.txt": "second\n"})

    assert checkout.push(BRANCH) == "rejected"
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 1
    assert kill_points.reached(KillPoint.AFTER_PUSH) == 0

    run_git(directory, "fetch", "-q", "origin")
    run_git(directory, "reset", "-q", "--hard", f"origin/{BRANCH}")
    write_files(directory, {"second.txt": "second\n"})
    commit_all(directory, "second")
    assert checkout.push(BRANCH) == "pushed"
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 2
    assert kill_points.reached(KillPoint.AFTER_PUSH) == 1

    plain = _branch_with_commit(directory, "plain", {"plain.txt": "plain\n"})
    assert GitCli(directory).push("plain") == "pushed"
    assert remote_commit(remote, "plain") == plain
