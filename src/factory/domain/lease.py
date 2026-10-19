"""The lease clock: the age of a claim, its expiry and the status it gives an instance."""

from datetime import datetime, timedelta
from typing import Literal

from factory.domain.work_item import Claim

ClaimStatus = Literal["none", "own", "held", "expired"]


def lease_age(claim: Claim, now: datetime) -> timedelta:
    """How long ago the claim's stage started; negative when `now` is before the start."""
    return now - claim.started_at


def lease_expired(claim: Claim, now: datetime) -> bool:
    """Whether the claim's own lease has run out at `now`; a negative age never has."""
    return lease_age(claim, now) >= timedelta(minutes=claim.lease_duration)


def claim_status(claim: Claim | None, *, instance: str, now: datetime) -> ClaimStatus:
    """The status of `claim` as `instance` sees it at `now`.

    An own claim is "own" whatever its age, so a restart under the same name reruns at once.
    """
    if claim is None:
        return "none"
    if claim.instance == instance:
        return "own"
    if lease_expired(claim, now):
        return "expired"
    return "held"


def observed_claim_status(claim: Claim | None, *, instance: str, now: datetime) -> ClaimStatus:
    """The status of `claim` as a look from outside `instance`'s tick sees it at `now`.

    An own claim within its lease is "held", since the tick may be running its stage; at and
    past its lease it is "own". Every other claim has its `claim_status`.
    """
    if claim is not None and claim.instance == instance and not lease_expired(claim, now):
        return "held"
    return claim_status(claim, instance=instance, now=now)
