"""A journal record's time, stage and run in the work item file: written when set, read back."""

from datetime import UTC, datetime

import pytest

from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state

AT = datetime(2026, 10, 17, 20, 31, tzinfo=UTC)
HEAD = (
    "---\nstage: tests\nblocked: null\nround: 0\nattempts: 0\ncrashes: 0\npull_request: null\n"
    "comments_read: []\nhanded_over: null\nclaim: null\njournal:\n"
)
BODY = "# T\n\n## Journal\n\n1. 2026-10-17 human: created.\n2. tester: tests written.\n"
CREATED_LINES = "- number: 1\n  speaker: human\n  kind: created\n"
RESULT_LINES = "- number: 2\n  speaker: tester\n  kind: result\n"
OLD_FILE = f"{HEAD}{CREATED_LINES}{RESULT_LINES}---\n\n{BODY}"
STAMPED_FILE = (
    f"{HEAD}{CREATED_LINES}{RESULT_LINES}  at: '2026-10-17T20:31:00Z'\n  stage: tests\n"
    f"  run: {'a' * 32}\n---\n\n{BODY}"
)


def _document(result: JournalRecord) -> WorkItemDocument:
    created = JournalRecord(number=1, speaker="human", kind="created")
    state = initial_state("tests").model_copy(update={"journal": [created, result]})
    return WorkItemDocument(state=state, body=BODY)


@pytest.mark.parametrize(
    ("result", "lines"),
    [
        pytest.param(
            JournalRecord(
                number=2, speaker="tester", kind="result", at=AT, stage="tests", run="a" * 32
            ),
            f"{RESULT_LINES}  at: '2026-10-17T20:31:00Z'\n  stage: tests\n  run: {'a' * 32}\n",
            id="all-three",
        ),
        pytest.param(
            JournalRecord(number=2, speaker="tester", kind="result", at=AT, stage="tests"),
            f"{RESULT_LINES}  at: '2026-10-17T20:31:00Z'\n  stage: tests\n",
            id="no-run",
        ),
        pytest.param(
            JournalRecord(number=2, speaker="tester", kind="result"),
            RESULT_LINES,
            id="none-of-the-three",
        ),
        pytest.param(
            JournalRecord(
                number=2, speaker="tester", kind="result", at=AT, stage="tests", run="1" * 32
            ),
            f"{RESULT_LINES}  at: '2026-10-17T20:31:00Z'\n  stage: tests\n  run: '{'1' * 32}'\n",
            id="numeric-looking-run",
        ),
    ],
)
def test_the_writer_writes_a_records_time_stage_and_run_only_when_set(
    result: JournalRecord, lines: str
) -> None:
    document = _document(result)

    text = FrontmatterWorkItemWriter().render(document)

    assert text == f"{HEAD}{CREATED_LINES}{lines}---\n\n{BODY}"
    assert FrontmatterWorkItemReader().parse(text) == document


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(OLD_FILE, (None, None, None), id="written-before"),
        pytest.param(STAMPED_FILE, (AT, "tests", "a" * 32), id="stamped"),
    ],
)
def test_a_work_item_file_reads_with_and_without_the_stamps_and_is_written_back_the_same(
    text: str, expected: tuple[datetime | None, str | None, str | None]
) -> None:
    document = FrontmatterWorkItemReader().parse(text)

    assert document.state is not None
    first = document.state.journal[0]
    assert (first.at, first.stage, first.run) == (None, None, None)
    last = document.state.journal[-1]
    assert (last.at, last.stage, last.run) == expected
    assert FrontmatterWorkItemWriter().render(document) == text
