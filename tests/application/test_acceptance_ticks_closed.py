"""An acceptance the human closes is booked refused in one tick; its hand-over runs once."""

from pathlib import Path

from acceptance_walk import (
    FIRST,
    FIRST_RECORDS,
    REVIEWER,
    SECOND,
    AcceptanceWalk,
    booked_state,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.acceptance import RECOMMENDATION, acceptance_description
from factory.domain.identifiers import branch_name
from factory.domain.sections import section_text
from git_support import remote_commit

REASON = "The list cannot be sorted."


def test_a_close_at_the_approval_is_booked_refused_with_the_comment_until_another_archive(
    boundaries: Boundaries, walk: AcceptanceWalk, *, remote: Path
) -> None:
    number = walk.open(FIRST)
    walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    walk.close(number, REASON)

    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "closed"
    document = walk.booked(FIRST)
    assert (booked_state(document).stage, booked_state(document).outcome) == ("done", "refused")
    recommendation = section_text(document.body, RECOMMENDATION)
    assert recommendation is not None
    refused_on = boundaries.clock.now().date().isoformat()
    assert recommendation.split("\n\n")[0].strip() == (
        f"Refused by the human on {refused_on}: {REASON}"
    )
    assert walk.status() == "refused"
    assert walk.due() == []
    later = [walk.tick(), walk.tick()]
    assert [outcome.event.kind for outcome in later if outcome.event is not None] == [
        "idle",
        "idle",
    ]
    walk.archive("F0002-S0003-c.md", "# C\n")
    reopened = walk.tick()
    assert reopened.event is not None
    assert reopened.event.kind == "acceptance_due"
    assert remote_commit(remote, branch_name(SECOND)) is not None


def test_a_close_before_the_approval_runs_through_the_gate_and_is_booked_refused(
    walk: AcceptanceWalk, *, agent_runtime: FakeAgentRuntime
) -> None:
    number = walk.open(FIRST)
    walk.record(FIRST, number, FIRST_RECORDS, stage="acceptance")
    walk.close(number)

    outcome = walk.tick()

    assert walk.evaluations[-1].kind == "run"
    assert outcome.event is not None
    assert (outcome.event.kind, outcome.dispatch) == ("run", "handled")
    state = booked_state(walk.booked(FIRST))
    assert (state.stage, state.outcome) == ("done", "refused")
    assert agent_runtime.requests() == []
    walk.tick()
    assert "reject" not in walk.kinds()


def test_an_acceptance_at_its_approval_is_handed_over_once_through_the_wiring(
    walk: AcceptanceWalk, *, hosting: FakeHostingService
) -> None:
    number = walk.open(FIRST)
    document = walk.record(FIRST, number, FIRST_RECORDS, stage="approval")

    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "hand_over"
    view = hosting.get_pull_request(number)
    assert (view.state, view.draft) == ("open", False)
    assert hosting.description(number) == acceptance_description(document, REVIEWER)
    [post] = hosting.factory_posts(number)
    assert post.key is not None
    assert post.key.kind == "cost_table"
    again = walk.tick()
    assert again.event is not None
    assert again.event.kind == "idle"
    assert hosting.factory_posts(number) == [post]
