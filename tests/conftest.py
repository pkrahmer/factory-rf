"""Fixtures shared by the whole test suite."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from acceptance_walk import AcceptanceWalk
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
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


@pytest.fixture
def agent_home(tmp_path: Path) -> Path:
    """Return the test's agent home, `tmp_path / "agent-home"`; nothing is created in it."""
    return tmp_path / "agent-home"


@pytest.fixture
def boundaries(
    tmp_path: Path,
    checkout: GitCli,
    *,
    agent_home: Path,
    hosting: FakeHostingService,
    agent_runtime: FakeAgentRuntime,
    kill_points: KillPoints,
    clock: ManualClock,
) -> Boundaries:
    """Return the interfaces on the test's checkout, fakes and clock, the state under `tmp_path`."""
    state = tmp_path / "state"
    return Boundaries(
        git=checkout,
        hosting=hosting,
        agent_runtime=agent_runtime,
        project_commands=MakeProjectCommands(tmp_path / CHECKOUT, kill_points),
        work_item_reader=FrontmatterWorkItemReader(),
        work_item_writer=FrontmatterWorkItemWriter(),
        cost_reader=JsonLinesCostRecordReader(),
        cost_writer=JsonLinesCostRecordWriter(),
        pipeline_reader=RuamelPipelineDefinitionReader(),
        agent_definitions=FrontmatterAgentDefinitionReader(agent_home),
        clock=clock,
        log=TimestampedFactoryLog(state / "factory.log", clock),
        health=JsonHealthStatusFile(state / "health.json"),
        checkout=tmp_path / CHECKOUT,
    )


@pytest.fixture
def walk(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    hosting: FakeHostingService,
    agent_home: Path,
) -> AcceptanceWalk:
    """Return a walk over the feature `F0002-todo`, due with two archived stories."""
    return AcceptanceWalk(
        boundaries, remote=remote, human=human, hosting=hosting, agent_home=agent_home
    )
