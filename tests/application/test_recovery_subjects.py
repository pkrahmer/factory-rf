"""The subjects of the commits the recovery records on the work item's branch."""

from collections.abc import Callable

import pytest

from crash_support import (
    BRANCH,
    Claimed,
    Rerun,
    claim,
    crash_event,
    expired_claim,
    expired_event,
    handler,
    open_pull_request,
    other_handler,
    snapshot,
)
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from human_clone import HumanClone

Recover = Callable[[Boundaries, HumanClone, ManualClock, FakeHostingService], Claimed]


def _crash(
    boundaries: Boundaries, human: HumanClone, _clock: ManualClock, hosting: FakeHostingService
) -> Claimed:
    claimed = claim(boundaries, human, crashes=0, pull_request=open_pull_request(hosting))
    handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))
    return claimed


def _expiry(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, hosting: FakeHostingService
) -> Claimed:
    claimed = expired_claim(boundaries, human, clock, pull_request=open_pull_request(hosting))
    other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))
    return claimed


def _expiry_without_pull_request(
    boundaries: Boundaries, human: HumanClone, clock: ManualClock, _hosting: FakeHostingService
) -> Claimed:
    claimed = expired_claim(boundaries, human, clock)
    other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))
    return claimed


@pytest.mark.parametrize(
    ("recover", "subjects"),
    [
        pytest.param(_crash, ["work item F0001-S0001: crash of stage doing recorded"], id="crash"),
        pytest.param(
            _expiry, ["work item F0001-S0001: expiry of stage doing recorded"], id="expiry"
        ),
        pytest.param(
            _expiry_without_pull_request,
            [
                "work item F0001-S0001: pull request opened",
                "work item F0001-S0001: expiry of stage doing recorded",
            ],
            id="expiry-opening-a-pull-request",
        ),
    ],
)
def test_the_recovery_commits_name_the_work_item_and_what_it_recorded(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    clock: ManualClock,
    hosting: FakeHostingService,
    recover: Recover,
    subjects: list[str],
) -> None:
    claimed = recover(boundaries, human, clock, hosting)

    boundaries.git.fetch()
    commits = boundaries.git.log(f"origin/{BRANCH}", since=claimed.start.commit)
    assert [commit.subject for commit in commits] == subjects
