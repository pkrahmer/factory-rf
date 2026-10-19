"""Fixtures shared by the whole test suite."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from acceptance_walk import AcceptanceWalk
from confine_support import Layout, build_layout
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
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.domain.git import GitOptions
from factory.domain.identifiers import WorkItemId
from factory.domain.kill_points import KillPoints
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord
from git_support import CHECKOUT, TEST_IDENTITY, clone, copy_remote, make_remote
from human_clone import HumanClone
from proof_support import World, build_world, start_story
from tmp_path_support import reopen
from wiring_support import HOSTED_URL


@pytest.fixture(autouse=True)
def reopened_tmp_path(request: pytest.FixtureRequest) -> Iterator[None]:
    """After a test that uses `tmp_path`, give its owner back every folder and file under it."""
    if "tmp_path" not in request.fixturenames:
        yield
        return
    tmp_path: Path = request.getfixturevalue("tmp_path")
    yield
    reopen(tmp_path)


@pytest.fixture
def group_umask() -> Iterator[None]:
    """Run the test under the entrypoint's umask `0002` and restore the previous one afterwards."""
    previous = os.umask(0o002)
    yield
    os.umask(previous)


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


@pytest.fixture(scope="session")
def remote_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return the folder of one remote made per session, which each test's remote copies."""
    return make_remote(tmp_path_factory.mktemp("remote-template")).parent


@pytest.fixture
def remote(tmp_path: Path, remote_template: Path) -> Path:
    """Return a bare repository whose `main` holds a small factory layout."""
    return copy_remote(remote_template, tmp_path / "origin")


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
def local_settings(tmp_path: Path) -> InstanceSettings:
    """Settings whose checkout, state directory and agent home lie in `tmp_path`."""
    root = tmp_path.resolve()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
    )


@pytest.fixture
def hosted_environment(tmp_path: Path) -> dict[str, str]:
    """Return a valid environment whose token and image identity files lie in `tmp_path`."""
    token = tmp_path / "hosting-token"
    token.write_text("example-value\n", encoding="utf-8")
    image = tmp_path / "image-id"
    image.write_text("build-7\n", encoding="utf-8")
    return {
        "FACTORY_REPOSITORY_URL": HOSTED_URL,
        "FACTORY_INSTANCE": "factory-1",
        "FACTORY_IMAGE_ID_FILE": str(image),
        "FACTORY_TOKEN_FILE": str(token),
    }


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


@pytest.fixture
def world(tmp_path: Path, remote_template: Path) -> World:
    """Return a world of the recovery proof built under `tmp_path`."""
    return build_world(tmp_path, template=remote_template)


@pytest.fixture
def work_item(world: World) -> WorkItemId:
    """Return a story started in the world, its work item on its branch."""
    return start_story(world)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    """A checkout with `src` and `other`, a home and a temporary root under `tmp_path`."""
    return build_layout(tmp_path)


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[StopRecord]:
    """The stop records in the test's state directory."""
    return JsonLinesRecordLog(tmp_path / "state" / "records" / "stops.jsonl", StopRecord)
