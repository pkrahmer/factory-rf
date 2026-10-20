"""Project commands run with the checkout's git folder sealed, as an agent run does."""

import shutil
import stat
from collections.abc import Callable, Sequence
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from application.test_checkout_preparer_seal import RecordingLog
from factory.adapters.git_cli import GitCli
from factory.application.project_commands import ProjectCommands
from factory.application.sealed_runs import SealedProjectCommands
from factory.domain.checks import CheckResult
from factory.domain.errors import ProjectCommandError, RepositoryUnsealed
from git_support import run_git
from project_command_support import raising

OPEN_FOLDER = 0o2775
LIMIT = timedelta(seconds=30)
NESTED = "nested"
PASSED = CheckResult(
    command="check",
    status="passed",
    exit_status=0,
    duration=timedelta(seconds=3),
    last_line="check: green",
    output_tail="check: green\n",
)

Answer = Callable[[str, timedelta], CheckResult]
Act = Callable[[Path], None]


def _passed(_command: str, _limit: timedelta) -> CheckResult:
    return PASSED


def _nothing(checkout: Path) -> None:
    del checkout


def _nest(checkout: Path, folders: Sequence[str] = (NESTED,)) -> None:
    for folder in folders:
        directory = checkout / folder
        directory.mkdir(parents=True)
        run_git(directory, "init", "--quiet")


def _open_git_folder(checkout: Path) -> None:
    moved = checkout.parent / "moved-git"
    (checkout / ".git").rename(moved)
    shutil.copytree(moved, checkout / ".git", symlinks=True)
    (checkout / ".git").chmod(OPEN_FOLDER)


def _nest_and_open(checkout: Path) -> None:
    _nest(checkout)
    _open_git_folder(checkout)


def _remove_git_folder(checkout: Path) -> None:
    shutil.rmtree(checkout / ".git")


class ProbeCommands(ProjectCommands):
    """Records each call and whether `.git` was group-writable during it, then acts and answers."""

    def __init__(self, checkout: Path, act: Act, answer: Answer) -> None:
        self._checkout = checkout
        self._act = act
        self._answer = answer
        self.calls: list[tuple[str, timedelta]] = []
        self.group_writable: list[bool] = []

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        self.calls.append((command, time_limit))
        mode = (self._checkout / ".git").lstat().st_mode
        self.group_writable.append(bool(mode & stat.S_IWGRP))
        self._act(self._checkout)
        return self._answer(command, time_limit)


@pytest.fixture
def directory(checkout: GitCli, tmp_path: Path) -> Path:
    """Return the working copy of the `checkout` clone."""
    del checkout
    return tmp_path / "checkout"


def test_the_inner_command_runs_with_a_sealed_git_folder_and_its_result_is_returned(
    checkout: GitCli, directory: Path
) -> None:
    (directory / ".git").chmod(OPEN_FOLDER)
    inner = ProbeCommands(directory, _nothing, _passed)

    result = SealedProjectCommands(inner, checkout, RecordingLog()).run("check", time_limit=LIMIT)

    assert inner.group_writable == [False]
    assert inner.calls == [("check", LIMIT)]
    assert result == PASSED


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        pytest.param(_passed, None, id="returns"),
        pytest.param(
            raising(ProjectCommandError("check", "no make")),
            ProjectCommandError,
            id="project-command-error",
        ),
        pytest.param(raising(ValueError("bad output")), ValueError, id="value-error"),
    ],
)
def test_nested_repositories_are_removed_after_every_inner_run(
    checkout: GitCli, directory: Path, *, answer: Answer, expected: type[Exception] | None
) -> None:
    inner = ProbeCommands(directory, _nest, answer)
    sealed = SealedProjectCommands(inner, checkout, RecordingLog())

    if expected is None:
        sealed.run("check", time_limit=LIMIT)
    else:
        with pytest.raises(expected):
            sealed.run("check", time_limit=LIMIT)

    assert not (directory / NESTED / ".git").exists()
    assert len(inner.calls) == 1


@pytest.mark.parametrize(
    ("before", "act", "answer", "context", "called"),
    [
        pytest.param(_nothing, _nest_and_open, _passed, None, True, id="opened-during-the-run"),
        pytest.param(
            _nothing,
            _nest_and_open,
            raising(ProjectCommandError("check", "no make")),
            ProjectCommandError,
            True,
            id="opened-then-project-command-error",
        ),
        pytest.param(_remove_git_folder, _nest, _passed, None, False, id="missing-before-the-run"),
    ],
)
def test_a_run_raises_unless_git_is_sealed_before_and_after_it(
    checkout: GitCli,
    directory: Path,
    *,
    before: Act,
    act: Act,
    answer: Answer,
    context: type[Exception] | None,
    called: bool,
) -> None:
    inner = ProbeCommands(directory, act, answer)
    sealed = SealedProjectCommands(inner, checkout, RecordingLog())
    before(directory)

    with pytest.raises(RepositoryUnsealed) as raised:
        sealed.run("check", time_limit=LIMIT)

    if context is None:
        assert not isinstance(raised.value.__context__, ProjectCommandError)
    else:
        assert isinstance(raised.value.__context__, context)
    assert (len(inner.calls) == 1) == called
    assert (directory / NESTED / ".git").exists() == called


@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        pytest.param(
            ["a", "b/c"],
            ["removed nested repositories after check: a/.git, b/c/.git"],
            id="two-nested",
        ),
        pytest.param([], [], id="none"),
    ],
)
def test_the_removed_nested_repositories_are_logged_in_one_line(
    checkout: GitCli, directory: Path, *, folders: list[str], expected: list[str]
) -> None:
    log = RecordingLog()
    inner = ProbeCommands(directory, lambda path: _nest(path, folders), _passed)

    result = SealedProjectCommands(inner, checkout, log).run("check", time_limit=LIMIT)

    assert log.lines == expected
    assert result == PASSED


def test_sealed_project_commands_implement_the_project_commands_interface() -> None:
    assert issubclass(SealedProjectCommands, ProjectCommands)
