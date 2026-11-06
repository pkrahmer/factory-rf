"""An acceptance merged early says so on a definition whose docs route comes first."""

import pytest

from factory.pipeline.application.boundaries import Boundaries
from factory.watching.domain.bills import bill, cost_line
from support.acceptance_walk import FIRST, FIRST_RECORDS, AcceptanceWalk, booked_state, last_entry
from support.human_clone import HumanClone
from support.two_routes_support import TWO_ROUTES

BEFORE_APPROVAL = "done (pull request merged before approval); cost: "
AT_APPROVAL = "done (pull request merged); cost: "


@pytest.fixture
def two_routes(walk: AcceptanceWalk, boundaries: Boundaries, human: HumanClone) -> AcceptanceWalk:
    """The walk with the two-route definition, in the shipped order, on main and in its watcher."""
    human.push_file("main", "factory/pipeline.yml", TWO_ROUTES)
    walk.definition = boundaries.pipeline_reader.parse(TWO_ROUTES)
    return walk


@pytest.mark.parametrize(
    ("stage", "entry"),
    [("acceptance", BEFORE_APPROVAL), ("approval", AT_APPROVAL)],
    ids=["at-acceptance", "at-approval"],
)
def test_an_acceptance_merged_on_the_shipped_order_says_whether_it_came_before_approval(
    two_routes: AcceptanceWalk, stage: str, entry: str
) -> None:
    number = two_routes.open(FIRST)
    handed_over = stage if stage == "approval" else None
    two_routes.record(FIRST, number, FIRST_RECORDS, stage=stage, handed_over=handed_over)
    two_routes.merge(FIRST, number)

    two_routes.tick()

    document = two_routes.booked(FIRST)
    state = booked_state(document)
    assert (state.stage, state.outcome) == ("done", "accepted")
    assert last_entry(document) == entry + cost_line(bill(FIRST_RECORDS))
