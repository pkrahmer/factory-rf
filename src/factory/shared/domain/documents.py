"""The check of the documents and the project guide's files: sections, rows, phrases, words."""

import posixpath
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict

from factory.pipeline.domain.fault_paths import FAULT_PATHS
from factory.pipeline.domain.stop_table import STOP_TABLE, Destination
from factory.shared.domain.kill_point_cases import KILL_POINT_CASES
from factory.shared.domain.sections import lines_outside_blocks, sections, split_lines

README: Final = "README.md"
OPERATOR_GUIDE_FOLDER: Final = "docs/operator-guide"
OPERATOR_GUIDE: Final = f"{OPERATOR_GUIDE_FOLDER}/README.md"
OPERATOR_INSTALL: Final = f"{OPERATOR_GUIDE_FOLDER}/install.md"
OPERATOR_STOPS: Final = f"{OPERATOR_GUIDE_FOLDER}/stops.md"
OPERATOR_GUIDE_FILES: Final = (
    OPERATOR_INSTALL,
    f"{OPERATOR_GUIDE_FOLDER}/agent-runtime.md",
    f"{OPERATOR_GUIDE_FOLDER}/machine.md",
    f"{OPERATOR_GUIDE_FOLDER}/site.md",
    f"{OPERATOR_GUIDE_FOLDER}/cloud-run.md",
    f"{OPERATOR_GUIDE_FOLDER}/health.md",
    OPERATOR_STOPS,
    f"{OPERATOR_GUIDE_FOLDER}/pipeline.md",
    f"{OPERATOR_GUIDE_FOLDER}/records.md",
    f"{OPERATOR_GUIDE_FOLDER}/work-items.md",
)
PROJECT_GUIDE_FOLDER: Final = "docs/project-guide"
PROJECT_GUIDE: Final = f"{PROJECT_GUIDE_FOLDER}/README.md"
DECISION_LOG: Final = "docs/decisions.md"
DOCUMENT_PATHS: Final = (
    README,
    OPERATOR_GUIDE,
    *OPERATOR_GUIDE_FILES,
    PROJECT_GUIDE,
    DECISION_LOG,
)
OPERATOR_GUIDE_SECTIONS: Final = ("Install", "Configuration", "The stops")
_OPERATOR_SECTION_FILES: Final[Mapping[str, str]] = {
    "Install": OPERATOR_INSTALL,
    "Configuration": OPERATOR_INSTALL,
    "The stops": OPERATOR_STOPS,
}
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
UNCHECKED_SECTIONS: Final = ("Replaced from v1", "Replaced in v1.2")
_BACKTICKED = re.compile(r"`([^`]+)`")
_LINK_TARGET = re.compile(r"\]\(([^)\s]+)")
_MODULE_NAME = re.compile(r"factory(\.\w+)+")
_FILE_EXTENSION = re.compile(r".+\.\w+")
_PLACEHOLDER_OR_GLOB = ("<", ">", "*")
_WEB_ADDRESS = "://"
_FRAGMENT = "#"
_PATH_SEPARATOR = "/"
_HOME = "~"
_MAIL_PREFIX = "mailto:"

ReferenceKind = Literal["module", "path", "link"]


class DocumentFinding(BaseModel):
    """One thing a document lacks or says that it must not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    message: str


class Reference(BaseModel):
    """A name, path or link target one line of a document names, which must exist."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    line: int
    name: str
    kind: ReferenceKind


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


def _stop_rows(text: str) -> list[str]:
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


def _decision_log_messages(text: str) -> list[str]:
    return [] if sections(text) else ["no decision recorded"]


def _operator_sections(document: str) -> list[str]:
    return [name for name in OPERATOR_GUIDE_SECTIONS if _OPERATOR_SECTION_FILES[name] == document]


def _install_messages(text: str) -> list[str]:
    return [*_missing_sections(text, _operator_sections(OPERATOR_INSTALL)), *_wording(text)]


def _stops_messages(text: str) -> list[str]:
    return [
        *_missing_sections(text, _operator_sections(OPERATOR_STOPS)),
        *_stop_rows(text),
        *_wording(text),
    ]


def _project_guide_messages(text: str) -> list[str]:
    return [
        *_missing_sections(text, PROJECT_GUIDE_SECTIONS),
        *_project_guide_rows(text),
        *_wording(text),
    ]


_RULES: Final[Mapping[str, Callable[[str], list[str]]]] = {
    DECISION_LOG: _decision_log_messages,
    OPERATOR_INSTALL: _install_messages,
    OPERATOR_STOPS: _stops_messages,
    PROJECT_GUIDE: _project_guide_messages,
}


def _messages(document: str, text: str | None) -> list[str]:
    if text is None:
        return ["missing"]
    if not text.strip():
        return ["empty"]
    return _RULES.get(document, _wording)(text)


def is_guide_file(path: str) -> bool:
    """Whether `path` is a file of the project guide beside its index: `<folder>/<name>.md`."""
    folder, _, name = path.rpartition("/")
    return (
        folder == PROJECT_GUIDE_FOLDER
        and _GUIDE_FILE_NAME.fullmatch(name) is not None
        and path != PROJECT_GUIDE
    )


def check_documents(texts: Mapping[str, str | None]) -> list[DocumentFinding]:
    """The findings of the documents, in their order, then of the project guide's other files.

    An absent key among the documents is a missing document; a guide file is checked for its
    words only, in path order, and every other key is ignored.
    """
    guide_files = sorted(path for path in texts if is_guide_file(path))
    documents = [*DOCUMENT_PATHS, *guide_files]
    return [
        DocumentFinding(document=document, message=message)
        for document in documents
        for message in _messages(document, texts.get(document))
    ]


def _is_path(text: str, top_level: frozenset[str]) -> bool:
    if _PATH_SEPARATOR not in text or any(character.isspace() for character in text):
        return False
    if text.startswith((_PATH_SEPARATOR, _HOME)) or _WEB_ADDRESS in text:
        return False
    segments = text.rstrip(_PATH_SEPARATOR).split(_PATH_SEPARATOR)
    return segments[0] in top_level or _FILE_EXTENSION.fullmatch(segments[-1]) is not None


def _backticked_kind(text: str, top_level: frozenset[str]) -> ReferenceKind | None:
    if any(marker in text for marker in _PLACEHOLDER_OR_GLOB):
        return None
    if _MODULE_NAME.fullmatch(text) is not None:
        return "module"
    if _is_path(text, top_level):
        return "path"
    return None


def _link_name(document: str, target: str) -> str | None:
    if target.startswith((_FRAGMENT, _PATH_SEPARATOR, _MAIL_PREFIX)) or _WEB_ADDRESS in target:
        return None
    if any(marker in target for marker in _PLACEHOLDER_OR_GLOB):
        return None
    relative = target.split(_FRAGMENT, 1)[0]
    return posixpath.normpath(posixpath.join(posixpath.dirname(document), relative))


def _line_references(
    document: str, number: int, line: str, top_level: frozenset[str]
) -> list[Reference]:
    references: list[Reference] = []
    for text in _BACKTICKED.findall(line):
        kind = _backticked_kind(text, top_level)
        if kind is not None:
            references.append(Reference(document=document, line=number, name=text, kind=kind))
    for target in _LINK_TARGET.findall(line):
        name = _link_name(document, target)
        if name is not None:
            references.append(Reference(document=document, line=number, name=name, kind="link"))
    return references


def _checked_lines(text: str) -> list[int]:
    exempt: set[int] = set()
    for found in sections(text):
        if found.heading in UNCHECKED_SECTIONS:
            exempt.update(range(found.start, found.end))
    lines = split_lines(text)
    return [index for index in lines_outside_blocks(lines) if index not in exempt]


def named_references(document: str, text: str, top_level: frozenset[str]) -> list[Reference]:
    """The backticked `factory.` names and repository paths and the relative links of a document.

    Fenced blocks and the sections under `UNCHECKED_SECTIONS` are left out; a path counts
    when its first segment is in `top_level` or its last segment has a file extension, and
    a link's target is resolved against the document's folder, without its fragment.
    """
    lines = split_lines(text)
    return [
        reference
        for index in _checked_lines(text)
        for reference in _line_references(document, index + 1, lines[index], top_level)
    ]


def unresolved(references: list[Reference], exists: Callable[[Reference], bool]) -> list[str]:
    """One finding per reference that `exists` refuses, in their order.

    Each reads `<document>:<line>: <name> does not exist`.
    """
    return [
        f"{reference.document}:{reference.line}: {reference.name} does not exist"
        for reference in references
        if not exists(reference)
    ]
