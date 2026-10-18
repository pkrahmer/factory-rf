"""A record's block or stall reason in the work item file: written when set, read back."""

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state

HEAD = (
    "---\nstage: tests\nblocked: null\nround: 0\nattempts: 0\ncrashes: 0\npull_request: null\n"
    "comments_read: []\nhanded_over: null\nclaim: null\njournal:\n"
)
BODY = (
    "# T\n\n## Journal\n\n1. 2026-10-17 human: created.\n2. factory: Try again?\n"
    "3. factory: Stage tests stalled.\n"
)
CREATED = JournalRecord(number=1, speaker="human", kind="created")
CREATED_LINES = "- number: 1\n  speaker: human\n  kind: created\n"
QUESTION_LINES = "- number: 2\n  speaker: factory\n  kind: question\n"
STALL_LINES = "- number: 3\n  speaker: factory\n  kind: stall\n"


@pytest.mark.parametrize(
    ("question", "stall", "lines"),
    [
        pytest.param(
            JournalRecord(number=2, speaker="factory", kind="question", blocked="crash_cap"),
            JournalRecord(number=3, speaker="factory", kind="stall", reason="time_limit"),
            f"{QUESTION_LINES}  blocked: crash_cap\n{STALL_LINES}  reason: time_limit\n",
            id="with-causes",
        ),
        pytest.param(
            JournalRecord(number=2, speaker="factory", kind="question"),
            JournalRecord(number=3, speaker="factory", kind="stall"),
            f"{QUESTION_LINES}{STALL_LINES}",
            id="without-causes",
        ),
    ],
)
def test_the_writer_writes_a_records_cause_only_when_set_and_reads_it_back(
    question: JournalRecord, stall: JournalRecord, lines: str
) -> None:
    state = initial_state("tests").model_copy(update={"journal": [CREATED, question, stall]})
    document = WorkItemDocument(state=state, body=BODY)

    text = FrontmatterWorkItemWriter().render(document)

    assert text == f"{HEAD}{CREATED_LINES}{lines}---\n\n{BODY}"
    assert FrontmatterWorkItemReader().parse(text) == document
