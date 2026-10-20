"""The expiry note is posted under the key of the expiry record, also at the crash cap."""

import pytest

from crash_support import (
    Rerun,
    expired_claim,
    expired_event,
    open_pull_request,
    other_handler,
    snapshot,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.hosting import PostKey
from human_clone import HumanClone

EXPIRY_KEY = PostKey(work_item="F0001-S0001", kind="expiry", n="3")
CRASH_CAP_KEY = PostKey(work_item="F0001-S0001", kind="crash_cap", n="4")


@pytest.mark.parametrize(
    ("crashes", "keys"),
    [(1, [EXPIRY_KEY, CRASH_CAP_KEY]), (0, [EXPIRY_KEY])],
    ids=["at-the-cap", "below-the-cap"],
)
def test_the_expiry_note_is_keyed_by_the_expiry_record(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    hosting: FakeHostingService,
    crashes: int,
    keys: list[PostKey],
) -> None:
    number = open_pull_request(hosting)
    claimed = expired_claim(boundaries, human, clock, crashes=crashes, pull_request=number)

    other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))

    assert [post.key for post in hosting.factory_posts(number)] == keys
