"""The time, stage and run a journal record carries, and how appending and booking set them."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.acceptance import AcceptanceState, book_merge, book_refusal
from factory.domain.bills import bill
from factory.domain.journal import FACTORY, HUMAN, JournalRecord, NewEntry, append_entry
from factory.domain.work_item import WorkItemDocument, initial_state

AT = datetime(2026, 10, 17, 20, 31, tzinfo=UTC)
RUN = "a" * 32
RESULT = NewEntry(speaker="tester", kind="result", text="tests written.")
RESULT_LINE = "2. tester: tests written."
ROLE = "acceptance-reviewer"
REPORT_BODY = (
    "# Acceptance of Todo service\n\n## Recommendation\n\nnot accepted\n\n"
    "## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n"
    "3. 2026-10-12 human: Too wide.\n"
)
REPORT_JOURNAL = [
    JournalRecord(number=1, speaker=FACTORY, kind="started"),
    JournalRecord(number=2, speaker=ROLE, kind="result"),
    JournalRecord(number=3, speaker=HUMAN, kind="comment"),
]


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param({}, (None, None, None), id="none-of-the-three"),
        pytest.param({"at": AT, "stage": "tests", "run": RUN}, (AT, "tests", RUN), id="all-three"),
        pytest.param(
            {"at": datetime(2026, 10, 17, 22, 31, tzinfo=timezone(timedelta(hours=2)))},
            (AT, None, None),
            id="offset-stored-in-utc",
        ),
        pytest.param(
            {"run": "0123456789abcdef" * 2}, (None, None, "0123456789abcdef" * 2), id="hex"
        ),
        pytest.param({"at": datetime(2026, 10, 17, 20, 31)}, None, id="naive-at"),  # noqa: DTZ001
        pytest.param({"stage": "Tests"}, None, id="stage-not-a-name"),
        pytest.param({"run": "a" * 31}, None, id="run-31"),
        pytest.param({"run": "a" * 33}, None, id="run-33"),
        pytest.param({"run": "A" + "a" * 31}, None, id="run-uppercase"),
        pytest.param({"run": "g" + "a" * 31}, None, id="run-not-hex"),
    ],
)
def test_a_journal_record_reads_its_time_stage_and_run_when_valid(
    values: dict[str, object], expected: tuple[datetime | None, str | None, str | None] | None
) -> None:
    model: type[BaseModel] = JournalRecord
    if expected is None:
        with pytest.raises(ValidationError):
            model(number=1, speaker="tester", kind="result", **values)
        return

    record = model(number=1, speaker="tester", kind="result", **values)

    assert isinstance(record, JournalRecord)
    assert (record.at, record.stage, record.run) == expected
    if record.at is not None:
        assert record.at.utcoffset() == timedelta(0)


def _created(state: bool = True) -> WorkItemDocument:
    created = NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 17))
    document = append_entry(
        WorkItemDocument(state=initial_state("tests"), body="# T\n\n## Journal\n"), created
    )
    return document if state else document.model_copy(update={"state": None})


@pytest.mark.parametrize(
    ("with_state", "at", "run", "expected"),
    [
        pytest.param(True, None, None, (None, None, None), id="neither"),
        pytest.param(True, AT, None, (AT, "tests", None), id="at-alone"),
        pytest.param(True, AT, RUN, (AT, "tests", RUN), id="at-and-run"),
        pytest.param(True, None, RUN, None, id="run-alone"),
        pytest.param(False, None, RUN, None, id="run-alone-without-state"),
    ],
)
def test_append_entry_stamps_the_record_with_the_time_the_state_stage_and_the_run(
    with_state: bool,
    at: datetime | None,
    run: str | None,
    expected: tuple[datetime | None, str | None, str | None] | None,
) -> None:
    document = _created(with_state)
    if expected is None:
        with pytest.raises(ValueError, match="^an entry with a run needs the time it was written$"):
            append_entry(document, RESULT, at=at, run=run)
        assert document == _created(with_state)
        return

    appended = append_entry(document, RESULT, at=at, run=run)

    assert appended.state is not None
    record = appended.state.journal[-1]
    assert (record.number, record.speaker, record.kind) == (2, "tester", "result")
    assert (record.at, record.stage, record.run) == expected
    assert appended.body == f"{document.body}{RESULT_LINE}\n"


def _report() -> WorkItemDocument:
    state = AcceptanceState(stage="approval", stories=["F0002-S0001"], journal=REPORT_JOURNAL)
    return WorkItemDocument(state=state, body=REPORT_BODY)


def _merge(at: datetime | None) -> WorkItemDocument:
    return book_merge(_report(), bill([]), at=at)


def _refuse(at: datetime | None) -> WorkItemDocument:
    return book_refusal(_report(), role=ROLE, on=date(2026, 10, 12), bill=bill([]), at=at)


@pytest.mark.parametrize("booking", [_merge, _refuse], ids=["merge", "refusal"])
@pytest.mark.parametrize(
    ("at", "expected"),
    [
        pytest.param(AT, (AT, "done", None), id="with-at"),
        pytest.param(None, (None, None, None), id="without-at"),
    ],
)
def test_booking_records_the_done_entry_with_the_time_and_the_done_stage(
    booking: Callable[[datetime | None], WorkItemDocument],
    at: datetime | None,
    expected: tuple[datetime | None, str | None, str | None],
) -> None:
    booked = booking(at)

    assert booked.state is not None
    record = booked.state.journal[-1]
    assert (record.number, record.speaker, record.kind) == (4, FACTORY, "done")
    assert (record.at, record.stage, record.run) == expected
