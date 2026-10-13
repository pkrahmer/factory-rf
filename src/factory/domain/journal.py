"""The journal of a work item: its visible entries in the body and their records in the state."""

# Postponed annotations let this module name the document while work_item imports JournalRecord.
from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date
from typing import TYPE_CHECKING, Literal, Self

from pydantic import BaseModel, ConfigDict, PositiveInt, field_validator, model_validator

from factory.domain.errors import WorkItemFormatError
from factory.domain.identifiers import Name
from factory.domain.sections import JOURNAL, Section, sections, split_lines

if TYPE_CHECKING:
    from factory.domain.work_item import WorkItemDocument, WorkItemState

HUMAN = "human"
FACTORY = "factory"

Speaker = Name
JournalKind = Literal[
    "created",
    "started",
    "result",
    "question",
    "comment",
    "close",
    "stall",
    "crash",
    "expiry",
    "move_back",
    "send_back",
    "done",
]

_ENTRY_START = re.compile(r"\d")


class JournalRecord(BaseModel):
    """One journal entry as the state lists it: its number, who spoke and what kind it is."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: PositiveInt
    speaker: Speaker
    kind: JournalKind


class NewEntry(BaseModel):
    """An entry to append: who speaks, what kind it is, its text and, for the human, its date."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    speaker: Speaker
    kind: JournalKind
    text: str
    on: date | None = None

    @field_validator("text")
    @classmethod
    def _stripped_and_not_blank(cls, text: str) -> str:
        stripped = text.strip()
        if not stripped:
            raise ValueError("the text of a journal entry must not be blank")
        return stripped

    @model_validator(mode="after")
    def _dated_exactly_when_human(self) -> Self:
        if self.speaker == HUMAN and self.on is None:
            raise ValueError("an entry of the human needs a date")
        if self.speaker != HUMAN and self.on is not None:
            raise ValueError(f"an entry of {self.speaker!r} carries no date")
        return self


def _prefix(number: int) -> str:
    return f"{number}. "


def render_entry(number: int, entry: NewEntry) -> str:
    """The visible entry: number, the human's date, speaker and text, continuation indented."""
    dated = "" if entry.on is None else f"{entry.on.isoformat()} "
    indent = " " * len(_prefix(number))
    first, *rest = entry.text.split("\n")
    continued = [indent + line if line else "" for line in rest]
    return "\n".join([f"{_prefix(number)}{dated}{entry.speaker}: {first}", *continued])


def _state_of(document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise WorkItemFormatError("the document has no state")
    return document.state


def _find_journal_section(body: str) -> Section | None:
    return next((section for section in sections(body) if section.heading == JOURNAL), None)


def _journal_section(body: str) -> Section:
    found = _find_journal_section(body)
    if found is None:
        raise WorkItemFormatError(f"missing section: ## {JOURNAL}")
    return found


def _last_text_line(lines: Sequence[str], section: Section) -> int:
    """The index of the section's last non-blank line, its heading when it has no text."""
    for index in range(section.end - 1, section.start, -1):
        if lines[index].strip():
            return index
    return section.start


def _joined(lines: Sequence[str], like: str) -> str:
    final_newline = "\n" if like.endswith("\n") else ""
    return "\n".join(lines) + final_newline


def append_entry(document: WorkItemDocument, entry: NewEntry) -> WorkItemDocument:
    """The document with the entry rendered into its journal section and recorded in its state."""
    state = _state_of(document)
    section = _journal_section(document.body)
    number = len(state.journal) + 1
    record = JournalRecord(number=number, speaker=entry.speaker, kind=entry.kind)
    lines = split_lines(document.body)
    last = _last_text_line(lines, section)
    rendered = split_lines(render_entry(number, entry))
    if last == section.start:
        rendered = ["", *rendered]
    body = _joined([*lines[: last + 1], *rendered, *lines[last + 1 :]], like=document.body)
    journal = [*state.journal, record]
    return document.model_copy(
        update={"state": state.model_copy(update={"journal": journal}), "body": body}
    )


def _entry_lines(lines: Sequence[str], section: Section, number: int) -> list[str]:
    content = lines[section.start + 1 : section.end]
    first = next(
        (index for index, line in enumerate(content) if line.startswith(_prefix(number))), None
    )
    if first is None:
        raise WorkItemFormatError(f"no journal entry {number}")
    following = (
        index for index in range(first + 1, len(content)) if _ENTRY_START.match(content[index])
    )
    entry = list(content[first : next(following, len(content))])
    while not entry[-1].strip():
        entry.pop()
    return entry


def entry_text(document: WorkItemDocument, number: int) -> str:
    """The text of entry `number` as it was given, for display only."""
    section = _journal_section(document.body)
    first, *rest = _entry_lines(split_lines(document.body), section, number)
    indent = " " * len(_prefix(number))
    unindented = [line.removeprefix(indent) for line in rest]
    return "\n".join([first.split(": ", 1)[-1], *unindented])


def last_record(
    document: WorkItemDocument, *, speaker: str | None = None, kind: JournalKind | None = None
) -> JournalRecord | None:
    """The last journal record that matches every filter given, or None."""
    matching = [
        record
        for record in _state_of(document).journal
        if (speaker is None or record.speaker == speaker) and (kind is None or record.kind == kind)
    ]
    return matching[-1] if matching else None


def _journal_block(body: str) -> list[str]:
    """The journal section from its heading to its last non-blank line."""
    lines = split_lines(body)
    section = _journal_section(body)
    return lines[section.start : _last_text_line(lines, section) + 1]


def restore_state_and_journal(
    current: WorkItemDocument, baseline: WorkItemDocument
) -> WorkItemDocument:
    """The current document with the baseline's whole state and journal section put back."""
    state = _state_of(baseline)
    block = _journal_block(baseline.body)
    lines = split_lines(current.body)
    found = _find_journal_section(current.body)
    if found is None:
        while lines and not lines[-1].strip():
            lines.pop()
        body = "\n".join([*lines, "", *block]) + "\n"
    else:
        last = _last_text_line(lines, found)
        body = _joined([*lines[: found.start], *block, *lines[last + 1 :]], like=current.body)
    return current.model_copy(update={"state": state, "body": body})
