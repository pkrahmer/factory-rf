"""The journal's speaker and kind are read from the front matter, never from the text."""

from datetime import date

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.journal import NewEntry, append_entry, last_record
from factory.domain.work_item import WorkItemDocument, initial_state


def test_a_changed_speaker_in_the_text_changes_no_record() -> None:
    document = append_entry(
        WorkItemDocument(state=initial_state("intake"), body="# T\n\n## Journal\n"),
        NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 12)),
    )
    document = append_entry(document, NewEntry(speaker="intake", kind="result", text="accepted"))
    text = FrontmatterWorkItemWriter().render(document)
    edited = text.replace("2. intake: accepted", "2. Intake Agent: accepted")

    parsed = FrontmatterWorkItemReader().parse(edited)

    assert edited != text
    assert parsed.state is not None
    assert document.state is not None
    assert parsed.state.journal == document.state.journal
    assert last_record(parsed, speaker="intake") == last_record(document, speaker="intake")
