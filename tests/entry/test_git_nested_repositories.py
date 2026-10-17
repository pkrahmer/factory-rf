"""The factory's git never starts the `core.fsmonitor` of a repository nested in the checkout."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.entry.wiring import git_environment
from git_support import CHECKOUT, clone, commit_all, run_git, write_fsmonitor

FACTORY = GitOptions(environment=git_environment())
PLAIN = GitOptions()

Operation = Callable[[GitCli], object]


def _status(git: GitCli) -> object:
    return git.status()


def _changed_paths(git: GitCli) -> object:
    return git.changed_paths("HEAD")


@pytest.mark.parametrize(
    "operation",
    [pytest.param(_status, id="status"), pytest.param(_changed_paths, id="changed-paths")],
)
@pytest.mark.parametrize(
    ("options", "runs"),
    [pytest.param(FACTORY, False, id="factory"), pytest.param(PLAIN, True, id="plain")],
)
def test_a_nested_repositorys_fsmonitor_does_not_run_under_the_factorys_git(
    tmp_path: Path, remote: Path, operation: Operation, options: GitOptions, runs: bool
) -> None:
    checkout = clone(remote, tmp_path / CHECKOUT)
    marker = tmp_path / "fsmonitor-ran"
    monitor = write_fsmonitor(tmp_path, marker)
    nested = checkout / "notes" / "sub"
    nested.mkdir(parents=True)
    run_git(nested, "init", "-q")
    (nested / "a.txt").write_text("a\n", encoding="utf-8")
    commit_all(nested, "nested")
    run_git(nested, "config", "core.fsmonitor", str(monitor))
    GitCli(checkout, PLAIN).commit("Add the nested repository")
    marker.write_text("", encoding="utf-8")

    operation(GitCli(checkout, options))

    assert (marker.read_text(encoding="utf-8") != "") == runs
