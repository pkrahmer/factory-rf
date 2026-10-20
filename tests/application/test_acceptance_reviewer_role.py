"""The acceptance handlers read the reviewer's own last result, and the close's commits say so."""

from datetime import date
from pathlib import Path

import pytest

from acceptance_walk import FIRST, FIRST_RECORDS, REVIEWER, AcceptanceWalk, report_of
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.domain.identifiers import branch_name
from factory.domain.journal import NewEntry, append_entry
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.sections import section_text
from factory.domain.work_item import WorkItemDocument
from git_support import remote_commit
from human_clone import HumanClone

ROLE = REVIEWER
BRANCH = branch_name(FIRST)
ACCEPTED = NewEntry(speaker=ROLE, kind="result", text="accepted; the feature holds together.")
NOT_ACCEPTED = NewEntry(speaker=ROLE, kind="result", text="not accepted")
TOO_WIDE = NewEntry(speaker="human", kind="comment", text="Too wide.", on=date(2026, 10, 12))
RED = NewEntry(speaker="tester", kind="result", text="red")
REFUSED = "Refused by the human on 2026-10-12: Too wide. Cut the second story."


def _push_entries(
    boundaries: Boundaries, human: HumanClone, document: WorkItemDocument, entries: list[NewEntry]
) -> None:
    for entry in entries:
        document = append_entry(document, entry)
    human.push_file(BRANCH, report_of(FIRST), boundaries.work_item_writer.render(document))


@pytest.mark.parametrize(
    "entries",
    [
        pytest.param([ACCEPTED], id="the-reviewer-alone"),
        pytest.param([ACCEPTED, RED], id="a-later-result-of-another-speaker"),
    ],
)
def test_the_hand_over_s_findings_are_the_reviewer_s_last_result(
    boundaries: Boundaries,
    walk: AcceptanceWalk,
    entries: list[NewEntry],
    *,
    human: HumanClone,
    hosting: FakeHostingService,
) -> None:
    number = walk.open(FIRST)
    document = walk.record(FIRST, number, FIRST_RECORDS, stage="approval")
    _push_entries(boundaries, human, document, entries)

    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "hand_over"
    findings = section_text(hosting.description(number), "Findings in short")
    assert findings == "accepted; the feature holds together."


@pytest.mark.parametrize(
    "entries",
    [
        pytest.param([NOT_ACCEPTED, TOO_WIDE, RED], id="a-later-result-of-another-speaker"),
        pytest.param([NOT_ACCEPTED, TOO_WIDE], id="the-reviewer-and-the-human-alone"),
    ],
)
def test_the_close_s_reason_is_the_human_s_comments_after_the_reviewer_s_last_result(
    boundaries: Boundaries, walk: AcceptanceWalk, entries: list[NewEntry], *, human: HumanClone
) -> None:
    number = walk.open(FIRST)
    document = walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    _push_entries(boundaries, human, document, entries)
    walk.close(number, "Cut the second story.")

    outcome = walk.tick()

    assert outcome.event is not None
    assert outcome.event.kind == "closed"
    assert section_text(walk.booked(FIRST).body, "Recommendation") == REFUSED


def test_the_close_is_committed_as_close_recorded_on_the_branch_and_closed_refused_on_main(
    boundaries: Boundaries,
    walk: AcceptanceWalk,
    *,
    human: HumanClone,
    remote: Path,
    kill_points: KillPoints,
) -> None:
    number = walk.open(FIRST)
    document = walk.record(FIRST, number, FIRST_RECORDS, stage="approval", handed_over="approval")
    _push_entries(boundaries, human, document, [NOT_ACCEPTED, TOO_WIDE, RED])
    walk.close(number, "Cut the second story.")
    branch_head = remote_commit(remote, BRANCH)
    main_head = remote_commit(remote, "main")
    assert branch_head is not None
    assert main_head is not None
    kill_points.arm(KillPoint.AFTER_PUSH)

    with pytest.raises(InjectedKill):
        walk.tick()

    boundaries.git.fetch()
    [branch_commit] = boundaries.git.log(f"origin/{BRANCH}", since=branch_head)
    assert branch_commit.subject == f"work item {FIRST}: close recorded"
    walk.tick()
    boundaries.git.fetch()
    [main_commit] = boundaries.git.log("origin/main", since=main_head)
    assert main_commit.subject == f"work item {FIRST}: closed, refused"
