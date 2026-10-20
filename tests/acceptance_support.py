"""Helpers for acceptance tests: a report whose journal holds given entries."""

from factory.domain.acceptance import AcceptanceState
from factory.domain.journal import HUMAN, JournalKind, JournalRecord
from factory.domain.work_item import WorkItemDocument


def report_of(entries: list[tuple[str, JournalKind, str]]) -> WorkItemDocument:
    """A report whose journal holds the entries; the human's lines carry a date, as rendered."""
    journal = [
        JournalRecord(number=number, speaker=speaker, kind=kind)
        for number, (speaker, kind, _) in enumerate(entries, 1)
    ]
    lines = [
        f"{number}. 2026-10-12 {speaker}: {text}"
        if speaker == HUMAN
        else f"{number}. {speaker}: {text}"
        for number, (speaker, _, text) in enumerate(entries, 1)
    ]
    body = "# Acceptance of Todo service\n\n## Journal\n\n" + "\n".join(lines) + "\n"
    state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=journal)
    return WorkItemDocument(state=state, body=body)
