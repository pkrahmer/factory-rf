"""A hosting failure after a stage's claim, before any agent ran, and the tick after it."""

import pytest

from factory.domain.identifiers import WorkItemId
from proof_support import World, branch_state, head_state, run_ticks


@pytest.fixture
def failed_after_claim(world: World, work_item: WorkItemId) -> World:
    """A world whose first tick claimed the work item and then met a hosting failure."""
    del work_item  # requested only so that the story exists before the tick
    world.hosting.fail_next("create_pull_request")
    run_ticks(world)
    return world


def test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run(
    failed_after_claim: World, work_item: WorkItemId
) -> None:
    claimed = branch_state(failed_after_claim, work_item)
    assert claimed is not None
    assert claimed.claim is not None
    assert failed_after_claim.agent_runtime.requests() == []


def test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick(
    failed_after_claim: World, work_item: WorkItemId
) -> None:
    run_ticks(failed_after_claim)

    after = head_state(failed_after_claim, work_item)
    assert ("factory", "crash") not in [(record.speaker, record.kind) for record in after.journal]
    assert after.crashes == 0
