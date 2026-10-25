"""The tick's restore discards uncommitted changes and keeps the git-ignored files."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.tick import IdleHandler, Tick
from git_support import CHECKOUT, write_files
from log_support import log_lines
from stage_run_support import INSTANCE
from tick_support import handlers_of

pytestmark = pytest.mark.usefixtures("installed_agents")


def test_the_restore_discards_an_untracked_file_and_keeps_an_ignored_one(
    boundaries: Boundaries, checkout: GitCli, tmp_path: Path
) -> None:
    directory = tmp_path / CHECKOUT
    (directory / ".git" / "info" / "exclude").write_text(".venv/\n", encoding="utf-8")
    write_files(directory, {".venv/x": "kept\n", "src/a.py": "untracked\n"})

    Tick(boundaries, INSTANCE, handlers_of({"idle": IdleHandler()})).run()

    assert not (directory / "src" / "a.py").exists()
    assert (directory / ".venv" / "x").read_text(encoding="utf-8") == "kept\n"
    status = checkout.status()
    assert status.branch == "main"
    assert status.head == checkout.resolve("origin/main")
    assert any(
        line.endswith(" discarded uncommitted changes: src/a.py") for line in log_lines(tmp_path)
    )
