"""An acceptance the human merges, at any stage, is booked accepted in one tick and never loops."""

from pathlib import Path

import pytest

from acceptance_walk import (
    FIRST,
    FIRST_RECORDS,
    SECOND,
    AcceptanceWalk,
    booked_state,
    branch_of,
    last_entry,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.bills import bill, cost_line
from factory.domain.work_item import Blocked
from git_support import remote_commit
from human_clone import HumanClone

BEFORE_APPROVAL = "done (pull request merged before approval); cost: "
AT_APPROVAL = "done (pull request merged); cost: "
CASES = [("acceptance", None), ("approval", None), ("acceptance", "question")]
CASE_IDS = ["at-acceptance", "at-approval", "asking"]


@pytest.fixture
def walk(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    hosting: FakeHostingService,
    agent_home: Path,
) -> AcceptanceWalk:
    """Return a walk over the feature `F0002-todo`, due with two archived stories."""
    return AcceptanceWalk(
        boundaries, remote=remote, human=human, hosting=hosting, agent_home=agent_home
    )


def _merged(walk: AcceptanceWalk, stage: str, blocked: Blocked | None) -> int:
    """Open the acceptance, record it at `stage`, merge it as the human; return its number."""
    number = walk.open(FIRST)
    handed_over = stage if stage == "approval" else None
    walk.record(FIRST, number, FIRST_RECORDS, stage=stage, blocked=blocked, handed_over=handed_over)
    if (stage, blocked) == ("acceptance", None):
        walk.propose(FIRST)
    walk.merge(FIRST, number)
    return number


def test_a_merge_at_the_review_stage_runs_through_the_gate_and_is_booked_before_approval(
    walk: AcceptanceWalk, *, remote: Path, agent_runtime: FakeAgentRuntime
) -> None:
    _merged(walk, "acceptance", None)

    outcome = walk.tick()

    evaluated = walk.evaluations[-1]
    assert evaluated.kind == "run"
    assert evaluated.work_item is not None
    assert evaluated.work_item.id == FIRST
    assert outcome.event is not None
    assert (outcome.event.kind, outcome.dispatch) == ("run", "handled")
    document = walk.booked(FIRST)
    assert (booked_state(document).stage, booked_state(document).outcome) == ("done", "accepted")
    assert last_entry(document) == BEFORE_APPROVAL + cost_line(bill(FIRST_RECORDS))
    assert remote_commit(remote, branch_of(FIRST)) is None
    assert agent_runtime.requests() == []


def test_a_merge_at_the_approval_is_the_merged_event_and_is_booked_accepted(
    walk: AcceptanceWalk,
) -> None:
    _merged(walk, "approval", None)

    outcome = walk.tick()

    assert walk.evaluations[-1].kind == "merged"
    assert outcome.event is not None
    assert outcome.event.kind == "merged"
    document = walk.booked(FIRST)
    assert (booked_state(document).stage, booked_state(document).outcome) == ("done", "accepted")
    assert last_entry(document) == AT_APPROVAL + cost_line(bill(FIRST_RECORDS))


def test_a_merge_while_the_reviewer_asks_is_booked_accepted_and_unblocked(
    walk: AcceptanceWalk,
) -> None:
    _merged(walk, "acceptance", "question")

    outcome = walk.tick()

    assert walk.evaluations[-1].kind == "merged"
    assert outcome.event is not None
    assert outcome.event.kind == "merged"
    document = walk.booked(FIRST)
    state = booked_state(document)
    assert (state.stage, state.outcome, state.blocked) == ("done", "accepted", None)
    assert last_entry(document) == BEFORE_APPROVAL + cost_line(bill(FIRST_RECORDS))


@pytest.mark.parametrize(("stage", "blocked"), CASES, ids=CASE_IDS)
def test_the_ticks_after_the_booking_are_idle_commit_nothing_and_post_nothing(
    walk: AcceptanceWalk,
    *,
    remote: Path,
    hosting: FakeHostingService,
    stage: str,
    blocked: Blocked | None,
) -> None:
    number = _merged(walk, stage, blocked)
    walk.tick()
    main = remote_commit(remote, "main")
    posts = hosting.factory_posts(number)

    later = [walk.tick(), walk.tick()]

    assert [outcome.event.kind for outcome in later if outcome.event is not None] == [
        "idle",
        "idle",
    ]
    assert remote_commit(remote, "main") == main
    assert hosting.factory_posts(number) == posts


@pytest.mark.parametrize(("stage", "blocked"), CASES, ids=CASE_IDS)
def test_no_tick_or_evaluation_of_a_merged_acceptance_is_a_reject(
    walk: AcceptanceWalk, *, stage: str, blocked: Blocked | None
) -> None:
    _merged(walk, stage, blocked)

    for _ in range(3):
        walk.tick()

    assert len(walk.outcomes) == 4
    assert "reject" not in walk.kinds()


def test_proposed_stories_leave_the_feature_incomplete_and_open_no_new_acceptance(
    walk: AcceptanceWalk, *, remote: Path
) -> None:
    _merged(walk, "acceptance", None)
    walk.tick()

    assert walk.status() == "incomplete"
    assert walk.due() == []
    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "idle"
    assert remote_commit(remote, branch_of(SECOND)) is None
