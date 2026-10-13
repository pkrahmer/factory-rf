"""Fixtures shared by the whole test suite."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.domain.kill_points import KillPoints
from git_support import CHECKOUT, TEST_IDENTITY, clone, make_remote
from human_clone import HumanClone


@pytest.fixture
def kill_points() -> KillPoints:
    """Return a new, inert set of kill points for each test."""
    return KillPoints()


@pytest.fixture
def agent_runtime(kill_points: KillPoints) -> FakeAgentRuntime:
    """Return a fake agent runtime with nothing queued, on the test's kill points."""
    return FakeAgentRuntime(kill_points)


@pytest.fixture
def hosting(kill_points: KillPoints) -> FakeHostingService:
    """Return a fake hosting service with no pull requests, on the test's kill points."""
    return FakeHostingService(kill_points)


@pytest.fixture
def remote(tmp_path: Path) -> Path:
    """Return a bare repository whose `main` holds a small factory layout."""
    return make_remote(tmp_path / "origin")


@pytest.fixture
def checkout(tmp_path: Path, remote: Path, kill_points: KillPoints) -> GitCli:
    """Return a `GitCli` on a fresh clone of `remote`, at `tmp_path / CHECKOUT`."""
    directory = clone(remote, tmp_path / CHECKOUT)
    return GitCli(directory, GitOptions(kill_points=kill_points, identity=TEST_IDENTITY))


@pytest.fixture
def human(tmp_path: Path, remote: Path) -> HumanClone:
    """Return the human's own clone of `remote`, at `tmp_path / "human"`."""
    return HumanClone(tmp_path / "human", remote)


@pytest.fixture
def clock() -> ManualClock:
    """Return a manual clock started at noon UTC on 2026-10-12."""
    return ManualClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
