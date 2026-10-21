"""The handlers that ask record on the question the block it opened."""

from collections.abc import Sequence
from typing import Literal

import pytest

from crash_support import (
    BRANCH,
    PATH,
    Rerun,
    claim,
    crash_event,
    expired_claim,
    expired_event,
    handler,
    open_pull_request,
    other_handler,
    remote_state,
    snapshot,
)
from definition_support import pipeline_definition
from factory.adapters.clock import ManualClock
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.handlers.closed import ClosedHandler
from factory.application.handlers.questions import AskHandler
from factory.domain.events import Event, EventKind
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry
from factory.domain.work_item import WorkItemDocument, WorkItemState
from human_clone import HumanClone

BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"
CREATED = JournalRecord(number=1, speaker=HUMAN, kind="created")


def _publish(
    boundaries: Boundaries, human: HumanClone, state: WorkItemState, entries: Sequence[NewEntry]
) -> Event:
    """Push a document in `state` with `entries` to the branch; the event's kind is set later."""
    document = WorkItemDocument(state=state, body=BODY)
    for entry in entries:
        document = append_entry(document, entry)
    human.push_file(BRANCH, PATH, boundaries.work_item_writer.render(document))
    return Event(kind="ask", work_item=snapshot(boundaries), remote_state="a" * 40)


def _of_kind(event: Event, kind: EventKind) -> Event:
    return event.model_copy(update={"kind": kind})


def test_the_ask_handler_at_the_attempts_cap_records_the_question_with_its_block(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    state = WorkItemState(
        stage="doing", attempts=2, pull_request=open_pull_request(hosting), journal=[CREATED]
    )
    stall = NewEntry(speaker=FACTORY, kind="stall", text="the agent gave no result")
    event = _publish(boundaries, human, state, [stall])

    AskHandler(boundaries, pipeline_definition(boundaries)).handle(event)

    last = remote_state(boundaries).journal[-1]
    assert (last.speaker, last.kind, last.blocked) == (FACTORY, "question", "attempts_cap")


@pytest.mark.parametrize("ended_by", ["crash", "expiry"])
def test_the_recovery_at_the_crash_cap_records_the_question_with_its_block(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    hosting: FakeHostingService,
    clock: ManualClock,
    ended_by: Literal["crash", "expiry"],
) -> None:
    pull_request = open_pull_request(hosting)
    if ended_by == "crash":
        claimed = claim(boundaries, human, crashes=1, pull_request=pull_request)
        handler(boundaries, claimed.definition, Rerun()).handle(crash_event(snapshot(boundaries)))
    else:
        claimed = expired_claim(boundaries, human, clock, crashes=1, pull_request=pull_request)
        other_handler(boundaries, claimed, Rerun()).handle(expired_event(snapshot(boundaries)))

    ended, question = remote_state(boundaries).journal[-2:]
    assert (ended.kind, ended.reason) == (ended_by, None)
    assert (question.kind, question.blocked) == ("question", "crash_cap")


def test_a_close_that_sends_back_without_a_reason_records_the_question_with_its_block(
    boundaries: Boundaries, *, human: HumanClone, hosting: FakeHostingService
) -> None:
    pull_request = open_pull_request(hosting)
    state = WorkItemState(
        stage="approval", pull_request=pull_request, handed_over="approval", journal=[CREATED]
    )
    result = NewEntry(speaker="smoke-tester", kind="result", text="the smoke test passed.")
    event = _publish(boundaries, human, state, [result])
    hosting.set_draft(pull_request, False)
    hosting.close_by_human(pull_request)

    ClosedHandler(boundaries, pipeline_definition(boundaries)).handle(_of_kind(event, "closed"))

    last = remote_state(boundaries).journal[-1]
    assert (last.speaker, last.kind, last.blocked) == (FACTORY, "question", "send_back")
