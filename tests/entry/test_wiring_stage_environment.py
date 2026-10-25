"""The wiring builds a container instance's boundaries: the dataset's adapters."""

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from entry.test_wiring_login import REPLY
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.make_commands import ContainerMakeCommands
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.podman_runs import PodmanRuns
from factory.adapters.zfs_snapshots import ZfsSnapshots
from factory.application.project_commands import RecordingProjectCommands
from factory.application.tick import Tick
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries, build_tick
from git_support import write_executable
from podman_support import IMAGE
from wiring_support import CREDENTIAL, every_tool
from zfs_support import DATASET


def _recording_stand_in(folder: Path, *, printed: str = "") -> Path:
    """A program that appends its arguments, one JSON list a line, to `calls` beside it."""
    folder.mkdir(parents=True)
    calls = folder / "calls"
    return write_executable(
        folder,
        "import json, sys\n"
        f"with open({str(calls)!r}, 'a', encoding='utf-8') as file:\n"
        "    file.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        f"sys.stdout.write({printed!r})\n",
    )


def _calls(executable: Path) -> list[list[str]]:
    calls = executable.parent / "calls"
    if not calls.exists():
        return []
    return [json.loads(line) for line in calls.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def zfs(tmp_path: Path) -> Path:
    """The stand-in `zfs`, which records its arguments."""
    return _recording_stand_in(tmp_path / "zfs-bin")


@pytest.fixture
def podman(tmp_path: Path) -> Path:
    """The stand-in `podman`, which records its arguments and prints a completed reply."""
    return _recording_stand_in(tmp_path / "podman-bin", printed=REPLY)


@pytest.fixture
def container_settings(tmp_path: Path, zfs: Path, podman: Path) -> InstanceSettings:
    """Settings of a container instance whose paths lie in `tmp_path`, the stand-ins its tools."""
    root = tmp_path.resolve()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        stage_environment="container",
        dataset=DATASET,
        workspace=root / "work",
        stage_image=IMAGE,
        zfs_executable=str(zfs),
        podman_executable=str(podman),
    )


class _Which:
    """A `which` that finds every tool under `/usr/bin` and records every name asked for."""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def __call__(self, name: str) -> str | None:
        self.asked.append(name)
        return f"/usr/bin/{name}"


def test_an_inline_instance_has_no_snapshots_and_no_containers(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
    )

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert boundaries.snapshots is None
    assert boundaries.containers is None


def test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool(
    tmp_path: Path, container_settings: InstanceSettings, zfs: Path, podman: Path
) -> None:
    which = _Which()
    boundaries = build_boundaries(
        container_settings,
        CREDENTIAL,
        hosting=FakeHostingService(),
        which=which,
        end_leftovers=True,
    )

    assert which.asked == []
    snapshots = boundaries.snapshots
    containers = boundaries.containers
    assert isinstance(snapshots, ZfsSnapshots)
    assert snapshots.mount_point == tmp_path.resolve() / "work"
    assert isinstance(containers, PodmanRuns)
    launch = containers.launch(
        ["true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=1),
        working_directory="/work",
    )
    assert launch.argv[0] == str(podman)
    assert IMAGE in launch.argv
    snapshots.reset()
    assert _calls(zfs) == [["rollback", "-r", f"{DATASET}@base"]]
    project_commands = boundaries.project_commands
    assert isinstance(project_commands, RecordingProjectCommands)
    assert isinstance(project_commands.inner, ContainerMakeCommands)
    assert boundaries.agent_home is None


@pytest.mark.parametrize(
    ("runtime", "kind"),
    [
        pytest.param("claude", ClaudeCodeRuntime, id="claude"),
        pytest.param("opencode", OpencodeRuntime, id="opencode"),
    ],
)
def test_a_container_instance_s_runtime_runs_in_its_containers_unconfined(
    container_settings: InstanceSettings, runtime: str, kind: type[object]
) -> None:
    which = _Which()
    boundaries = build_boundaries(
        container_settings.model_copy(update={"agent_runtime": runtime}),
        CREDENTIAL,
        hosting=FakeHostingService(),
        which=which,
        end_leftovers=True,
    )

    assert which.asked == []
    agent_runtime = boundaries.agent_runtime
    assert isinstance(agent_runtime, kind)
    assert isinstance(agent_runtime, ClaudeCodeRuntime | OpencodeRuntime)
    assert agent_runtime.containers is boundaries.containers
    assert agent_runtime.leftovers is None


def test_a_container_instance_s_runtime_mounts_its_login_file(
    tmp_path: Path, container_settings: InstanceSettings, podman: Path
) -> None:
    login = tmp_path.resolve() / "claude-login"
    login.write_text("stand-in-login\n", encoding="utf-8")
    work = tmp_path / "work"
    work.mkdir()
    request = AgentRunRequest(
        agent=AgentDefinition(
            name="coder",
            model="sonnet",
            tools=["Read"],
            effort=None,
            budget_usd=Decimal("1"),
            instructions="Write the code.",
        ),
        prompt="Stage: doing",
        allowed_decisions=["doing", "question"],
        time_limit=timedelta(seconds=30),
        working_directory=work,
        environment={"HOME": "/work/home", "LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
    )
    boundaries = build_boundaries(
        container_settings.model_copy(update={"claude_login_file": login}),
        CREDENTIAL,
        hosting=FakeHostingService(),
    )

    result = boundaries.agent_runtime.run(request)

    assert result.end_reason == "completed"
    [words] = _calls(podman)
    volume = f"{login}:{login}:ro"
    assert any(
        first == "--volume" and second == volume
        for first, second in zip(words, words[1:], strict=False)
    )


def test_wiring_a_container_instance_s_tick_starts_no_tool(
    container_settings: InstanceSettings, zfs: Path, podman: Path
) -> None:
    boundaries = build_boundaries(container_settings, CREDENTIAL, hosting=FakeHostingService())

    tick = build_tick(boundaries, container_settings, every_tool)

    assert isinstance(tick, Tick)
    assert _calls(zfs) == []
    assert _calls(podman) == []
