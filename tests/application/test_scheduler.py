"""Tests for the scheduler's loop and pauses, and for the checkout preparer."""

import shutil
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.machine import FactoryLog
from factory.application.scheduler import CheckoutPreparer, Scheduler, pause_after
from factory.domain.errors import AgentRuntimeError, GitError
from factory.domain.git import GitOptions
from factory.domain.kill_points import InjectedKill, KillPoint
from factory.domain.settings import InstanceSettings
from git_support import CHECKOUT, TEST_IDENTITY
from settings_support import AGENT_HOME

Outcome = bool | BaseException


class RecordingLog(FactoryLog):
    """Keeps the lines written to it."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)


class Loop:
    """Recording callables for one scheduler: scripted outcomes, every call kept in order."""

    def __init__(self, prepares: Iterable[Outcome], ticks: Iterable[Outcome]) -> None:
        self._prepares = iter(prepares)
        self._ticks = iter(ticks)
        self.calls: list[str] = []
        self.sleeps: list[float] = []
        self.log = RecordingLog()

    def count(self, name: str) -> int:
        return self.calls.count(name)

    def prepare(self) -> bool:
        self.calls.append("prepare")
        return _outcome(next(self._prepares, True))

    def tick(self) -> bool:
        self.calls.append("tick")
        return _outcome(next(self._ticks, True))

    def sleep(self, seconds: float) -> None:
        self.calls.append("sleep")
        self.sleeps.append(seconds)

    def run(self, stop_when: Callable[["Loop"], bool]) -> None:
        Scheduler(
            prepare=self.prepare,
            tick=self.tick,
            sleep=self.sleep,
            should_stop=lambda: stop_when(self),
            log=self.log,
        ).run()


def _outcome(outcome: Outcome) -> bool:
    if isinstance(outcome, BaseException):
        raise outcome
    return outcome


@pytest.mark.parametrize(
    ("idle_ticks", "seconds"),
    [(0, 15), (1, 30), (2, 60), (3, 120), (4, 120), (10, 120)],
)
def test_pause_doubles_from_fifteen_seconds_up_to_two_minutes(
    idle_ticks: int, seconds: int
) -> None:
    assert pause_after(idle_ticks) == timedelta(seconds=seconds)


def test_negative_idle_count_is_refused() -> None:
    with pytest.raises(ValueError):
        pause_after(-1)


def test_each_iteration_prepares_then_ticks_and_the_first_comes_before_any_sleep() -> None:
    loop = Loop(prepares=[], ticks=[])
    loop.run(lambda loop: loop.count("tick") >= 3)
    assert loop.calls == [
        "prepare",
        "tick",
        "sleep",
        "prepare",
        "tick",
        "sleep",
        "prepare",
        "tick",
    ]
    assert loop.count("tick") == 3
    assert loop.count("sleep") == 2


def test_stop_from_the_start_calls_nothing() -> None:
    loop = Loop(prepares=[], ticks=[])
    loop.run(lambda _: True)
    assert loop.calls == []


@pytest.mark.parametrize(
    ("ticks", "sleeps"),
    [
        ([True, False, False, False, False, False], [15.0, 30.0, 60.0, 120.0, 120.0]),
        ([False, False, True, False], [30.0, 60.0, 15.0]),
    ],
)
def test_sleeps_follow_the_idle_count_since_the_last_activity(
    ticks: list[bool], sleeps: list[float]
) -> None:
    loop = Loop(prepares=[], ticks=ticks)
    loop.run(lambda loop: loop.count("tick") >= len(ticks))
    assert loop.sleeps == sleeps


def test_a_failed_preparation_skips_the_tick_and_counts_as_idle() -> None:
    loop = Loop(prepares=[False, True, True], ticks=[])
    loop.run(lambda loop: loop.count("prepare") >= 3)
    assert loop.count("tick") == 2
    assert loop.sleeps == [30.0, 15.0]


def test_an_exception_from_the_tick_is_logged_and_counts_as_idle() -> None:
    loop = Loop(prepares=[], ticks=[ValueError("boom"), True])
    loop.run(lambda loop: loop.count("tick") >= 2)
    assert loop.log.lines == ["iteration failed: ValueError: boom"]
    assert loop.calls == ["prepare", "tick", "sleep", "prepare", "tick"]
    assert loop.sleeps == [30.0]


def test_an_exception_from_the_preparation_is_logged_skips_the_tick_and_counts_as_idle() -> None:
    loop = Loop(prepares=[ValueError("boom"), True], ticks=[])
    loop.run(lambda loop: loop.count("prepare") >= 2)
    assert loop.log.lines == ["iteration failed: ValueError: boom"]
    assert loop.calls == ["prepare", "sleep", "prepare", "tick"]
    assert loop.sleeps == [30.0]


def test_an_injected_kill_from_the_tick_leaves_the_loop_unlogged() -> None:
    loop = Loop(prepares=[], ticks=[InjectedKill(KillPoint.AGENT_RUN)])
    with pytest.raises(InjectedKill):
        loop.run(lambda _: False)
    assert loop.log.lines == []


_LOOP_ERRORS = [
    (
        GitError("git fetch", 128, "boom"),
        "iteration failed: GitError: git fetch failed (exit 128): boom",
    ),
    (OSError("boom"), "iteration failed: OSError: boom"),
    (
        AgentRuntimeError("boom"),
        "iteration failed: AgentRuntimeError: agent runtime failed: boom",
    ),
    (RuntimeError("boom"), "iteration failed: RuntimeError: boom"),
]


@pytest.mark.parametrize(
    ("raising_side", "calls"),
    [
        ("tick", ["prepare", "tick", "sleep", "prepare", "tick", "sleep"]),
        ("prepare", ["prepare", "sleep", "prepare", "tick", "sleep"]),
    ],
)
@pytest.mark.parametrize(("error", "line"), _LOOP_ERRORS)
def test_every_kind_of_error_the_loop_meets_is_logged_once_and_counts_as_idle(
    raising_side: str, calls: list[str], error: Exception, line: str
) -> None:
    first_fails: list[Outcome] = [error, True]
    if raising_side == "tick":
        loop = Loop(prepares=[], ticks=first_fails)
    else:
        loop = Loop(prepares=first_fails, ticks=[True])
    loop.run(lambda loop: loop.count("sleep") >= 2)
    assert loop.log.lines == [line]
    assert loop.calls == calls
    assert loop.sleeps == [30.0, 15.0]


def _settings(remote: Path, checkout: Path) -> InstanceSettings:
    return InstanceSettings(
        repository_url=str(remote), instance="one", agent_home=AGENT_HOME, checkout=checkout
    )


def _tree(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): path.read_text() if path.is_file() else "/"
        for path in sorted(directory.rglob("*"))
    }


def test_a_missing_checkout_is_cloned_and_cloned_again_after_removal(
    tmp_path: Path, remote: Path
) -> None:
    directory = tmp_path / "work" / CHECKOUT
    git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
    preparer = CheckoutPreparer(git, _settings(remote, directory))

    preparer.prepare()
    assert git.resolve("origin/main") is not None

    shutil.rmtree(directory)
    preparer.prepare()
    assert git.resolve("origin/main") is not None


@pytest.mark.usefixtures("checkout")
def test_an_existing_clone_is_kept_without_calling_git(tmp_path: Path, remote: Path) -> None:
    directory = tmp_path / CHECKOUT
    added = directory / "added-by-test.txt"
    added.write_text("kept\n")
    no_git = GitOptions(executable=str(tmp_path / "missing" / "git"))
    preparer = CheckoutPreparer(GitCli(directory, no_git), _settings(remote, directory))

    preparer.prepare()
    assert added.read_text() == "kept\n"


def test_a_directory_with_files_but_no_clone_is_refused_unchanged(
    tmp_path: Path, remote: Path
) -> None:
    directory = tmp_path / "work" / CHECKOUT
    directory.mkdir(parents=True)
    (directory / "notes.txt").write_text("left by the operator\n")
    before = _tree(directory)
    git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
    preparer = CheckoutPreparer(git, _settings(remote, directory))

    with pytest.raises(GitError):
        preparer.prepare()
    assert _tree(directory) == before
