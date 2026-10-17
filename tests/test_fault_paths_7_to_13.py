"""The fault-injection paths 7 to 13: each behaviour path walked with one kill or one stall."""

from pathlib import Path
from typing import Literal

import pytest

from factory.domain.acceptance import AcceptanceState
from factory.domain.identifiers import WorkItemId, branch_name
from factory.domain.kill_points import InjectedKill, KillPoint
from factory.domain.work_item import WorkItemState
from git_support import remote_commit
from proof_support import (
    FEATURE,
    LEAK_PATH,
    World,
    completed,
    died,
    drive_to,
    head_journal,
    head_state,
    leak_writes,
    markers_in_history,
    posts,
    pull_request_of,
    repeated_posts,
    rerun,
    run_ticks,
    start_story,
    tick_until_killed,
    work_item_file,
)

TITLE_QUESTION = "Which format does the title take?"
ACCEPTANCE = "F0001-A0001"
RECOMMENDATION = "Recommendation: accepted."
ACCEPTANCE_TICKS = 6
STAGE_TICKS = 4


def _number(world: World, work_item: WorkItemId) -> int:
    return pull_request_of(world, work_item).number


def _merge_main(world: World, work_item: WorkItemId) -> None:
    world.human.merge(branch_name(work_item), "merge")
    main = remote_commit(world.remote, "main")
    assert main is not None
    world.hosting.merge_by_human(_number(world, work_item), main)


def _branch_state(world: World, work_item: WorkItemId) -> WorkItemState | None:
    git = world.boundaries.git
    git.fetch()
    branch = f"origin/{branch_name(work_item)}"
    if git.resolve(branch) is None:
        return None
    text = git.show_file(branch, work_item_file(world, work_item))
    assert text is not None
    return world.boundaries.work_item_reader.parse(text).state


def test_round_cap_question_killed_between_post_and_record_posts_once_and_waits(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "review")
    world.kill_points.arm(KillPoint.AFTER_POST)
    for _ in range(3):
        world.agent_runtime.queue(completed("doing", "Finding."))
        world.tick.run()
        world.agent_runtime.queue(completed("review", "Fixed."))
        world.tick.run()
    third = head_state(world, work_item)
    caps_before = posts(world, work_item, "round_cap")
    world.agent_runtime.queue(completed("doing", "Finding."))
    point = tick_until_killed(world, limit=6)
    restarted = rerun(world)
    run_ticks(restarted, 3)

    state = head_state(restarted, work_item)
    assert third.round == 3
    assert caps_before == []
    assert point == KillPoint.AFTER_POST
    assert len(posts(restarted, work_item, "round_cap")) == 1
    assert state.blocked == "round_cap"
    assert restarted.agent_runtime.requests() == []


def test_attempts_cap_run_stalls_twice_asks_human_without_a_rerun_and_reruns_on_comment(
    world: World, work_item: WorkItemId
) -> None:
    world.agent_runtime.queue(died())
    world.agent_runtime.queue(died())

    world.tick.run()
    first = head_state(world, work_item)
    first_stalls = posts(world, work_item, "stall")
    world.tick.run()
    second = head_state(world, work_item)
    second_stalls = posts(world, work_item, "stall")[len(first_stalls) :]
    caps_after_second = posts(world, work_item, "attempts_cap")
    world.tick.run()
    asked = head_state(world, work_item)
    caps_after_third = posts(world, work_item, "attempts_cap")
    requests_waiting = len(world.agent_runtime.requests())
    posts_waiting = len(posts(world, work_item))
    run_ticks(world, 2)
    requests_waited = len(world.agent_runtime.requests())
    posts_waited = len(posts(world, work_item))
    world.hosting.add_human_comment(_number(world, work_item), "Retry.")
    world.agent_runtime.queue(completed("question", TITLE_QUESTION))
    run_ticks(world, 3)
    retried = head_state(world, work_item)

    assert first.attempts == 1
    assert len(first_stalls) == 1
    assert "retrying" in first_stalls[0].body.lower()
    assert second.attempts == 2
    assert len(second_stalls) == 1
    assert "retrying" not in second_stalls[0].body.lower()
    assert caps_after_second == []
    assert asked.blocked == "attempts_cap"
    assert len(caps_after_third) == 1
    assert (requests_waited, posts_waited) == (requests_waiting, posts_waiting)
    assert retried.attempts == 0
    assert len(world.agent_runtime.requests()) == 3


def _moved_by_hand(world: World, work_item: WorkItemId, stage: str) -> None:
    git = world.boundaries.git
    branch = branch_name(work_item)
    path = work_item_file(world, work_item)
    text = git.show_file(f"origin/{branch}", path)
    assert text is not None
    document = world.boundaries.work_item_reader.parse(text)
    assert document.state is not None
    moved = document.model_copy(
        update={"state": document.state.model_copy(update={"stage": stage})}
    )
    world.human.push_file(branch, path, world.boundaries.work_item_writer.render(moved))


def test_reject_killed_before_push_reverts_once_and_leaves_main_clean(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "tests")
    main_before = world.boundaries.git.resolve("origin/main")
    _moved_by_hand(world, work_item, "review")
    world.kill_points.arm(KillPoint.BEFORE_PUSH, after=0)
    with pytest.raises(InjectedKill):
        world.tick.run()
    changes = world.boundaries.git.status().changes
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("question", "Which test?"))
    run_ticks(restarted, 3)

    kinds = [record.kind for record in head_journal(restarted, work_item)]
    git = restarted.boundaries.git
    git.fetch()
    assert kinds.count("move_back") == 1
    assert head_state(restarted, work_item).stage == "tests"
    assert len(posts(restarted, work_item, "correction")) == 1
    assert changes == []
    assert git.resolve("origin/main") == main_before


def test_two_items_in_progress_tick_killed_after_claim_push_reruns_lower_id_and_other_waits(
    world: World, work_item: WorkItemId
) -> None:
    higher = start_story(world, "Second")
    world.kill_points.arm(KillPoint.AFTER_PUSH, after=0)
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("question", TITLE_QUESTION))
    run_ticks(restarted, 3)

    state = head_state(restarted, work_item)
    git = restarted.boundaries.git
    git.fetch()
    assert work_item < higher
    assert (state.blocked, state.crashes) == ("question", 1)
    assert len(restarted.agent_runtime.requests()) == 1
    assert git.resolve(f"origin/{branch_name(higher)}") is None


def test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "approval")
    world.hosting.close_by_human(_number(world, work_item))
    world.kill_points.arm(KillPoint.AFTER_PUSH, after=0)
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world)
    run_ticks(restarted, 3)

    kinds = [record.kind for record in head_journal(restarted, work_item)]
    view = pull_request_of(restarted, work_item)
    assert kinds.count("close") == 1
    assert (view.state, view.draft) == ("open", True)
    assert len(posts(restarted, work_item, "send_back")) == 1
    assert head_state(restarted, work_item).blocked == "send_back"


def _tick_until_acceptance_opened(world: World) -> None:
    for _ in range(ACCEPTANCE_TICKS):
        world.tick.run()
        state = _branch_state(world, ACCEPTANCE)
        if state is not None and state.claim is None:
            return
    raise AssertionError(f"{ACCEPTANCE} was not opened in {ACCEPTANCE_TICKS} ticks")


def _booked(world: World) -> WorkItemState | None:
    git = world.boundaries.git
    git.fetch()
    done = git.list_files("origin/main", f"{FEATURE}/done")
    [path] = [
        path for path in done if Path(path).name.startswith(ACCEPTANCE) and path.endswith(".md")
    ]
    text = git.show_file("origin/main", path)
    assert text is not None
    return world.boundaries.work_item_reader.parse(text).state


@pytest.mark.parametrize("outcome", ["refused", "accepted"])
def test_acceptance_container_lost_in_review_reruns_once_and_books_result(
    world: World, work_item: WorkItemId, outcome: Literal["refused", "accepted"]
) -> None:
    drive_to(world, work_item, "approval")
    _merge_main(world, work_item)
    _tick_until_acceptance_opened(world)
    world.kill_points.arm(KillPoint.AGENT_RUN)
    world.agent_runtime.queue(completed("approval", RECOMMENDATION, kill=True))
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world, empty_disk=True)
    restarted.agent_runtime.queue(completed("approval", RECOMMENDATION))
    run_ticks(restarted, 3)
    requests = len(restarted.agent_runtime.requests())
    acceptance = pull_request_of(restarted, ACCEPTANCE)
    if outcome == "refused":
        restarted.hosting.close_by_human(acceptance.number)
    else:
        _merge_main(restarted, ACCEPTANCE)
    run_ticks(restarted, 3)

    booked = _booked(restarted)
    assert requests == 1
    assert not acceptance.draft
    assert isinstance(booked, AcceptanceState)
    assert booked.outcome == outcome
    assert repeated_posts(restarted) == []


def test_test_change_approved_tick_killed_during_tester_run_reruns_tests_without_round(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "doing")
    world.agent_runtime.queue(completed("question", "Test T contradicts criterion 3. Change it?"))
    run_ticks(world, 2)
    questions = posts(world, work_item, "question")
    world.hosting.add_human_comment(_number(world, work_item), "(a) the tester fixes the test.")
    world.agent_runtime.queue(completed("tests", "Change test T: expect 3, not 2."))
    for _ in range(STAGE_TICKS):
        world.tick.run()
        if head_state(world, work_item).stage == "tests":
            break
    assert head_state(world, work_item).stage == "tests"
    world.kill_points.arm(KillPoint.AGENT_RUN)
    leaked = leak_writes(world, work_item)
    world.agent_runtime.queue(completed("doing", "Changed test T.", writes=leaked, kill=True))
    with pytest.raises(InjectedKill):
        world.tick.run()
    restarted = rerun(world)
    restarted.agent_runtime.queue(completed("doing", "Changed test T."))
    restarted.tick.run()

    state = head_state(restarted, work_item)
    leaks = [
        place
        for place in markers_in_history(restarted, work_item)
        if place.endswith(f":{LEAK_PATH}")
    ]
    assert len(questions) == 1
    assert (state.stage, state.round, state.attempts) == ("doing", 0, 0)
    assert len(restarted.agent_runtime.requests()) == 1
    assert leaks == []
