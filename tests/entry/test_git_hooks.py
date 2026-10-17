"""The factory's git runs no hooks of the checkout, while a bare remote's hooks still run."""

import shlex
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.entry.wiring import git_environment
from git_support import CHECKOUT, clone, remote_commit, run_git

BRANCH = "work"
FACTORY = GitOptions(environment=git_environment())
PLAIN = GitOptions()

# Each operation installs its hook, runs the git operation and checks that it succeeded.
Operation = Callable[[GitCli, Path, Path, Path], None]


def _write_hook(path: Path, marker: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n", encoding="utf-8")
    path.chmod(0o755)


def _commit_with_pre_commit(git: GitCli, checkout: Path, marker: Path, _: Path) -> None:
    _write_hook(checkout / ".git" / "hooks" / "pre-commit", marker)
    (checkout / "note.md").write_text("A note.\n", encoding="utf-8")

    commit = git.commit("Add a note")

    assert run_git(checkout, "rev-parse", "HEAD").strip() == commit
    assert run_git(checkout, "show", "--format=%s", "--no-patch", "HEAD").strip() == "Add a note"


def _checkout_with_post_checkout(git: GitCli, checkout: Path, marker: Path, _: Path) -> None:
    _write_hook(checkout / ".git" / "hooks" / "post-checkout", marker)

    git.checkout(BRANCH, start_point="origin/main")

    assert run_git(checkout, "rev-parse", "--abbrev-ref", "HEAD").strip() == BRANCH


def _push_with_pre_push(git: GitCli, checkout: Path, marker: Path, remote: Path) -> None:
    _write_hook(checkout / ".git" / "hooks" / "pre-push", marker)
    run_git(checkout, "switch", "-q", "-c", BRANCH)
    (checkout / "note.md").write_text("A note.\n", encoding="utf-8")
    run_git(checkout, "add", "-A")
    run_git(checkout, "commit", "-q", "-m", "Add a note")
    commit = run_git(checkout, "rev-parse", "HEAD").strip()

    assert git.push(BRANCH) == "pushed"
    assert remote_commit(remote, BRANCH) == commit


def _commit_with_configured_hooks_path(git: GitCli, checkout: Path, marker: Path, _: Path) -> None:
    folder = marker.parent / "elsewhere-hooks"
    _write_hook(folder / "pre-commit", marker)
    run_git(checkout, "config", "core.hooksPath", str(folder))
    (checkout / "note.md").write_text("A note.\n", encoding="utf-8")

    commit = git.commit("Add a note")

    assert run_git(checkout, "rev-parse", "HEAD").strip() == commit


OPERATIONS = [
    pytest.param(_commit_with_pre_commit, id="pre-commit"),
    pytest.param(_checkout_with_post_checkout, id="post-checkout"),
    pytest.param(_push_with_pre_push, id="pre-push"),
    pytest.param(_commit_with_configured_hooks_path, id="configured-hooks-path"),
]


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize(
    ("options", "hook_runs"),
    [pytest.param(FACTORY, False, id="factory"), pytest.param(PLAIN, True, id="plain")],
)
def test_the_factorys_git_runs_no_hook_of_the_checkout(
    tmp_path: Path, remote: Path, operation: Operation, options: GitOptions, hook_runs: bool
) -> None:
    checkout = clone(remote, tmp_path / CHECKOUT)
    marker = tmp_path / "hook-ran"

    operation(GitCli(checkout, options), checkout, marker, remote)

    assert marker.exists() == hook_runs


@pytest.mark.parametrize(
    "options", [pytest.param(FACTORY, id="factory"), pytest.param(PLAIN, id="plain")]
)
def test_a_refusing_pre_receive_hook_of_the_remote_still_rejects_the_push(
    tmp_path: Path, remote: Path, options: GitOptions
) -> None:
    checkout = clone(remote, tmp_path / CHECKOUT)
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    run_git(checkout, "switch", "-q", "-c", BRANCH)
    (checkout / "note.md").write_text("A note.\n", encoding="utf-8")
    run_git(checkout, "add", "-A")
    run_git(checkout, "commit", "-q", "-m", "Add a note")

    assert GitCli(checkout, options).push(BRANCH) == "rejected"

    assert remote_commit(remote, BRANCH) is None
