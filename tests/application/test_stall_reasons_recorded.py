"""A stall records its reason on its journal record."""

import typing
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.opening import WorkItemOpening
from factory.application.stalls import StallContext, StallService
from factory.domain.decisions import StallReason
from factory.domain.work_item import WorkItemState
from git_support import PIPELINE_YAML
from human_clone import HumanClone
from stage_run_support import (
    BRANCH,
    CREATED,
    INSTANCE,
    NOTES,
    PATH,
    WORK_ITEM,
    completed,
    open_story,
    pushed_state,
    run_stage,
    stage_makefile,
)


@pytest.mark.parametrize("reason", typing.get_args(StallReason))
def test_a_stall_records_its_reason(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    remote: Path,
    reason: StallReason,
) -> None:
    open_story(boundaries, human, agent_home)
    definition = boundaries.pipeline_reader.parse(PIPELINE_YAML)
    prepared = WorkItemOpening(boundaries, definition).prepare(WORK_ITEM, PATH)
    context = StallContext(
        work_item=WORK_ITEM,
        stage="tests",
        branch=prepared.branch,
        path=PATH,
        stage_start=None,
        document=prepared.document,
    )

    StallService(boundaries, INSTANCE, definition).stall(context, reason, "")

    last = pushed_state(boundaries, remote).journal[-1]
    assert (last.kind, last.reason) == ("stall", reason)


@pytest.mark.parametrize(
    ("conflict", "reason"),
    [(False, "check_red"), (True, "merge_conflict")],
    ids=["red-check", "merge-conflict"],
)
def test_a_stage_run_that_stalls_records_the_reason(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
    conflict: bool,
    reason: StallReason,
) -> None:
    state = WorkItemState(stage="doing", journal=[CREATED])
    makefile = stage_makefile({"check": 1})
    files = {NOTES: "base\n"}
    open_story(
        boundaries,
        human,
        agent_home,
        makefile=makefile,
        main_files=files,
        state=state,
        roles=("coder",),
    )
    if conflict:
        human.push_file(BRANCH, NOTES, "branch\n")
        human.push_file("main", NOTES, "main\n")
        boundaries.git.fetch()
    else:
        agent_runtime.queue(ScriptedRun(result=completed("review")))

    run_stage(boundaries)

    last = pushed_state(boundaries, remote).journal[-1]
    assert (last.kind, last.reason) == ("stall", reason)
