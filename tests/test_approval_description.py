"""A move to an approval writes the pull request's description before the push that shows it."""

from collections.abc import Sequence

import pytest

from factory.domain.git import CommitInfo
from factory.domain.hand_over import HAND_OVER_CLOSING, hand_over_description
from factory.domain.identifiers import WorkItemId, branch_name
from factory.domain.kill_points import InjectedKill, KillPoint
from factory.domain.work_item import WorkItemDocument
from proof_support import (
    World,
    completed,
    drive_to,
    head_state,
    pull_request_of,
    work_item_file,
)

SMOKE_ENTRY = "The smoke test passed."


def _pushed(world: World, work_item: WorkItemId) -> tuple[WorkItemDocument, Sequence[CommitInfo]]:
    git = world.boundaries.git
    git.fetch()
    branch = f"origin/{branch_name(work_item)}"
    text = git.show_file(branch, work_item_file(world, work_item))
    assert text is not None
    document = world.boundaries.work_item_reader.parse(text)
    return document, git.log(branch, since="origin/main")


@pytest.mark.parametrize(
    ("stage", "decision", "written"),
    [
        pytest.param("smoke-test", "approval", True, id="approval"),
        pytest.param("smoke-test", "doing", False, id="rework"),
        pytest.param("review", "docs", False, id="forward"),
        pytest.param("smoke-test", "question", False, id="question"),
    ],
)
def test_the_description_is_written_before_the_result_push_only_for_a_move_to_an_approval(
    world: World, work_item: WorkItemId, stage: str, decision: str, written: bool
) -> None:
    drive_to(world, work_item, stage)
    number = pull_request_of(world, work_item).number
    before = world.hosting.description(number)
    world.kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    world.agent_runtime.queue(completed(decision, SMOKE_ENTRY))

    with pytest.raises(InjectedKill):
        world.tick.run()

    description = world.hosting.description(number)
    assert head_state(world, work_item).stage == stage
    if written:
        assert f"## Smoke test\n\n{SMOKE_ENTRY}" in description
        assert description.endswith(HAND_OVER_CLOSING + "\n")
    else:
        assert description == before


def test_a_work_item_at_its_approval_shows_the_full_description_before_its_hand_over(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "smoke-test")
    world.agent_runtime.queue(completed("approval", SMOKE_ENTRY))
    world.tick.run()
    number = pull_request_of(world, work_item).number

    state = head_state(world, work_item)
    document, commits = _pushed(world, work_item)
    assert state.stage == "approval"
    assert state.handed_over is None
    assert pull_request_of(world, work_item).draft
    assert world.hosting.description(number) == hand_over_description(document, commits)
    described = world.hosting.description(number)

    world.tick.run()

    assert head_state(world, work_item).handed_over == "approval"
    assert not pull_request_of(world, work_item).draft
    assert world.hosting.description(number) == described


def test_a_failing_description_write_before_the_push_is_logged_and_the_hand_over_writes_it(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "smoke-test")
    number = pull_request_of(world, work_item).number
    before = world.hosting.description(number)
    world.hosting.fail_next("set_description")
    world.agent_runtime.queue(completed("approval", SMOKE_ENTRY))
    world.tick.run()

    state = head_state(world, work_item)
    log = (world.state / "factory.log").read_text(encoding="utf-8")
    assert state.stage == "approval"
    assert state.handed_over is None
    assert world.hosting.description(number) == before
    assert f"pull request #{number}: description not written before the push" in log
    document, commits = _pushed(world, work_item)

    world.tick.run()

    assert head_state(world, work_item).handed_over == "approval"
    assert world.hosting.description(number) == hand_over_description(document, commits)
