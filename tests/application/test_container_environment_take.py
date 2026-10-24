"""The container environment's take on the snapshots' changes, its timing line, a whole stage."""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from container_support import (
    Dataset,
    container_dataset,
    push_main,
    sync_makefile,
    timing_lines,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.containers import ContainerRuns
from factory.application.snapshots import Snapshots
from factory.application.stage_environment import ContainerEnvironment
from factory.application.take import TakeReport
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.containers import ContainerLaunch, ContainerResult, Mount
from factory.domain.git import ChangedPath
from git_support import install_agents, write_files
from human_clone import HumanClone
from stage_run_support import branch_head, completed, open_story, pushed, run_stage, stage_makefile
from undo_support import BRANCH, GUIDE, GUIDE_TEXT, PATH, start_stage

FIVE_MINUTES = timedelta(minutes=5)
AGENT_TEXT = "written by the agent\n"
NEW = "src/new.py"
INSIDE = "tests/test_a.py"
NOTES = "notes.md"


def _started(boundaries: Boundaries, human: HumanClone, agent_home: Path) -> StageStart:
    push_main(boundaries, human, {"Makefile": sync_makefile(), ".gitignore": ".venv/\n"})
    install_agents(agent_home, ["tester"])
    return start_stage(boundaries, human, write_paths=["src/*", "{work_item}"])


def test_take_copies_the_snapshots_changes_the_role_may_write(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, tmp_path: Path
) -> None:
    start = _started(boundaries, human, agent_home)
    dataset = container_dataset(boundaries, tmp_path)
    environment = ContainerEnvironment(dataset.boundaries, dataset.snapshots, dataset.containers)
    environment.prepare(start.commit, BRANCH, sync_time_limit=FIVE_MINUTES)
    checkout = dataset.workspace / "checkout"
    write_files(checkout, {NEW: AGENT_TEXT, GUIDE: AGENT_TEXT, ".venv/bin/x": AGENT_TEXT})
    write_files(dataset.workspace / "home", {".claude.json": "{}\n"})

    report = environment.take(start, PATH)

    assert (boundaries.checkout / NEW).read_bytes() == AGENT_TEXT.encode("utf-8")
    assert (boundaries.checkout / GUIDE).read_text(encoding="utf-8") == GUIDE_TEXT
    assert not (boundaries.checkout / ".venv").exists()
    assert not (boundaries.checkout / "home").exists()
    assert not (boundaries.checkout / ".claude.json").exists()
    assert report == TakeReport(left=[GUIDE], restored_work_item=False)


class ClockedSnapshots(Snapshots):
    """Snapshots that advance the manual clock inside `reset`, `advance` and `changed_paths`."""

    def __init__(self, delegate: Snapshots, clock: ManualClock) -> None:
        """Delegate to `delegate`, advancing `clock`."""
        self._delegate = delegate
        self._clock = clock

    @property
    def mount_point(self) -> Path:
        """The delegate's mount point."""
        return self._delegate.mount_point

    def reset(self) -> None:
        """Advance 0.4 s, then reset."""
        self._clock.advance(timedelta(seconds=0.4))
        self._delegate.reset()

    def advance(self) -> None:
        """Advance 0.1 s, then move the base."""
        self._clock.advance(timedelta(seconds=0.1))
        self._delegate.advance()

    def changed_paths(self) -> list[ChangedPath]:
        """Advance 0.25 s, then compare."""
        self._clock.advance(timedelta(seconds=0.25))
        return self._delegate.changed_paths()


class ClockedContainerRuns(ContainerRuns):
    """Container runs that advance the manual clock by 12.3 s inside each run."""

    def __init__(self, delegate: ContainerRuns, clock: ManualClock) -> None:
        """Delegate to `delegate`, advancing `clock`."""
        self._delegate = delegate
        self._clock = clock

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
        """Advance 12.3 s, then run on the delegate."""
        self._clock.advance(timedelta(seconds=12.3))
        return self._delegate.run(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )


def _clocked(dataset: Dataset, clock: ManualClock) -> ContainerEnvironment:
    return ContainerEnvironment(
        dataset.boundaries,
        ClockedSnapshots(dataset.snapshots, clock),
        ClockedContainerRuns(dataset.containers, clock),
    )


@pytest.mark.parametrize(
    ("prepares", "takes", "expected"),
    [
        pytest.param(
            True,
            True,
            "stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s",
            id="prepare-and-take",
        ),
        pytest.param(
            False,
            True,
            "stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s",
            id="take-without-prepare",
        ),
        pytest.param(True, False, None, id="prepare-alone"),
    ],
)
def test_one_timing_line_per_take_carries_the_last_prepares_durations(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    clock: ManualClock,
    *,
    prepares: bool,
    takes: bool,
    expected: str | None,
) -> None:
    start = _started(boundaries, human, agent_home)
    dataset = container_dataset(boundaries, tmp_path)
    if prepares:
        environment = _clocked(dataset, clock)
        environment.prepare(start.commit, BRANCH, sync_time_limit=FIVE_MINUTES)
    else:
        environment = ContainerEnvironment(
            dataset.boundaries, dataset.snapshots, dataset.containers
        )

    if takes:
        environment.take(start, PATH)

    lines = timing_lines(boundaries)
    if expected is None:
        assert lines == []
    else:
        [line] = lines
        assert line.endswith(expected)


class WorkspaceRuntime(AgentRuntime):
    """Writes the agent's files into the dataset's checkout, then lets the delegate play."""

    def __init__(self, delegate: FakeAgentRuntime, checkout: Path) -> None:
        """Write into `checkout`, then run on `delegate`."""
        self._delegate = delegate
        self._checkout = checkout

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Write `tests/test_a.py` and `notes.md` into the dataset's checkout, then delegate."""
        write_files(self._checkout, {INSIDE: AGENT_TEXT, NOTES: AGENT_TEXT})
        return self._delegate.run(request)

    def version(self) -> str:
        """The delegate's version."""
        return self._delegate.version()


def test_a_whole_stage_takes_the_agents_work_from_the_dataset(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    tmp_path: Path,
) -> None:
    makefile = stage_makefile() + "\nsync:\n\t@echo synced > .synced\n"
    open_story(
        boundaries, human, agent_home, makefile=makefile, main_files={".gitignore": ".synced\n"}
    )
    dataset = container_dataset(boundaries, tmp_path)
    agent_runtime.queue(ScriptedRun(result=completed("doing")))
    runtime = WorkspaceRuntime(agent_runtime, dataset.workspace / "checkout")

    report = run_stage(replace(dataset.boundaries, agent_runtime=runtime))

    assert report.commit == branch_head(remote)
    assert boundaries.git.show_file(report.commit, INSIDE) == AGENT_TEXT
    assert boundaries.git.show_file(report.commit, NOTES) is None
    journal = pushed(boundaries, remote).body.split("## Journal", 1)[1]
    assert NOTES in journal
    assert len(timing_lines(boundaries)) == 1
    assert boundaries.git.status().changes == []
