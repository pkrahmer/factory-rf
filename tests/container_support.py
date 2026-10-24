"""Shared helpers of the container environment tests: a dataset beside the host and its fakes."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path

from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.containers import ContainerRuns
from factory.application.project_commands import ProjectCommands
from factory.application.snapshots import Snapshots
from factory.application.stage import StageReport
from factory.application.stage_environment import ContainerEnvironment
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount
from factory.domain.git import ChangedPath, CommitId
from factory.domain.settings import InstanceSettings
from git_support import install_agents, run_git, write_files
from human_clone import HumanClone
from podman_support import IMAGE
from stage_run_support import branch_head, completed, open_story, pushed, run_stage, stage_makefile
from take_support import AGENT_TEXT
from undo_support import start_stage
from zfs_support import DATASET, MOUNT_POINT

SYNC_MARKER = ".synced"
SYNC_RECIPE = f"@echo synced > {SYNC_MARKER}"
TIMING_PREFIX = "stage environment:"
TAKE_SECONDS = 0.25
FIVE_MINUTES = timedelta(minutes=5)
INSIDE = "tests/test_a.py"
NOTES = "notes.md"
CONTAINER: dict[str, object] = {
    "stage_environment": "container",
    "dataset": DATASET,
    "workspace": str(MOUNT_POINT),
    "stage_image": IMAGE,
}


def sync_makefile(recipe: str = SYNC_RECIPE) -> str:
    """A Makefile whose `sync` runs `recipe`; by default it writes the marker `.synced`."""
    return f".PHONY: sync\n\nsync:\n\t{recipe}\n"


@dataclass(frozen=True)
class Dataset:
    """The boundaries with the two fakes set, the fakes, and the dataset's folder and base."""

    boundaries: Boundaries
    snapshots: FakeSnapshots
    containers: FakeContainerRuns
    workspace: Path
    base: Path


def container_instance_settings(tmp_path: Path, agent_home: Path) -> InstanceSettings:
    """Settings of a container instance: its workspace and state under `tmp_path`."""
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "state_directory": tmp_path / "state",
            "agent_home": agent_home,
            "pinned_agent_version": "fake",
            **CONTAINER,
            "workspace": tmp_path / "workspace",
        }
    )


def container_dataset(boundaries: Boundaries, tmp_path: Path, *, with_base: bool = True) -> Dataset:
    """An empty dataset at `<tmp_path>/workspace`; its empty base beside it when `with_base`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    base = tmp_path / "base"
    if with_base:
        base.mkdir()
    snapshots = FakeSnapshots(workspace, base)
    containers = FakeContainerRuns(workspace)
    return Dataset(
        boundaries=replace(boundaries, snapshots=snapshots, containers=containers),
        snapshots=snapshots,
        containers=containers,
        workspace=workspace,
        base=base,
    )


def push_main(boundaries: Boundaries, human: HumanClone, files: dict[str, str]) -> CommitId:
    """Push `files` to `main`, bring the host's `main` to it and return its commit."""
    human.push_files("main", files)
    git = boundaries.git
    git.fetch()
    git.checkout("main", start_point="origin/main")
    commit = git.resolve("main")
    assert commit is not None
    return commit


def dataset_git(dataset: Dataset, *args: str) -> str:
    """Run git in the dataset's checkout and return its output."""
    return run_git(dataset.workspace / "checkout", *args)


def local_branches(dataset: Dataset) -> list[str]:
    """The local branches of the dataset's repository, by name."""
    return dataset_git(dataset, "branch", "--format=%(refname:short)").split()


def timing_lines(boundaries: Boundaries) -> list[str]:
    """The lines of the factory log that carry the stage environment's timing."""
    log = boundaries.settings.state_directory / "factory.log"
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if TIMING_PREFIX in line]


def started_with_sync(boundaries: Boundaries, human: HumanClone, agent_home: Path) -> StageStart:
    """Push a `sync` Makefile to `main` and start a tester stage writing `src/*`."""
    push_main(boundaries, human, {"Makefile": sync_makefile(), ".gitignore": ".venv/\n"})
    install_agents(agent_home, ["tester"])
    return start_stage(boundaries, human, write_paths=["src/*", "{work_item}"])


@dataclass(frozen=True)
class Steps:
    """The seconds one `prepare` spends inside `reset`, the sync container's run and `advance`."""

    reset: float
    sync: float
    advance: float


@dataclass
class Pace:
    """The steps the clocked fakes advance the clock by; the test sets them before each prepare."""

    steps: Steps
    take: float = TAKE_SECONDS


FIRST = Steps(reset=0.4, sync=12.3, advance=0.1)
SECOND = Steps(reset=1.0, sync=2.0, advance=3.0)


class ClockedSnapshots(Snapshots):
    """Snapshots that advance the manual clock inside `reset`, `advance` and `changed_paths`."""

    def __init__(self, delegate: Snapshots, clock: ManualClock, pace: Pace) -> None:
        """Delegate to `delegate`, advancing `clock` by `pace`."""
        self._delegate = delegate
        self._clock = clock
        self._pace = pace

    @property
    def mount_point(self) -> Path:
        """The delegate's mount point."""
        return self._delegate.mount_point

    def reset(self) -> None:
        """Advance by the pace's reset, then reset."""
        self._clock.advance(timedelta(seconds=self._pace.steps.reset))
        self._delegate.reset()

    def advance(self) -> None:
        """Advance by the pace's advance, then move the base."""
        self._clock.advance(timedelta(seconds=self._pace.steps.advance))
        self._delegate.advance()

    def changed_paths(self) -> list[ChangedPath]:
        """Advance by the pace's take, by default 0.25 s, then compare."""
        self._clock.advance(timedelta(seconds=self._pace.take))
        return self._delegate.changed_paths()


class ClockedContainerRuns(ContainerRuns):
    """Container runs that advance the manual clock by the pace's sync inside each run."""

    def __init__(self, delegate: ContainerRuns, clock: ManualClock, pace: Pace) -> None:
        """Delegate to `delegate`, advancing `clock` by `pace`."""
        self._delegate = delegate
        self._clock = clock
        self._pace = pace

    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """The delegate's launch."""
        return self._delegate.launch(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )

    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Advance by the pace's sync, then run on the delegate."""
        self._clock.advance(timedelta(seconds=self._pace.steps.sync))
        return self._delegate.run(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )


def clocked_environment(dataset: Dataset, clock: ManualClock, pace: Pace) -> ContainerEnvironment:
    """The container environment on the dataset's fakes, each advancing `clock` by `pace`."""
    return ContainerEnvironment(
        dataset.boundaries,
        ClockedSnapshots(dataset.snapshots, clock, pace),
        ClockedContainerRuns(dataset.containers, clock, pace),
    )


class WorkspaceRuntime(AgentRuntime):
    """Writes the agent's files into the dataset's checkout, then lets the delegate play."""

    def __init__(
        self, delegate: FakeAgentRuntime, checkout: Path, writes: Mapping[str, str]
    ) -> None:
        """Write `writes` into `checkout`, then run on `delegate`."""
        self._delegate = delegate
        self._checkout = checkout
        self._writes = writes

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Write the files into the dataset's checkout, then delegate."""
        write_files(self._checkout, dict(self._writes))
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()


def whole_stage(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
    project_commands: Callable[[Dataset], ProjectCommands] | None = None,
) -> tuple[Dataset, StageReport]:
    """Run the story's `tests` stage on a dataset whose agent writes `INSIDE` and `NOTES`.

    `project_commands`, given the dataset, picks the stage's project commands; the host's
    stay by default.
    """
    open_story(
        boundaries,
        human,
        agent_home,
        makefile=stage_makefile() + f"\nsync:\n\t{SYNC_RECIPE}\n",
        main_files={".gitignore": f"{SYNC_MARKER}\n"},
    )
    dataset = container_dataset(boundaries, tmp_path)
    agent_runtime.queue(ScriptedRun(result=completed("doing")))
    runtime = WorkspaceRuntime(
        agent_runtime, dataset.workspace / "checkout", {INSIDE: AGENT_TEXT, NOTES: AGENT_TEXT}
    )
    stage_boundaries = replace(dataset.boundaries, agent_runtime=runtime)
    if project_commands is not None:
        stage_boundaries = replace(stage_boundaries, project_commands=project_commands(dataset))
    return dataset, run_stage(stage_boundaries)


def assert_taken_and_pushed(boundaries: Boundaries, remote: Path, report: StageReport) -> None:
    """Check the stage pushed `INSIDE` but not `NOTES`, logged its timing, kept the host clean."""
    assert report.commit == branch_head(remote)
    assert boundaries.git.show_file(report.commit, INSIDE) == AGENT_TEXT
    assert boundaries.git.show_file(report.commit, NOTES) is None
    journal = pushed(boundaries, remote).body.split("## Journal", 1)[1]
    assert NOTES in journal
    assert len(timing_lines(boundaries)) == 1
    assert boundaries.git.status().changes == []
