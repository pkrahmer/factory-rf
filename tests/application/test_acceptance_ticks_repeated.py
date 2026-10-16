"""A feature accepted again over ticks: a new acceptance, the earlier report left as it was."""

from pathlib import Path

import pytest

from acceptance_walk import (
    FIRST,
    FIRST_RECORDS,
    SECOND,
    SECOND_RECORDS,
    AcceptanceWalk,
    report_of,
)
from factory.adapters.git_cli import GitCli
from factory.domain.identifiers import branch_name
from factory.domain.paths import cost_records_path
from git_support import remote_commit

REPEATED = [("approval", "merged"), ("acceptance", "run")]


@pytest.fixture
def walk(walk: AcceptanceWalk) -> AcceptanceWalk:
    """Return a walk where `F0002-A0001` is accepted for two stories and a third is archived."""
    number = walk.open(FIRST)
    walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    walk.merge(FIRST, number)
    walk.tick()
    walk.archive("F0002-S0003-c.md", "# C\n")
    return walk


def _merge_second(walk: AcceptanceWalk, stage: str) -> None:
    number = walk.open(SECOND)
    handed_over = stage if stage == "approval" else None
    walk.record(SECOND, number, SECOND_RECORDS, stage=stage, handed_over=handed_over)
    walk.merge(SECOND, number)


def test_a_story_archived_after_the_acceptance_opens_the_next_acceptance_in_one_tick(
    walk: AcceptanceWalk, *, remote: Path, checkout: GitCli
) -> None:
    assert walk.status() == "due"

    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "acceptance_due"
    assert remote_commit(remote, branch_name(SECOND)) is not None
    checkout.fetch()
    assert checkout.show_file(f"origin/{branch_name(SECOND)}", report_of(SECOND)) is not None


def test_opening_the_repeated_acceptance_leaves_the_earlier_report_and_costs_byte_for_byte(
    walk: AcceptanceWalk, *, checkout: GitCli
) -> None:
    paths = [report_of(FIRST, "done"), cost_records_path(report_of(FIRST, "done"))]
    checkout.fetch()
    before = [checkout.show_file("origin/main", path) for path in paths]
    assert None not in before

    walk.tick()

    checkout.fetch()
    assert [checkout.show_file("origin/main", path) for path in paths] == before


@pytest.mark.parametrize(("stage", "kind"), REPEATED, ids=["at-approval", "at-acceptance"])
def test_the_merged_repeated_acceptance_is_booked_in_one_tick_and_the_feature_rests(
    walk: AcceptanceWalk, *, stage: str, kind: str
) -> None:
    _merge_second(walk, stage)
    assert walk.status() == "merged_unrecorded"
    assert walk.due() == []

    walk.tick()

    evaluated = walk.evaluations[-1]
    assert evaluated.kind == kind
    assert evaluated.work_item is not None
    assert evaluated.work_item.id == SECOND
    assert walk.status() == "accepted"
    assert walk.due() == []
    outcome = walk.tick()
    assert outcome.event is not None
    assert outcome.event.kind == "idle"


@pytest.mark.parametrize("stage", ["approval", "acceptance"])
def test_no_tick_or_evaluation_of_a_repeated_acceptance_is_a_reject(
    walk: AcceptanceWalk, stage: str
) -> None:
    _merge_second(walk, stage)

    walk.tick()
    walk.tick()

    assert "reject" not in walk.kinds()
