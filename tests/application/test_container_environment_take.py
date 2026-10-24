"""The container environment's take on the snapshots' changes, its timing line, a whole stage."""

from dataclasses import replace
from pathlib import Path

import pytest

from container_support import (
    FIRST,
    FIVE_MINUTES,
    SECOND,
    Pace,
    Steps,
    WorkspaceRuntime,
    clocked_environment,
    container_dataset,
    started_with_sync,
    timing_lines,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import ContainerEnvironment
from factory.application.take import TakeReport
from git_support import write_files
from human_clone import HumanClone
from stage_run_support import branch_head, completed, open_story, pushed, run_stage, stage_makefile
from undo_support import BRANCH, GUIDE, GUIDE_TEXT, PATH

AGENT_TEXT = "written by the agent\n"
NEW = "src/new.py"
INSIDE = "tests/test_a.py"
NOTES = "notes.md"


def test_take_copies_the_snapshots_changes_the_role_may_write(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, tmp_path: Path
) -> None:
    start = started_with_sync(boundaries, human, agent_home)
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


@pytest.mark.parametrize(
    ("prepares", "takes", "expected"),
    [
        pytest.param(
            ((BRANCH, FIRST),),
            True,
            "stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s",
            id="prepare-and-take",
        ),
        pytest.param(
            (),
            True,
            "stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s",
            id="take-without-prepare",
        ),
        pytest.param(((BRANCH, FIRST),), False, None, id="prepare-alone"),
        pytest.param(
            (("main", FIRST), (BRANCH, SECOND)),
            True,
            "stage environment: reset 1.0 s, sync 2.0 s, advance 3.0 s, take 0.2 s",
            id="last-prepare-counts",
        ),
    ],
)
def test_one_timing_line_per_take_carries_the_last_prepares_durations(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    clock: ManualClock,
    *,
    prepares: tuple[tuple[str, Steps], ...],
    takes: bool,
    expected: str | None,
) -> None:
    start = started_with_sync(boundaries, human, agent_home)
    main = boundaries.git.resolve("main")
    assert main is not None
    commits = {"main": main, BRANCH: start.commit}
    dataset = container_dataset(boundaries, tmp_path)
    if prepares:
        pace = Pace(steps=prepares[0][1])
        environment = clocked_environment(dataset, clock, pace)
        for branch, steps in prepares:
            pace.steps = steps
            environment.prepare(commits[branch], branch, sync_time_limit=FIVE_MINUTES)
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
    runtime = WorkspaceRuntime(
        agent_runtime, dataset.workspace / "checkout", {INSIDE: AGENT_TEXT, NOTES: AGENT_TEXT}
    )

    report = run_stage(replace(dataset.boundaries, agent_runtime=runtime))

    assert report.commit == branch_head(remote)
    assert boundaries.git.show_file(report.commit, INSIDE) == AGENT_TEXT
    assert boundaries.git.show_file(report.commit, NOTES) is None
    journal = pushed(boundaries, remote).body.split("## Journal", 1)[1]
    assert NOTES in journal
    assert len(timing_lines(boundaries)) == 1
    assert boundaries.git.status().changes == []
