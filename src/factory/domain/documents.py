"""The check of the four documents and the guide's other files: sections, rows, phrases, words."""

import re
from collections.abc import Mapping, Sequence
from typing import Final

from pydantic import BaseModel, ConfigDict

from factory.domain.fault_paths import FAULT_PATHS
from factory.domain.kill_point_cases import KILL_POINT_CASES
from factory.domain.sections import lines_outside_blocks, sections, split_lines
from factory.domain.stop_table import STOP_TABLE, Destination

README: Final = "README.md"
OPERATOR_GUIDE: Final = "docs/operator-guide.md"
PROJECT_GUIDE_FOLDER: Final = "docs/project-guide"
PROJECT_GUIDE: Final = f"{PROJECT_GUIDE_FOLDER}/README.md"
DECISION_LOG: Final = "docs/decisions.md"
DOCUMENT_PATHS: Final = (README, OPERATOR_GUIDE, PROJECT_GUIDE, DECISION_LOG)
OPERATOR_GUIDE_SECTIONS: Final = ("Install", "Configuration", "The stops")
PROJECT_GUIDE_SECTIONS: Final = ("Kill points", "Fault-injection paths")
REPLACED_SECTION: Final = "Replaced from v1"
REPLACED_PHRASES: Final = (
    "--follow",
    "factory-last-line",
    "tasks/.gitkeep",
    "factory-tick.lock",
    "factory-run.json",
    "recover_dirty_tree",
    "lease plus ten minutes",
    "local branch first",
    "run record",
)
GLOSSARY_FORBIDDEN: Final = (
    "ticket",
    "tickets",
    "lane",
    "lanes",
    "stage table",
    "stages.yml",
    "promote",
    "promoted",
    "acceptor",
    "demonstration",
    "control surface",
    "hardening",
    "memo",
    "lease_minutes",
    "max_attempts",
    "max_rounds",
    "drafts/",
    "ongoing/",
)

_DESTINATION_WORDS: Final[Mapping[Destination, str]] = {
    "health_status": "health status",
    "pull_request": "pull request",
    "none": "no stop",
}
_TABLE_ROW_PREFIX = "|"
_GUIDE_FILE_NAME = re.compile(r"[^/]+\.md")
# A word character or a hyphen: next to an entry, it makes the entry part of a longer word.
_WORD_EDGE = r"[\w-]"


class DocumentFinding(BaseModel):
    """One thing a document lacks or says that it must not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    message: str


def _table_rows(text: str) -> list[str]:
    lines = split_lines(text)
    return [
        lines[index]
        for index in lines_outside_blocks(lines)
        if lines[index].startswith(_TABLE_ROW_PREFIX)
    ]


def _has_row(rows: Sequence[str], *needles: str) -> bool:
    return any(all(needle in row.lower() for needle in needles) for row in rows)


def _missing_sections(text: str, required: Sequence[str]) -> list[str]:
    present = {found.heading for found in sections(text)}
    return [f"section '{name}' is missing" for name in required if name not in present]


def _operator_guide_rows(text: str) -> list[str]:
    rows = _table_rows(text)
    return [
        f"stop '{row.id}' has no table row with its destination"
        for row in STOP_TABLE
        if not _has_row(rows, f"`{row.id.lower()}`", _DESTINATION_WORDS[row.destination])
    ]


def _project_guide_rows(text: str) -> list[str]:
    rows = _table_rows(text)
    messages = [
        f"kill point case '{case.id}' has no table row"
        for case in KILL_POINT_CASES
        if not _has_row(rows, f"`{case.id.lower()}`")
    ]
    messages += [
        f"fault-injection path {path.number} has no table row naming '{path.test}'"
        for path in FAULT_PATHS
        if not _has_row(rows, f"`{path.test.lower()}`")
    ]
    return messages


def _without_replaced_section(text: str) -> str:
    exempt: set[int] = set()
    for found in sections(text):
        if found.heading == REPLACED_SECTION:
            exempt.update(range(found.start, found.end))
    lines = split_lines(text)
    return "\n".join(line for index, line in enumerate(lines) if index not in exempt)


def _uses_word(text: str, entry: str) -> bool:
    after = f"(?!{_WORD_EDGE})" if entry[-1].isalpha() else ""
    pattern = f"(?<!{_WORD_EDGE}){re.escape(entry)}{after}"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _wording(text: str) -> list[str]:
    checked = _without_replaced_section(text)
    lowered = checked.lower()
    messages = [
        f"describes a replaced behaviour: '{phrase}'"
        for phrase in REPLACED_PHRASES
        if phrase in lowered
    ]
    messages += [
        f"uses the v1 word '{entry}'" for entry in GLOSSARY_FORBIDDEN if _uses_word(checked, entry)
    ]
    return messages


def _messages(document: str, text: str | None) -> list[str]:
    if text is None:
        return ["missing"]
    if not text.strip():
        return ["empty"]
    if document == DECISION_LOG:
        return [] if sections(text) else ["no decision recorded"]
    if document == OPERATOR_GUIDE:
        return [
            *_missing_sections(text, OPERATOR_GUIDE_SECTIONS),
            *_operator_guide_rows(text),
            *_wording(text),
        ]
    if document == PROJECT_GUIDE:
        return [
            *_missing_sections(text, PROJECT_GUIDE_SECTIONS),
            *_project_guide_rows(text),
            *_wording(text),
        ]
    return _wording(text)


def is_guide_file(path: str) -> bool:
    """Whether `path` is a file of the project guide beside its index: `<folder>/<name>.md`."""
    folder, _, name = path.rpartition("/")
    return (
        folder == PROJECT_GUIDE_FOLDER
        and _GUIDE_FILE_NAME.fullmatch(name) is not None
        and path != PROJECT_GUIDE
    )


def check_documents(texts: Mapping[str, str | None]) -> list[DocumentFinding]:
    """The findings of the four documents, in their order, then of the guide's other files.

    An absent key among the four documents is a missing document; a guide file is checked for its
    words only, in path order, and every other key is ignored.
    """
    guide_files = sorted(path for path in texts if is_guide_file(path))
    documents = [*DOCUMENT_PATHS, *guide_files]
    return [
        DocumentFinding(document=document, message=message)
        for document in documents
        for message in _messages(document, texts.get(document))
    ]
