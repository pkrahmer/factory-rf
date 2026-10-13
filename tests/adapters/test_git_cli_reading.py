"""The git wrapper's reading operations, against a real bare remote and its clones."""

import shutil
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.git import Git
from factory.domain.errors import FetchFailed, GitError
from factory.domain.git import GitOptions, RemoteBranch
from git_support import CHECKOUT, clone, commit_all, run_git, write_executable, write_files


def _other_clone(tmp_path: Path, remote: Path) -> Path:
    return clone(remote, tmp_path / "other")


def _push_branch(work: Path, branch: str, files: dict[str, str], start: str = "origin/main") -> str:
    run_git(work, "checkout", "-q", "-b", branch, start)
    write_files(work, files)
    commit = commit_all(work, f"on {branch}")
    run_git(work, "push", "-q", "origin", branch)
    return commit


def _push_main(work: Path, files: dict[str, str]) -> str:
    run_git(work, "checkout", "-q", "main")
    write_files(work, files)
    commit = commit_all(work, "on main")
    run_git(work, "push", "-q", "origin", "main")
    return commit


def _gitconfig_rewriting(tmp_path: Path, remote: Path, name: str) -> Path:
    path = tmp_path / name
    missing = tmp_path / "missing.git"
    path.write_text(f'[url "{missing}"]\n\tinsteadOf = {remote}\n', encoding="utf-8")
    return path


def _rewrite_to_remote(remote: Path, missing: str) -> dict[str, str]:
    return {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"url.{remote}.insteadOf",
        "GIT_CONFIG_VALUE_0": missing,
    }


def _remote_branch(checkout: GitCli, name: str) -> RemoteBranch | None:
    return next((branch for branch in checkout.remote_branches() if branch.name == name), None)


NUMBERED_LINES = (
    "import sys\n"
    "for n in range(1, {count} + 1):\n"
    "    print(f'line {{n}}', file=sys.stderr)\n"
    "sys.exit(1)"
)


@pytest.mark.parametrize(
    ("count", "first_kept"),
    [(40, 11), (3, 1)],
    ids=["forty-lines", "three-lines"],
)
@pytest.mark.parametrize(
    ("operation", "error"),
    [
        (lambda cli: cli.fetch(), FetchFailed),
        (lambda cli: cli.remote_branches(), GitError),
    ],
    ids=["fetch", "remote_branches"],
)
def test_failure_keeps_the_last_thirty_lines_of_output(
    tmp_path: Path,
    count: int,
    first_kept: int,
    operation: Callable[[GitCli], object],
    error: type[GitError],
) -> None:
    executable = write_executable(tmp_path, NUMBERED_LINES.format(count=count))
    cli = GitCli(tmp_path, GitOptions(executable=str(executable)))

    with pytest.raises(error) as raised:
        operation(cli)

    expected = [f"line {n}" for n in range(first_kept, count + 1)]
    assert raised.value.output_tail.splitlines() == expected


def test_executable_that_cannot_start_raises_without_exit_status(tmp_path: Path) -> None:
    cli = GitCli(tmp_path, GitOptions(executable="/no/such/git"))

    with pytest.raises(GitError) as raised:
        cli.resolve("HEAD")
    with pytest.raises(FetchFailed):
        cli.fetch()

    assert raised.value.exit_status is None
    assert raised.value.output_tail != ""


def test_command_that_reaches_its_time_limit_raises_without_exit_status(tmp_path: Path) -> None:
    executable = write_executable(tmp_path, "import time\ntime.sleep(60)")
    cli = GitCli(tmp_path, GitOptions(executable=str(executable), time_limit=timedelta(seconds=1)))

    start = time.monotonic()
    with pytest.raises(GitError) as raised:
        cli.resolve("HEAD")
    elapsed = time.monotonic() - start
    with pytest.raises(FetchFailed):
        cli.fetch()

    assert elapsed < 6
    assert raised.value.exit_status is None
    assert "time limit reached" in raised.value.output_tail


def test_fetch_brings_in_a_branch_pushed_by_another_clone(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    other = _other_clone(tmp_path, remote)
    pushed = _push_branch(other, "work-item/F0001-S0002", {"new.txt": "new\n"})

    before = _remote_branch(checkout, "work-item/F0001-S0002")
    checkout.fetch()

    assert before is None
    assert _remote_branch(checkout, "work-item/F0001-S0002") == RemoteBranch(
        name="work-item/F0001-S0002", commit=pushed
    )


def test_fetch_prunes_a_branch_the_remote_deleted(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    other = _other_clone(tmp_path, remote)
    _push_branch(other, "short-lived", {"new.txt": "new\n"})
    checkout.fetch()
    present = _remote_branch(checkout, "short-lived")

    run_git(remote, "branch", "-D", "short-lived")
    checkout.fetch()

    assert present is not None
    assert _remote_branch(checkout, "short-lived") is None


def test_fetch_outside_a_repository_raises_fetch_failed(tmp_path: Path) -> None:
    directory = tmp_path / "plain"
    directory.mkdir()

    with pytest.raises(FetchFailed) as raised:
        GitCli(directory).fetch()

    assert raised.value.command == "git fetch --prune origin"
    assert raised.value.exit_status == 128
    assert "not a git repository" in raised.value.output_tail


def test_fetch_from_a_removed_remote_raises_fetch_failed(remote: Path, checkout: GitCli) -> None:
    shutil.rmtree(remote)

    with pytest.raises(FetchFailed) as raised:
        checkout.fetch()

    assert raised.value.command == "git fetch --prune origin"
    assert raised.value.exit_status == 128
    assert raised.value.output_tail != ""


def test_global_configuration_is_ignored(
    tmp_path: Path, remote: Path, checkout: GitCli, monkeypatch: pytest.MonkeyPatch
) -> None:
    rewriting = _gitconfig_rewriting(tmp_path, remote, "global.gitconfig")
    directory = tmp_path / CHECKOUT

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(rewriting))
    checkout.fetch()
    monkeypatch.delenv("GIT_CONFIG_GLOBAL")
    GitCli(directory, GitOptions(environment={"GIT_CONFIG_GLOBAL": str(rewriting)})).fetch()


def test_system_configuration_is_ignored(
    tmp_path: Path, remote: Path, checkout: GitCli, monkeypatch: pytest.MonkeyPatch
) -> None:
    rewriting = _gitconfig_rewriting(tmp_path, remote, "system.gitconfig")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(rewriting))
    monkeypatch.delenv("GIT_CONFIG_NOSYSTEM", raising=False)

    checkout.fetch()


def test_options_environment_reaches_git(tmp_path: Path, remote: Path, checkout: GitCli) -> None:
    directory = tmp_path / CHECKOUT
    missing = str(tmp_path / "missing.git")
    run_git(directory, "remote", "set-url", "origin", missing)

    with pytest.raises(FetchFailed):
        checkout.fetch()
    GitCli(directory, GitOptions(environment=_rewrite_to_remote(remote, missing))).fetch()


@pytest.mark.usefixtures("checkout")
def test_process_environment_reaches_git(
    tmp_path: Path, remote: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / CHECKOUT
    missing = str(tmp_path / "missing.git")
    run_git(directory, "remote", "set-url", "origin", missing)
    for key, value in _rewrite_to_remote(remote, missing).items():
        monkeypatch.setenv(key, value)

    GitCli(directory, GitOptions()).fetch()


def test_remote_branches_lists_the_remote_tracking_branches_sorted(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    other = _other_clone(tmp_path, remote)
    main = run_git(other, "rev-parse", "origin/main").strip()
    item = _push_branch(other, "work-item/F0001-S0001", {"a.txt": "a\n"})
    lower = _push_branch(other, "feature-b", {"b.txt": "b\n"})
    upper = _push_branch(other, "Zeta", {"z.txt": "z\n"})
    run_git(tmp_path / CHECKOUT, "branch", "local-only")

    checkout.fetch()

    assert checkout.remote_branches() == [
        RemoteBranch(name="Zeta", commit=upper),
        RemoteBranch(name="feature-b", commit=lower),
        RemoteBranch(name="main", commit=main),
        RemoteBranch(name="work-item/F0001-S0001", commit=item),
    ]


def test_resolve_returns_the_full_commit_id(tmp_path: Path, checkout: GitCli) -> None:
    head = run_git(tmp_path / CHECKOUT, "rev-parse", "HEAD").strip()

    assert len(head) == 40
    assert checkout.resolve("HEAD") == head
    assert checkout.resolve("origin/main") == head
    assert checkout.resolve(head) == head


def test_resolve_returns_none_for_a_missing_ref(tmp_path: Path, checkout: GitCli) -> None:
    run_git(tmp_path, "init", "-q", "--initial-branch=main", "empty")

    assert checkout.resolve("origin/nope") is None
    assert GitCli(tmp_path / "empty").resolve("HEAD") is None


def test_show_file_returns_the_text_as_committed(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    other = _other_clone(tmp_path, remote)
    older = _push_main(other, {"notes/grüße.md": "Grüße, élan\nsecond line\n"})
    _push_main(other, {"notes/grüße.md": "changed\n"})

    checkout.fetch()

    assert checkout.show_file("origin/main", "notes/grüße.md") == "changed\n"
    assert checkout.show_file(older, "notes/grüße.md") == "Grüße, élan\nsecond line\n"
    assert checkout.show_file("origin/main", "factory/features/F0001-example/feature.md") == (
        "# Example feature\n"
    )


def test_show_file_returns_none_for_no_file_and_raises_for_a_missing_ref(
    checkout: GitCli,
) -> None:
    assert checkout.show_file("origin/main", "factory/missing.md") is None
    assert checkout.show_file("origin/main", "factory/features") is None
    with pytest.raises(GitError):
        checkout.show_file("origin/nope", "factory/pipeline.yml")


def test_list_files_returns_all_paths_under_a_directory_sorted(
    tmp_path: Path, remote: Path, checkout: GitCli
) -> None:
    other = _other_clone(tmp_path, remote)
    _push_main(other, {"factory/features/F0001-example/read me é.txt": "hello\n"})

    checkout.fetch()

    assert checkout.list_files("origin/main", "factory/features") == [
        "factory/features/F0001-example/backlog/F0001-S0001-first.md",
        "factory/features/F0001-example/feature.md",
        "factory/features/F0001-example/read me é.txt",
    ]


def test_list_files_is_empty_for_a_missing_directory_and_raises_for_a_missing_ref(
    checkout: GitCli,
) -> None:
    assert checkout.list_files("origin/main", "factory/nope") == []
    with pytest.raises(GitError):
        checkout.list_files("origin/nope", "factory")


def test_is_ancestor_follows_history(tmp_path: Path, remote: Path, checkout: GitCli) -> None:
    other = _other_clone(tmp_path, remote)
    earlier = run_git(other, "rev-parse", "origin/main").strip()
    later = _push_main(other, {"later.txt": "later\n"})
    left = _push_branch(other, "left", {"left.txt": "left\n"}, start=earlier)
    right = _push_branch(other, "right", {"right.txt": "right\n"}, start=earlier)

    checkout.fetch()

    assert checkout.is_ancestor(earlier, later) is True
    assert checkout.is_ancestor(earlier, earlier) is True
    assert checkout.is_ancestor(later, earlier) is False
    assert checkout.is_ancestor(left, right) is False


@pytest.mark.parametrize(
    ("ancestor", "descendant"),
    [("origin/nope", "origin/main"), ("origin/main", "origin/nope")],
    ids=["unknown-ancestor", "unknown-descendant"],
)
def test_is_ancestor_raises_for_an_unknown_ref(
    checkout: GitCli, ancestor: str, descendant: str
) -> None:
    with pytest.raises(GitError):
        checkout.is_ancestor(ancestor, descendant)


def test_git_cli_inherits_the_git_interface(checkout: GitCli) -> None:
    assert issubclass(GitCli, Git)
    assert isinstance(checkout, Git)


@pytest.mark.parametrize(
    "make",
    [GitCli, lambda directory: GitCli(directory, GitOptions())],
    ids=["no-options", "default-options"],
)
@pytest.mark.usefixtures("checkout")
def test_git_cli_works_with_default_options(tmp_path: Path, make: Callable[[Path], GitCli]) -> None:
    make(tmp_path / CHECKOUT).fetch()
