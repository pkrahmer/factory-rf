"""The journal functions on a feature acceptance keep its state's type and its extra fields."""

from factory.domain.acceptance import AcceptanceState
from factory.domain.journal import (
    JournalRecord,
    NewEntry,
    append_entry,
    restore_state_and_journal,
)
from factory.domain.work_item import WorkItemDocument

BODY = "# Acceptance of Todo service\n\n## Journal\n\n1. factory: created.\n"
CREATED = [JournalRecord(number=1, speaker="factory", kind="created")]


def test_append_entry_keeps_the_acceptance_state() -> None:
    state = AcceptanceState(
        stage="done", stories=["F0001-S0001"], outcome="refused", journal=CREATED
    )
    document = WorkItemDocument(state=state, body=BODY)

    appended = append_entry(document, NewEntry(speaker="acceptance", kind="result", text="ok"))

    assert isinstance(appended.state, AcceptanceState)
    assert appended.state.stories == ["F0001-S0001"]
    assert appended.state.outcome == "refused"


def test_restore_puts_back_the_baseline_stories_and_outcome() -> None:
    baseline_state = AcceptanceState(
        stage="done", stories=["F0001-S0001"], outcome="refused", journal=CREATED
    )
    current_state = AcceptanceState(
        stage="done",
        stories=["F0001-S0001", "F0001-S0002"],
        outcome="accepted",
        journal=CREATED,
    )
    baseline = WorkItemDocument(state=baseline_state, body=BODY)
    current = WorkItemDocument(state=current_state, body=BODY)

    restored = restore_state_and_journal(current, baseline)

    assert isinstance(restored.state, AcceptanceState)
    assert restored.state.stories == ["F0001-S0001"]
    assert restored.state.outcome == "refused"
