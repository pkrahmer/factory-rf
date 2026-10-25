"""Fixtures shared by the whole test suite."""

import os
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from acceptance_walk import AcceptanceWalk
from adapters.container_runtime_support import make_workspace
from compose_support import COMPOSE
from confine_support import Layout, build_layout
from container_support import Dataset, container_dataset
from definition_support import pipeline_definition
from disk_support import FakeDiskSpace
from entrypoint_support import Layout as ImageLayout
from factory.adapters import claude_runtime
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.agent_launch import API_LOGIN_VARIABLE, LOGIN_VARIABLE
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.podman_runs import PodmanRuns
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.domain.disk import DiskRecord
from factory.domain.git import GitOptions
from factory.domain.identifiers import WorkItemId
from factory.domain.kill_points import KillPoints
from factory.domain.known_results import ResultRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord
from git_support import (
    CHECKOUT,
    PIPELINE_YAML,
    TEST_IDENTITY,
    clone,
    copy_remote,
    install_agents,
    make_remote,
)
from human_clone import HumanClone
from podman_support import IMAGE, Podman, PodmanPlan, write_podman
from proof_support import World, build_world, start_story
from run_process_recorder import Recorder
from stage_run_support import INSTANCE
from tmp_path_support import reopen
from wiring_support import HOSTED_URL, PODMAN_VERSION
from zfs_support import DATASET, Answer, Zfs, write_zfs

TESTS_UMASK = 0o022


def pytest_configure() -> None:
    """Run every test under the umask `0o022`, whatever umask pytest was started under."""
    os.umask(TESTS_UMASK)


@pytest.fixture(autouse=True)
def without_agent_login(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the agent's login from every test's environment, so no child process sees it."""
    for name in (LOGIN_VARIABLE, API_LOGIN_VARIABLE):
        monkeypatch.delenv(name, raising=False)


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
def workspace(tmp_path: Path) -> Path:
    """Return the folder the fake container runs play `/work` as, `checkout/` and `home/` made."""
    return make_workspace(tmp_path)


@pytest.fixture
def fake(workspace: Path) -> FakeContainerRuns:
    """Return fake container runs on the test's `workspace`."""
    return FakeContainerRuns(workspace)


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
def probe_settings(agent_home: Path, tmp_path: Path) -> InstanceSettings:
    """Return settings whose agents run as the user `agent`, the state in `tmp_path`."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        pinned_agent_version="fake",
    )


@pytest.fixture
def compose_service() -> dict[str, object]:
    """Return the service `factory` of the compose file."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    services = loaded["services"]
    assert isinstance(services, dict)
    found = services["factory"]
    assert isinstance(found, dict)
    return found


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    """Return an image identity file in `tmp_path` that holds `build-7`."""
    path = tmp_path / "image-id"
    path.write_text("build-7\n", encoding="utf-8")
    return path


@pytest.fixture
def environment(image_file: Path) -> dict[str, str]:
    """Return a valid environment whose image identity file lies in `tmp_path`."""
    return {
        "FACTORY_REPOSITORY_URL": HOSTED_URL,
        "FACTORY_INSTANCE": INSTANCE,
        "FACTORY_IMAGE_ID_FILE": str(image_file),
    }


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
    """Return the interfaces on the test's checkout, fakes and clock, the state under `tmp_path`.

    Every feature is on: the settings name `factory-1` and the test's checkout, state and agent
    home; the fake disk has ample room; the disk, stop and known-result records lie under
    `<tmp_path>/state/records/`; the waiter is a manual one on the `clock` fixture.
    """
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
        settings=InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            checkout=tmp_path / CHECKOUT,
            state_directory=state,
            agent_home=agent_home,
        ),
        disk=FakeDiskSpace(free={tmp_path: 10**12, state: 10**12}, used={tmp_path: 1, state: 1}),
        disk_records=JsonLinesRecordLog(state / "records" / "disk.jsonl", DiskRecord),
        stop_records=JsonLinesRecordLog(state / "records" / "stops.jsonl", StopRecord),
        waiter=ManualWaiter(clock),
        result_records=JsonLinesRecordLog(state / "records" / "known-results.jsonl", ResultRecord),
    )


@pytest.fixture
def definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, with the acceptance stage `acceptance`."""
    return pipeline_definition(boundaries)


@pytest.fixture
def installed(boundaries: Boundaries, agent_home: Path) -> Boundaries:
    """Return boundaries whose agents are installed in the test's agent home."""
    install_agents(agent_home, ["coder"])
    return replace(boundaries, agent_definitions=FrontmatterAgentDefinitionReader(agent_home))


@pytest.fixture
def installed_agents(boundaries: Boundaries, agent_home: Path) -> None:
    """Install a valid agent file for every role of the remote's definition."""
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)


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
def image_layout(tmp_path: Path) -> ImageLayout:
    """Return the image layout, homes, state and stubs of one entrypoint run under `tmp_path`."""
    return ImageLayout(tmp_path)


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[StopRecord]:
    """The stop records in the test's state directory."""
    return JsonLinesRecordLog(tmp_path / "state" / "records" / "stops.jsonl", StopRecord)


@pytest.fixture
def disk_settings(tmp_path: Path) -> InstanceSettings:
    """Return settings whose checkout and state directory lie under `tmp_path`."""
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=tmp_path / CHECKOUT,
        state_directory=tmp_path / "state",
    )


@pytest.fixture
def disk_records(tmp_path: Path) -> JsonLinesRecordLog[DiskRecord]:
    """Return the disk record log of the test, in `tmp_path`."""
    return JsonLinesRecordLog(tmp_path / "state" / "records" / "disk.jsonl", DiskRecord)


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    """Replace the runtime's `run_process` with a `Recorder` and return it."""
    recording = Recorder()
    monkeypatch.setattr(claude_runtime, "run_process", recording)
    return recording


@pytest.fixture
def podman(tmp_path: Path) -> Podman:
    """Return a stand-in `podman` in `tmp_path`, planned to exit 0 silently."""
    return write_podman(tmp_path / "podman-bin")


@pytest.fixture
def versioned_podman(tmp_path: Path) -> Podman:
    """The stand-in `podman`, printing its version and exiting 0 for every call."""
    folder = tmp_path / "podman-bin"
    folder.mkdir()
    return write_podman(folder, PodmanPlan(stdout=f"{PODMAN_VERSION}\n"))


@pytest.fixture
def listing_zfs(tmp_path: Path) -> Zfs:
    """The stand-in `zfs`, answering `--version` and naming the dataset for `list`."""
    folder = tmp_path / "zfs-bin"
    folder.mkdir()
    return write_zfs(
        folder,
        {"--version": Answer(stdout="zfs-2.2.2\n"), "list": Answer(stdout=f"{DATASET}\n")},
    )


@pytest.fixture
def runs(podman: Podman) -> PodmanRuns:
    """Return a `PodmanRuns` over the stand-in `podman`, its dataset at a fixed host path."""
    return PodmanRuns(str(podman.path), IMAGE, Path("/srv/factory/vm/work"))


@pytest.fixture
def dataset(boundaries: Boundaries, tmp_path: Path) -> Dataset:
    """An empty dataset with an empty base, its fakes set in the boundaries."""
    return container_dataset(boundaries, tmp_path)
