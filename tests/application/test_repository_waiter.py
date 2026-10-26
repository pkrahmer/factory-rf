"""The wait for a repository that is not ready: each fault one `repository_unavailable` stop."""

import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.machine import FactoryLog
from factory.application.scheduler import CheckoutPreparer, RepositoryWaiter
from factory.application.stops import StopService
from factory.domain.git import GitOptions
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop
from git_support import (
    PIPELINE_YAML,
    TEST_IDENTITY,
    clone,
    commit_all,
    remote_commit,
    run_git,
    write_files,
)
from human_clone import HumanClone
from settings_support import AGENT_HOME

NO_MAIN = "the repository has no main branch yet"
NO_PIPELINE = "origin/main has no factory/pipeline.yml yet"


class RecordingLog(FactoryLog):
    """Keeps the lines written to it."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)

    def stop_lines(self) -> list[str]:
        return [line for line in self.lines if line.startswith("stop ")]


class Instance:
    """One instance's checkout of a repository URL, its waiter and what the waiter reported."""

    def __init__(self, boundaries: Boundaries, directory: Path, url: str) -> None:
        self.directory = directory
        self.log = RecordingLog()
        self.git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
        self.boundaries = replace(boundaries, git=self.git, log=self.log, checkout=directory)
        settings = InstanceSettings(
            repository_url=url, instance="factory-1", agent_home=AGENT_HOME, checkout=directory
        )
        self.waiter = RepositoryWaiter(
            CheckoutPreparer(self.git, settings), self.boundaries, StopService(self.boundaries)
        )

    def unavailable(self) -> list[RepositoryStop]:
        return [
            stop
            for stop in self.boundaries.health.read().stops
            if stop.reason == "repository_unavailable"
        ]


InstanceFactory = Callable[[str], Instance]


@pytest.fixture
def instance(boundaries: Boundaries, tmp_path: Path) -> InstanceFactory:
    """Return a maker of the instance on a URL, its checkout at `tmp_path / "instance"`."""

    def make(url: str) -> Instance:
        return Instance(boundaries, tmp_path / "instance", url)

    return make


@pytest.fixture
def empty_remote(tmp_path: Path) -> Path:
    """Return a bare repository without any commit."""
    root = tmp_path / "empty"
    root.mkdir()
    run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
    return root / "remote.git"


def _push_main(remote: Path, files: dict[str, str]) -> str:
    """Push a commit of `files` as `main` of `remote` from a seed of its own; return its id."""
    seed = remote.parent / "seed"
    if not seed.exists():
        run_git(remote.parent, "init", "-q", "--initial-branch=main", "seed")
    write_files(seed, files)
    commit = commit_all(seed, "seed")
    run_git(seed, "push", "-q", "--force", str(remote), "main")
    return commit


def test_a_ready_checkout_is_not_fetched_and_leaves_no_stop(
    tmp_path: Path, remote: Path, human: HumanClone, instance: InstanceFactory
) -> None:
    clone(remote, tmp_path / "instance")
    ready = instance(str(remote))
    human.push_file("main", "docs/later.md", "pushed after the clone\n")
    later = remote_commit(remote, "main")

    prepared = ready.waiter.prepare()

    assert prepared is True
    assert ready.unavailable() == []
    assert later is not None
    assert ready.git.resolve("origin/main") != later


def _missing_url(tmp_path: Path) -> str:
    return str(tmp_path / "no-such-remote.git")


def _deleted_after_clone(tmp_path: Path) -> str:
    root = tmp_path / "vanishing"
    root.mkdir()
    run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
    remote = root / "remote.git"
    clone(remote, tmp_path / "instance")
    shutil.rmtree(remote)
    return str(remote)


@pytest.mark.parametrize(
    ("arrange", "prefix"),
    [
        (_missing_url, "cannot prepare the checkout: git clone --quiet "),
        (_deleted_after_clone, "cannot fetch: git fetch --prune origin failed"),
    ],
)
def test_a_failing_clone_or_fetch_is_one_stop_naming_the_git_error(
    tmp_path: Path,
    instance: InstanceFactory,
    arrange: Callable[[Path], str],
    prefix: str,
) -> None:
    waiting = instance(arrange(tmp_path))

    prepared = waiting.waiter.prepare()

    assert prepared is False
    stops = waiting.unavailable()
    assert len(stops) == 1
    assert stops[0].scope == "repository"
    assert stops[0].detail.startswith(prefix)


def test_a_remote_without_any_commit_is_a_stop_at_the_clocks_time(
    empty_remote: Path, instance: InstanceFactory, clock: ManualClock
) -> None:
    waiting = instance(str(empty_remote))

    prepared = waiting.waiter.prepare()

    assert prepared is False
    assert [(stop.detail, stop.at) for stop in waiting.unavailable()] == [(NO_MAIN, clock.now())]


def test_the_pushed_pipeline_definition_is_fetched_and_clears_the_stop(
    empty_remote: Path, instance: InstanceFactory
) -> None:
    waiting = instance(str(empty_remote))
    waiting.waiter.prepare()
    pushed = _push_main(empty_remote, {"factory/pipeline.yml": PIPELINE_YAML})

    prepared = waiting.waiter.prepare()

    assert prepared is True
    assert waiting.git.resolve("origin/main") == pushed
    assert waiting.unavailable() == []


def test_a_main_branch_without_the_pipeline_definition_is_a_stop(
    empty_remote: Path, instance: InstanceFactory
) -> None:
    _push_main(empty_remote, {"README.md": "no factory here\n"})
    waiting = instance(str(empty_remote))

    prepared = waiting.waiter.prepare()

    assert prepared is False
    assert [stop.detail for stop in waiting.unavailable()] == [NO_PIPELINE]


def test_a_repeated_fault_is_reported_once_and_a_changed_fault_again(
    empty_remote: Path, instance: InstanceFactory
) -> None:
    waiting = instance(str(empty_remote))

    waiting.waiter.prepare()
    waiting.waiter.prepare()
    after_repeat = len(waiting.log.stop_lines())
    _push_main(empty_remote, {"README.md": "no factory here\n"})
    waiting.waiter.prepare()
    run_git(empty_remote, "update-ref", "-d", "refs/heads/main")
    waiting.waiter.prepare()

    assert after_repeat == 1
    assert waiting.log.stop_lines() == [
        f"stop repository repository_unavailable: {NO_MAIN}",
        f"stop repository repository_unavailable: {NO_PIPELINE}",
        f"stop repository repository_unavailable: {NO_MAIN}",
    ]
    assert [stop.detail for stop in waiting.unavailable()] == [NO_MAIN]
