"""The fault-injection paths: each behaviour path walked with one kill or one stall added."""

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.domain.identifiers import WorkItemId
from factory.domain.kill_points import InjectedKill, KillPoint
from factory.domain.story_form import check_story_form
from git_support import STORY_FORM
from proof_support import (
    STORY,
    World,
    branch_cost_records,
    completed,
    died,
    drive_to,
    head_journal,
    head_state,
    leak_writes,
    posts,
    repeated_posts,
    rerun,
    run_ticks,
    tick_until_killed,
    timed_out,
)

TITLE_QUESTION = "Which format does the title take?"
LIMITS_QUESTION = "Which of the two limits is meant?"
ORDER_QUESTION = "Test and interface disagree on the order. Which wins?"


def test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once(
    world: World, work_item: WorkItemId
) -> None:
    world.kill_points.arm(KillPoint.AGENT_RUN)
    leaked = leak_writes(world, work_item)
    world.agent_runtime.queue(completed("question", TITLE_QUESTION, writes=leaked, kill=True))
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("question", TITLE_QUESTION))
    run_ticks(restarted, 3)

    questions = posts(restarted, work_item, "question")
    state = head_state(restarted, work_item)
    assert len(questions) == 1
    assert TITLE_QUESTION in questions[0].body
    assert (state.stage, state.blocked, state.attempts, state.crashes) == (
        "intake",
        "question",
        0,
        1,
    )
    assert repeated_posts(restarted) == []


def _without_first_expect(text: str) -> str:
    lines = text.split("\n")
    smoke = lines.index("## Smoke test")
    fences = [i for i in range(smoke, len(lines)) if lines[i].startswith("```")]
    expect = fences[1] + 1
    assert lines[expect].startswith("Expect:")
    lines[expect] = ""
    return "\n".join(lines)


@pytest.mark.parametrize(("expect_kept", "found"), [(True, False), (False, True)])
def test_a_smoke_test_without_expect_is_caught_by_the_story_form(
    *, expect_kept: bool, found: bool
) -> None:
    text = STORY.format(title="Example")
    if not expect_kept:
        text = _without_first_expect(text)
    document = FrontmatterWorkItemReader().parse_specification(text)

    findings = check_story_form(document, STORY_FORM, folder="backlog")

    assert bool(findings) == found


def test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once(
    world: World, work_item: WorkItemId
) -> None:
    world.kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    leaked = leak_writes(world, work_item)
    world.agent_runtime.queue(completed("question", LIMITS_QUESTION, writes=leaked))
    with pytest.raises(InjectedKill):
        world.tick.run()
    unpushed = world.boundaries.git.resolve("HEAD")
    assert unpushed is not None
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("question", LIMITS_QUESTION))
    run_ticks(restarted, 3)

    git = restarted.boundaries.git
    git.fetch()
    reached = [
        branch.name
        for branch in git.remote_branches()
        if git.is_ancestor(unpushed, f"origin/{branch.name}")
    ]
    state = head_state(restarted, work_item)
    kinds = [record.kind for record in state.journal]
    assert reached == []
    assert kinds.count("question") == 1
    assert len(posts(restarted, work_item, "question")) == 1
    assert (state.crashes, state.attempts) == (1, 0)


def test_tester_question_killed_between_post_and_record_posts_once(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "tests")
    world.kill_points.arm(KillPoint.AFTER_POST)
    world.agent_runtime.queue(completed("question", ORDER_QUESTION))
    assert tick_until_killed(world) == KillPoint.AFTER_POST
    restarted = rerun(world)
    run_ticks(restarted, 3)

    state = head_state(restarted, work_item)
    assert len(posts(restarted, work_item, "question")) == 1
    assert (state.stage, state.blocked) == ("tests", "question")
    assert restarted.agent_runtime.requests() == []
    assert repeated_posts(restarted) == []


def test_review_rework_after_reviewer_run_dies_charges_one_attempt_then_one_round(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "review")
    world.agent_runtime.queue(died())
    world.agent_runtime.queue(completed("doing", "Finding 1: the empty list has no test."))

    world.tick.run()
    stalled = head_state(world, work_item)
    world.tick.run()
    reworked = head_state(world, work_item)

    assert (stalled.attempts, stalled.stage, stalled.journal[-1].kind) == (1, "review", "stall")
    assert (reworked.stage, reworked.round, reworked.crashes) == ("doing", 1, 0)


def test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "docs")
    world.kill_points.arm(KillPoint.AFTER_PUSH, after=1)
    world.agent_runtime.queue(completed("doing", "Finding: the README example fails."))
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("review", "Fixed."))
    restarted.tick.run()

    state = head_state(restarted, work_item)
    documenter_results = [
        record
        for record in head_journal(restarted, work_item)
        if (record.speaker, record.kind) == ("documenter", "result")
    ]
    assert (state.round, state.crashes) == (1, 0)
    assert len(documenter_results) == 1
    assert len(restarted.agent_runtime.requests()) == 1


def test_smoke_test_finding_after_run_reaches_time_limit_charges_one_attempt_then_moves_back(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "smoke-test")
    world.agent_runtime.queue(timed_out())
    world.agent_runtime.queue(completed("doing", "Expect not met: the title is not stripped."))

    world.tick.run()
    stalled = head_state(world, work_item)
    timed = [
        record
        for record in branch_cost_records(world, work_item)
        if record.end_reason == "time_limit" and record.cost_usd is None
    ]
    world.tick.run()
    moved = head_state(world, work_item)

    assert (stalled.attempts, stalled.stage) == (1, "smoke-test")
    assert timed != []
    assert (moved.stage, moved.round) == ("doing", 1)
