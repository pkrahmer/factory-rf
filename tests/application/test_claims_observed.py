"""The claim service judges a claim from outside its tick by the lease, beside its own view."""

from datetime import timedelta

import pytest

from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from factory.application.claims import ClaimService
from factory.domain.lease import ClaimStatus
from factory.domain.work_item import Claim, WorkItemState
from git_support import PIPELINE_YAML
from stage_run_support import INSTANCE

OTHER_INSTANCE = "factory-2"


@pytest.mark.parametrize(
    ("claimant", "age", "observed", "status"),
    [
        pytest.param(INSTANCE, 59, "held", "own", id="own-within-lease"),
        pytest.param(INSTANCE, 60, "own", "own", id="own-at-lease"),
        pytest.param(OTHER_INSTANCE, 59, "held", "held", id="other-within-lease"),
        pytest.param(OTHER_INSTANCE, 60, "expired", "expired", id="other-at-lease"),
        pytest.param(None, 0, "none", "none", id="no-claim"),
    ],
)
def test_the_observed_status_judges_an_own_claim_by_its_lease(
    boundaries: Boundaries,
    clock: ManualClock,
    *,
    claimant: str | None,
    age: int,
    observed: ClaimStatus,
    status: ClaimStatus,
) -> None:
    claim = (
        None
        if claimant is None
        else Claim(
            instance=claimant,
            stage="intake",
            started_at=clock.now() - timedelta(minutes=age),
            lease_duration=60,
        )
    )
    state = WorkItemState(stage="intake", claim=claim)
    service = ClaimService(boundaries, INSTANCE, boundaries.pipeline_reader.parse(PIPELINE_YAML))

    assert (service.observed_status(state), service.status(state)) == (observed, status)
