"""A hosting failure after a stage's claim, before any agent ran, and the tick after it."""

import pytest

from factory.domain.identifiers import WorkItemId
from proof_support import World, branch_state, head_state, run_ticks


@pytest.mark.xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")
def test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick(
    world: World, work_item: WorkItemId
) -> None:
    world.hosting.fail_next("create_pull_request")

    run_ticks(world)

    claimed = branch_state(world, work_item)
    assert claimed is not None
    assert claimed.claim is not None
    assert world.agent_runtime.requests() == []

    run_ticks(world)

    after = head_state(world, work_item)
    assert ("factory", "crash") not in [(record.speaker, record.kind) for record in after.journal]
    assert after.crashes == 0
