"""The journal: new entries, their visible form, appending, reading back and the restore."""

import ast
import subprocess
import sys
from datetime import UTC, date, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import WorkItemFormatError
from factory.domain.journal import (
    JournalKind,
    JournalRecord,
    NewEntry,
    append_entry,
    entry_text,
    last_record,
    render_entry,
    restore_state_and_journal,
)
from factory.domain.sections import sections
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState, initial_state
from source_search import modules

CREATED_ON = date(2026, 10, 12)
CREATED = NewEntry(speaker="human", kind="created", text="created.", on=CREATED_ON)
CREATED_LINE = "1. 2026-10-12 human: created."
MULTILINE = "accepted\nfirst\n\nsecond"


def _result(text: str) -> NewEntry:
    return NewEntry(speaker="intake", kind="result", text=text)


def _records(count: int) -> list[JournalRecord]:
    return [
        JournalRecord(number=number, speaker="factory", kind="started")
        for number in range(1, count + 1)
    ]


def _fault(error: pytest.ExceptionInfo[WorkItemFormatError]) -> str:
    return error.value.fault


def _created_document() -> WorkItemDocument:
    return append_entry(
        WorkItemDocument(state=initial_state("intake"), body="# T\n\n## Journal\n"), CREATED
    )


def test_a_new_entry_strips_its_text_and_needs_a_date_only_from_the_human() -> None:
    started = NewEntry(speaker="factory", kind="started", text=" started intake as factory-1.\n")
    created = NewEntry(speaker="human", kind="created", text="created.", on=CREATED_ON)

    assert started.text == "started intake as factory-1."
    assert started.on is None
    assert created.on == CREATED_ON
    assert created.text == "created."


@pytest.mark.parametrize(
    "values",
    [
        {"speaker": "human", "kind": "created", "text": "created."},
        {"speaker": "factory", "kind": "started", "text": "started.", "on": CREATED_ON},
        {"speaker": "intake", "kind": "result", "text": "accepted", "on": CREATED_ON},
        {"speaker": "intake", "kind": "result", "text": ""},
        {"speaker": "intake", "kind": "result", "text": "  \n"},
        {"speaker": "Intake", "kind": "result", "text": "accepted"},
        {"speaker": "intake", "kind": "note", "text": "accepted"},
        {"speaker": "intake", "kind": "result", "text": "accepted", "cost": 1},
    ],
)
def test_a_new_entry_refuses_invalid_values(values: dict[str, object]) -> None:
    model: type[BaseModel] = NewEntry

    with pytest.raises(ValidationError):
        model(**values)


def test_a_new_entry_is_frozen() -> None:
    entry = _result("accepted")

    with pytest.raises(ValidationError):
        setattr(entry, "text", "changed")  # noqa: B010  (assigning to a frozen field)


def test_render_entry_writes_number_date_speaker_and_text() -> None:
    started = NewEntry(speaker="factory", kind="started", text="started intake as factory-1.")

    assert render_entry(2, started) == "2. factory: started intake as factory-1."
    assert render_entry(1, CREATED) == CREATED_LINE


def test_render_entry_indents_continuation_lines_and_keeps_blank_lines_empty() -> None:
    assert render_entry(3, _result(MULTILINE)) == "3. intake: accepted\n   first\n\n   second"


@pytest.mark.parametrize(
    ("number", "indent"),
    [(1, 3), (9, 3), (10, 4), (99, 4), (100, 5), (999, 5)],
)
def test_the_continuation_indent_is_the_width_of_the_number(number: int, indent: int) -> None:
    pad = " " * indent

    assert render_entry(number, _result(MULTILINE)) == (
        f"{number}. intake: accepted\n{pad}first\n\n{pad}second"
    )


def test_append_entry_writes_the_first_entry_under_the_heading_and_its_record() -> None:
    document = _created_document()

    assert document.body == f"# T\n\n## Journal\n\n{CREATED_LINE}\n"
    assert document.state is not None
    assert document.state.journal == [JournalRecord(number=1, speaker="human", kind="created")]


def test_append_entry_puts_the_next_entry_directly_under_the_last() -> None:
    document = append_entry(_created_document(), _result("accepted"))

    assert document.body == f"# T\n\n## Journal\n\n{CREATED_LINE}\n2. intake: accepted\n"
    assert document.state is not None
    assert document.state.journal == [
        JournalRecord(number=1, speaker="human", kind="created"),
        JournalRecord(number=2, speaker="intake", kind="result"),
    ]


def test_append_entry_numbers_the_tenth_entry_ten() -> None:
    entries = "".join(f"{number}. factory: started.\n" for number in range(1, 10))
    document = WorkItemDocument(
        state=WorkItemState(stage="intake", journal=_records(9)),
        body=f"# T\n\n## Journal\n\n{entries}",
    )

    appended = append_entry(document, _result("accepted"))

    assert appended.body == f"# T\n\n## Journal\n\n{entries}10. intake: accepted\n"
    assert appended.state is not None
    assert appended.state.journal[-1] == JournalRecord(number=10, speaker="intake", kind="result")


@pytest.mark.parametrize("final_newline", ["\n", ""])
def test_append_entry_changes_nothing_else(final_newline: str) -> None:
    before = "# T\n\n## Before\n\ntext\n\n## Journal\n\n" + CREATED_LINE
    body = f"{before}\n\n## After\n\nmore{final_newline}"
    state = WorkItemState(
        stage="doing",
        round=1,
        attempts=2,
        pull_request=12,
        comments_read=[3],
        journal=[JournalRecord(number=1, speaker="human", kind="created")],
    )
    document = WorkItemDocument(state=state, body=body, ignored_keys=["owner"])

    appended = append_entry(document, _result("accepted"))

    assert appended.body == f"{before}\n2. intake: accepted\n\n## After\n\nmore{final_newline}"
    assert appended.state is not None
    assert appended.state.model_dump(exclude={"journal"}) == state.model_dump(exclude={"journal"})
    assert appended.ignored_keys == ["owner"]
    assert document.body == body
    assert document.state == state
    assert document.ignored_keys == ["owner"]


def test_an_entry_with_a_heading_and_a_fence_adds_no_section() -> None:
    body = f"# T\n\n## Journal\n\n{CREATED_LINE}\n\n## After\n\nmore\n"
    document = WorkItemDocument(state=WorkItemState(stage="intake", journal=_records(1)), body=body)
    text = "accepted\n## Not a heading\n```\n## Inside a fence\n```\nend"

    appended = append_entry(document, _result(text))

    headings = [found.heading for found in sections(body)]
    assert [found.heading for found in sections(appended.body)] == headings


def test_append_entry_refuses_a_document_without_state() -> None:
    document = WorkItemDocument(state=None, body="# T\n\n## Journal\n")

    with pytest.raises(WorkItemFormatError) as caught:
        append_entry(document, CREATED)

    assert _fault(caught) == "the document has no state"


@pytest.mark.parametrize(
    "body",
    ["# T\n\n## Other\n\ntext\n", "# T\n\n```\n## Journal\n```\n"],
)
def test_append_entry_refuses_a_body_without_a_journal_section(body: str) -> None:
    document = WorkItemDocument(state=initial_state("intake"), body=body)

    with pytest.raises(WorkItemFormatError) as caught:
        append_entry(document, CREATED)

    assert _fault(caught) == "missing section: ## Journal"


def test_entry_text_returns_the_text_as_it_was_given() -> None:
    document = append_entry(_created_document(), _result(MULTILINE))

    assert entry_text(document, 2) == MULTILINE
    assert entry_text(document, 1) == "created."


def test_entry_text_returns_only_the_entry_asked_for() -> None:
    first = NewEntry(speaker="human", kind="created", text="created.\nwith detail", on=CREATED_ON)
    document = append_entry(
        WorkItemDocument(state=initial_state("intake"), body="# T\n\n## Journal\n"), first
    )
    for number in range(2, 11):
        document = append_entry(document, _result(f"entry {number}"))

    assert entry_text(document, 1) == "created.\nwith detail"
    assert entry_text(document, 2) == "entry 2"
    assert entry_text(document, 10) == "entry 10"


def test_entry_text_ignores_an_indented_number() -> None:
    first = NewEntry(
        speaker="human", kind="created", text="created.\n2. not an entry", on=CREATED_ON
    )
    document = append_entry(
        WorkItemDocument(state=initial_state("intake"), body="# T\n\n## Journal\n"), first
    )

    assert "\n   2. not an entry\n" in document.body
    assert entry_text(document, 1) == "created.\n2. not an entry"
    with pytest.raises(WorkItemFormatError) as caught:
        entry_text(document, 2)

    assert _fault(caught) == "no journal entry 2"


def test_entry_text_drops_the_blank_lines_before_the_next_section() -> None:
    start = WorkItemDocument(
        state=initial_state("intake"), body="# T\n\n## Journal\n\n\n## After\n\ntail\n"
    )
    document = append_entry(append_entry(start, CREATED), _result("accepted"))

    assert "accepted\n\n\n## After" in document.body
    assert entry_text(document, 2) == "accepted"


def test_entry_text_refuses_a_missing_entry() -> None:
    document = append_entry(_created_document(), _result("accepted"))

    with pytest.raises(WorkItemFormatError) as caught:
        entry_text(document, 7)

    assert _fault(caught) == "no journal entry 7"


def test_entry_text_refuses_a_body_without_a_journal_section() -> None:
    document = WorkItemDocument(state=initial_state("intake"), body="# T\n\n## Other\n")

    with pytest.raises(WorkItemFormatError) as caught:
        entry_text(document, 1)

    assert _fault(caught) == "missing section: ## Journal"


def _mixed_journal() -> WorkItemDocument:
    journal = [
        JournalRecord(number=1, speaker="human", kind="created"),
        JournalRecord(number=2, speaker="intake", kind="result"),
        JournalRecord(number=3, speaker="factory", kind="started"),
        JournalRecord(number=4, speaker="intake", kind="question"),
        JournalRecord(number=5, speaker="factory", kind="result"),
    ]
    return WorkItemDocument(state=WorkItemState(stage="intake", journal=journal), body="# T\n")


def test_last_record_without_a_filter_is_the_last_record() -> None:
    assert last_record(_mixed_journal()) == JournalRecord(
        number=5, speaker="factory", kind="result"
    )


@pytest.mark.parametrize(
    ("speaker", "kind", "number"),
    [
        ("intake", None, 4),
        (None, "result", 5),
        (None, "started", 3),
        ("intake", "result", 2),
        ("human", "created", 1),
    ],
)
def test_last_record_is_the_last_that_matches_every_filter(
    speaker: str | None, kind: JournalKind | None, number: int
) -> None:
    document = _mixed_journal()
    assert document.state is not None

    assert last_record(document, speaker=speaker, kind=kind) == document.state.journal[number - 1]


def test_last_record_is_none_when_nothing_matches() -> None:
    document = _mixed_journal()

    assert last_record(document, speaker="human", kind="result") is None
    assert last_record(document, speaker="review") is None
    assert last_record(document, kind="done") is None
    assert last_record(WorkItemDocument(state=initial_state("intake"), body="# T\n")) is None


def test_last_record_refuses_a_document_without_state() -> None:
    with pytest.raises(WorkItemFormatError) as caught:
        last_record(WorkItemDocument(state=None, body="# T\n"))

    assert _fault(caught) == "the document has no state"


def test_restore_refuses_a_baseline_without_state() -> None:
    baseline = WorkItemDocument(state=None, body=f"# T\n\n## Journal\n\n{CREATED_LINE}\n")

    with pytest.raises(WorkItemFormatError) as caught:
        restore_state_and_journal(_created_document(), baseline)

    assert _fault(caught) == "the document has no state"


def test_restore_returns_the_baseline_state_and_the_current_ignored_keys() -> None:
    baseline = WorkItemDocument(
        state=WorkItemState(stage="intake", journal=_records(1)),
        body=f"# T\n\n## Journal\n\n{CREATED_LINE}\n",
        ignored_keys=["baseline"],
    )
    claim = Claim(
        instance="factory-1",
        stage="doing",
        started_at=datetime(2026, 10, 13, 8, 30, tzinfo=UTC),
        lease_duration=60,
    )
    current_state = WorkItemState(
        stage="doing",
        blocked="question",
        attempts=2,
        pull_request=7,
        claim=claim,
        journal=_records(2),
    )
    current = WorkItemDocument(state=current_state, body=baseline.body, ignored_keys=["current"])

    restored = restore_state_and_journal(current, baseline)

    assert restored.state == baseline.state
    assert restored.ignored_keys == ["current"]


def test_restore_puts_the_baseline_journal_back_and_keeps_other_edits() -> None:
    baseline = WorkItemDocument(
        state=WorkItemState(stage="intake", journal=_records(1)),
        body=f"# T\n\nSpec.\n\n## Journal\n\n{CREATED_LINE}\n\n## After\n\ntail\n",
    )
    current = WorkItemDocument(
        state=WorkItemState(stage="doing", journal=_records(2)),
        body=(
            "# T\n\nSpec changed.\n\n## Journal\n\n"
            "1. 2026-10-12 human: forged.\n2. intake: extra\n\n\n## After\n\ntail changed\n"
        ),
    )

    restored = restore_state_and_journal(current, baseline)

    assert restored.body == (
        f"# T\n\nSpec changed.\n\n## Journal\n\n{CREATED_LINE}\n\n\n## After\n\ntail changed\n"
    )


@pytest.mark.parametrize("current_body", ["# T\n\nSpec.\n", "# T\n\nSpec.", "# T\n\nSpec.\n\n\n"])
def test_restore_adds_the_journal_when_the_current_body_has_none(current_body: str) -> None:
    baseline = WorkItemDocument(
        state=WorkItemState(stage="intake", journal=_records(1)),
        body=f"# T\n\n## Journal\n\n{CREATED_LINE}\n\n## After\n\ntail\n",
    )
    current = WorkItemDocument(state=initial_state("doing"), body=current_body)

    restored = restore_state_and_journal(current, baseline)

    assert restored.body == f"# T\n\nSpec.\n\n## Journal\n\n{CREATED_LINE}\n"


def test_restore_refuses_a_baseline_without_a_journal_section() -> None:
    baseline = WorkItemDocument(state=initial_state("intake"), body="# T\n\nSpec.\n")

    with pytest.raises(WorkItemFormatError) as caught:
        restore_state_and_journal(_created_document(), baseline)

    assert _fault(caught) == "missing section: ## Journal"


@pytest.mark.parametrize("module", ["factory.domain.journal", "factory.domain.work_item"])
def test_either_module_can_be_imported_first(module: str) -> None:
    result = subprocess.run(  # noqa: S603  (fixed interpreter and code, no input)
        [sys.executable, "-c", f"import {module}"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr


def _is_type_checking(test: ast.expr) -> bool:
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _imports_work_item(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(alias.name == "factory.domain.work_item" for alias in node.names)
    return isinstance(node, ast.ImportFrom) and node.module == "factory.domain.work_item"


def test_the_journal_imports_the_work_item_only_for_type_checking() -> None:
    tree = modules()["factory.domain.journal"]
    guarded = {
        id(node)
        for block in ast.walk(tree)
        if isinstance(block, ast.If) and _is_type_checking(block.test)
        for statement in block.body
        for node in ast.walk(statement)
        if _imports_work_item(node)
    }
    every = {id(node) for node in ast.walk(tree) if _imports_work_item(node)}

    assert guarded
    assert every == guarded
