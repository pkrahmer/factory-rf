"""A look from outside the tick judges an own claim by its lease, like any other claim."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.domain.lease import ClaimStatus, observed_claim_status
from factory.domain.work_item import Claim
from stage_run_support import INSTANCE

OTHER_INSTANCE = "factory-2"
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


def _claim(instance: str, age: timedelta) -> Claim:
    return Claim(instance=instance, stage="intake", started_at=NOW - age, lease_duration=60)


@pytest.mark.parametrize(
    ("claim", "status"),
    [
        pytest.param(None, "none", id="no-claim"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=-5)), "held", id="own-negative-age"),
        pytest.param(_claim(INSTANCE, timedelta(0)), "held", id="own-at-start"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=59)), "held", id="own-59m"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=59, seconds=59)), "held", id="own-59m59s"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=60)), "own", id="own-at-lease"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=60, seconds=1)), "own", id="own-60m1s"),
        pytest.param(_claim(INSTANCE, timedelta(minutes=120)), "own", id="own-120m"),
        pytest.param(_claim(OTHER_INSTANCE, timedelta(minutes=59)), "held", id="other-59m"),
        pytest.param(_claim(OTHER_INSTANCE, timedelta(minutes=60)), "expired", id="other-at-lease"),
    ],
)
def test_an_observed_claim_is_judged_by_its_lease(claim: Claim | None, status: ClaimStatus) -> None:
    assert observed_claim_status(claim, instance=INSTANCE, now=NOW) == status
