"""A human's answer to the round cap question starts the count of rounds over."""

from factory.domain.identifiers import WorkItemId
from proof_support import (
    World,
    completed,
    drive_to,
    head_state,
    posts,
    pull_request_of,
)


def test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over(
    world: World, work_item: WorkItemId
) -> None:
    drive_to(world, work_item, "review")
    for _ in range(3):
        world.agent_runtime.queue(completed("doing", "Finding."))
        world.tick.run()
        world.agent_runtime.queue(completed("review", "Fixed."))
        world.tick.run()
    world.agent_runtime.queue(completed("doing", "Finding."))
    world.tick.run()
    capped = head_state(world, work_item)
    caps_asked = posts(world, work_item, "round_cap")

    world.hosting.add_human_comment(pull_request_of(world, work_item).number, "Go on.")
    world.tick.run()
    answered = head_state(world, work_item)
    world.agent_runtime.queue(completed("doing", "Finding."))
    world.tick.run()
    sent_back = head_state(world, work_item)

    assert capped.stage == "review"
    assert capped.blocked == "round_cap"
    assert capped.round == 4
    assert len(caps_asked) == 1
    assert answered.blocked is None
    assert answered.round == 0
    assert sent_back.stage == "doing"
    assert sent_back.round == 1
    assert len(posts(world, work_item, "round_cap")) == 1
