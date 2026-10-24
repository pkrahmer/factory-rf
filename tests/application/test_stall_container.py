"""A stall under the container environment takes from the dataset, with one timing line."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from container_support import (
    FIRST,
    FIVE_MINUTES,
    Pace,
    WorkspaceRuntime,
    clocked_environment,
    container_dataset,
    started_with_sync,
    timing_lines,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.take import TakeReport
from factory.domain.agent_runs import AgentRunResult
from git_support import write_files
from human_clone import HumanClone
from stage_run_support import (
    INSIDE,
    NOTES,
    branch_head,
    completed,
    open_story,
    run_stage,
    stage_makefile,
)
from stall_support import DIED
from take_support import AGENT_TEXT
from undo_support import BRANCH, GUIDE, PATH

LATER = "src/c.py"
SYNC_TARGET = "\nsync:\n\t@echo synced\n"
BLANK_ENTRY = AgentRunResult(
    end_reason="completed", decision="doing", entry="tester: ", duration=timedelta(minutes=1)
)


def test_a_stall_before_the_take_takes_the_agents_writes_from_the_dataset(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    tmp_path: Path,
) -> None:
    open_story(boundaries, human, agent_home, makefile=stage_makefile() + SYNC_TARGET)
    dataset = container_dataset(boundaries, tmp_path)
    agent_runtime.queue(ScriptedRun(result=DIED))
    runtime = WorkspaceRuntime(
        agent_runtime, dataset.workspace / "checkout", {INSIDE: AGENT_TEXT, NOTES: AGENT_TEXT}
    )

    report = run_stage(replace(dataset.boundaries, agent_runtime=runtime))

    head = branch_head(remote)
    assert boundaries.git.show_file(head, INSIDE) == AGENT_TEXT
    assert boundaries.git.show_file(head, NOTES) is None
    assert report.stall is not None
    assert report.stall.take == TakeReport(left=[NOTES], restored_work_item=False)
    assert len(timing_lines(boundaries)) == 1
    assert boundaries.git.status().changes == []


@pytest.mark.parametrize(
    ("makefile", "result", "reason"),
    [
        pytest.param(stage_makefile({"lint": 1}), completed("doing"), "check_red", id="red-check"),
        pytest.param(stage_makefile(), BLANK_ENTRY, "no_result", id="blank-entry"),
    ],
)
def test_a_stall_after_the_take_takes_again_and_writes_no_second_timing_line(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    tmp_path: Path,
    makefile: str,
    result: AgentRunResult,
    reason: str,
) -> None:
    open_story(boundaries, human, agent_home, makefile=makefile + SYNC_TARGET)
    dataset = container_dataset(boundaries, tmp_path)
    agent_runtime.queue(ScriptedRun(result=result))
    runtime = WorkspaceRuntime(agent_runtime, dataset.workspace / "checkout", {INSIDE: AGENT_TEXT})

    report = run_stage(replace(dataset.boundaries, agent_runtime=runtime))

    assert report.stall is not None
    assert report.stall.reason == reason
    assert boundaries.git.show_file(branch_head(remote), INSIDE) == AGENT_TEXT
    assert report.stall.take == TakeReport(left=[], restored_work_item=False)
    assert len(timing_lines(boundaries)) == 1


@pytest.mark.parametrize(
    ("steps", "same_report", "endings"),
    [
        pytest.param(
            ("prepare", "take", "take"),
            True,
            ["stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s"],
            id="two-takes-after-one-prepare",
        ),
        pytest.param(
            ("prepare", "take", "prepare", "take"),
            False,
            [
                "stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s",
                "stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.5 s",
            ],
            id="a-prepare-between-the-takes",
        ),
        pytest.param(
            ("take", "take"),
            True,
            ["stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.2 s"],
            id="two-takes-without-a-prepare",
        ),
    ],
)
def test_the_first_take_after_a_prepare_writes_the_timing_line_and_a_second_none(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    clock: ManualClock,
    *,
    steps: tuple[str, ...],
    same_report: bool,
    endings: list[str],
) -> None:
    start = started_with_sync(boundaries, human, agent_home)
    dataset = container_dataset(boundaries, tmp_path)
    pace = Pace(steps=FIRST)
    environment = clocked_environment(dataset, clock, pace)
    reports: list[TakeReport] = []

    for step in steps:
        if step == "prepare":
            environment.prepare(start.commit, BRANCH, sync_time_limit=FIVE_MINUTES)
            write_files(dataset.workspace / "checkout", {GUIDE: AGENT_TEXT})
        else:
            reports.append(environment.take(start, PATH))
            pace.take = 0.5

    lines = timing_lines(boundaries)
    assert len(lines) == len(endings)
    for line, ending in zip(lines, endings, strict=True):
        assert line.endswith(ending)
    if same_report:
        assert reports[1] == reports[0]


def test_a_second_take_takes_what_the_dataset_gained_since_the_first(
    boundaries: Boundaries,
    human: HumanClone,
    agent_home: Path,
    tmp_path: Path,
    clock: ManualClock,
) -> None:
    start = started_with_sync(boundaries, human, agent_home)
    dataset = container_dataset(boundaries, tmp_path)
    environment = clocked_environment(dataset, clock, Pace(steps=FIRST))
    taken = boundaries.checkout / LATER

    environment.prepare(start.commit, BRANCH, sync_time_limit=FIVE_MINUTES)
    first = environment.take(start, PATH)
    taken_after_first = taken.exists()
    write_files(dataset.workspace / "checkout", {LATER: AGENT_TEXT, NOTES: AGENT_TEXT})
    second = environment.take(start, PATH)

    assert not taken_after_first
    assert taken.read_text(encoding="utf-8") == AGENT_TEXT
    assert NOTES not in first.left
    assert NOTES in second.left
    assert len(timing_lines(boundaries)) == 1
