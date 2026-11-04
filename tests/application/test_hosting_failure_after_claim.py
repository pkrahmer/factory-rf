"""A hosting failure after a stage's claim, before any agent ran, and the tick after it."""

from factory.domain.identifiers import WorkItemId
from proof_support import World, head_state, run_ticks


def test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick(
    failed_after_claim: World, work_item: WorkItemId
) -> None:
    run_ticks(failed_after_claim)

    after = head_state(failed_after_claim, work_item)
    assert ("factory", "crash") not in [(record.speaker, record.kind) for record in after.journal]
    assert after.crashes == 0
