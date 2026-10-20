"""The tick's restore removes the git-ignored paths before it switches to `main`."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.tick import IdleHandler, Tick
from factory.domain.identifiers import branch_name
from git_support import CHECKOUT, write_files
from log_support import log_lines
from root_support import AS_ROOT
from tick_support import handlers_of

INSTANCE = "factory-1"
BRANCH = branch_name("F0001-S0001")
STANDIN = "standin\n"

Setup = Callable[[GitCli, Path], None]

pytestmark = pytest.mark.usefixtures("installed_agents")


def _excluded(checkout: GitCli, directory: Path) -> None:
    del checkout
    (directory / ".git" / "info" / "exclude").write_text("ignored.log\n", encoding="utf-8")
    write_files(directory, {"ignored.log": STANDIN})


def _hidden_by_the_branch(checkout: GitCli, directory: Path) -> None:
    checkout.checkout(BRANCH, start_point="origin/main")
    write_files(directory, {"src/.gitignore": "*.dat\n"})
    checkout.commit("the branch's own ignore rule")
    write_files(directory, {"src/x.dat": STANDIN})


def _locked(checkout: GitCli, directory: Path) -> None:
    del checkout
    (directory / ".git" / "info" / "exclude").write_text("locked/\n", encoding="utf-8")
    locked = directory / "locked"
    write_files(locked, {"file.txt": STANDIN})
    locked.chmod(0o555)


@pytest.mark.parametrize(
    ("setup", "path", "stopped"),
    [
        pytest.param(_excluded, "ignored.log", None, id="info-exclude"),
        pytest.param(_hidden_by_the_branch, "src/x.dat", None, id="branch-gitignore"),
        pytest.param(_locked, "locked", "checkout_restore_failed", id="unremovable", marks=AS_ROOT),
    ],
)
def test_the_restore_removes_the_ignored_paths(
    boundaries: Boundaries,
    checkout: GitCli,
    tmp_path: Path,
    *,
    setup: Setup,
    path: str,
    stopped: str | None,
) -> None:
    directory = tmp_path / CHECKOUT
    setup(checkout, directory)
    tick = Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler()}))

    try:
        outcome = tick.run()
    finally:
        if (directory / "locked").exists():
            (directory / "locked").chmod(0o755)

    assert outcome.stopped == stopped
    if stopped is None:
        assert not (directory / path).exists()
        status = checkout.status()
        assert status.branch == "main"
        assert status.head == checkout.resolve("origin/main")
        assert [line for line in log_lines(tmp_path) if path in line] == []
    else:
        [stop] = [stop for stop in boundaries.health.read().stops if stop.reason == stopped]
        assert stop.detail.startswith("git clean --quiet --force --force -d -X failed (exit 1)")
