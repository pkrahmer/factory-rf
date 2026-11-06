"""The check of the documents and the guide's files: sections, rows, words, names, examples."""

import posixpath
import re
from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict

from factory.pipeline.domain.fault_paths import FAULT_PATHS
from factory.pipeline.domain.stop_table import STOP_TABLE, Destination
from factory.shared.domain.kill_point_cases import KILL_POINT_CASES
from factory.shared.domain.sections import (
    code_blocks,
    lines_outside_blocks,
    opening_fence,
    sections,
    split_lines,
)
from factory.shared.domain.settings import SettingDoc

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
UNCHECKED_SECTIONS: Final = (REPLACED_SECTION, "Replaced in v1.2")
_BACKTICKED = re.compile(r"`([^`]+)`")
_LINK_TARGET = re.compile(r"\]\(([^)\s]+)")
_MODULE_NAME = re.compile(r"factory(\.\w+)+")
_FILE_EXTENSION = re.compile(r".+\.\w+")
# A dotted `factory.` name that ends in one of these is a file, such as `factory.env`.
_FILE_NAME_EXTENSIONS = (
    ".env",
    ".service",
    ".yml",
    ".yaml",
    ".json",
    ".jsonl",
    ".toml",
    ".md",
    ".txt",
    ".log",
)
_SHELL_EXPRESSION_MARK = "$"
_NODE_ID_SEPARATOR = "::"
_PLACEHOLDER_OR_GLOB = ("<", ">", "*")
_WEB_ADDRESS = "://"
_FRAGMENT = "#"
_PATH_SEPARATOR = "/"
_ADDRESS_SEPARATOR = ":"
_HOME = "~"
_MAIL_PREFIX = "mailto:"
SETTINGS_SECTION: Final = "Configuration"
_SETTINGS_FIRST_COLUMNS = ("Name", "Variable")
_DEFAULT_COLUMN = "Default"
_NO_DEFAULT_CELLS = ("", "none")
REFUSALS_HEADING: Final = "The refusals"
_REFUSAL_FIRST_COLUMN = "Refusal"
_SHORTEST_CHECKED_PIECE = 3
_HEADING_MARK = "#"
# A pipe escaped with a backslash belongs to its cell's text.
_CELL_SEPARATOR = re.compile(r"(?<!\\)\|")
_PLACEHOLDER = re.compile(r"<[^>]*>")

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


class GuideTable(BaseModel):
    """A Markdown table of a guide: the nearest heading above it, its header and its rows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def _is_table_row(line: str) -> bool:
    return line.startswith(_TABLE_ROW_PREFIX)


def _table_rows(text: str) -> list[str]:
    lines = split_lines(text)
    return [lines[index] for index in lines_outside_blocks(lines) if _is_table_row(lines[index])]


def _cells(row: str) -> tuple[str, ...]:
    inner = row.strip().removeprefix(_TABLE_ROW_PREFIX).removesuffix(_TABLE_ROW_PREFIX)
    return tuple(cell.strip() for cell in _CELL_SEPARATOR.split(inner))


def _guide_table(heading: str, rows: Sequence[str]) -> GuideTable:
    # The second row of a Markdown table is the line that separates the header from the body.
    return GuideTable(
        heading=heading, header=_cells(rows[0]), rows=tuple(_cells(row) for row in rows[2:])
    )


def guide_tables(text: str, section: str) -> list[GuideTable]:
    """The tables inside the `## ` section `section` and its subsections, in their order.

    Each carries the nearest heading above it; fenced blocks are left out.
    """
    lines = split_lines(text)
    inside = _section_lines(text, (section,))
    tables: list[GuideTable] = []
    heading = section
    current: list[str] = []
    for index in lines_outside_blocks(lines):
        if index not in inside:
            continue
        line = lines[index]
        if _is_table_row(line):
            current.append(line)
            continue
        if current:
            tables.append(_guide_table(heading, current))
            current = []
        if line.startswith(_HEADING_MARK):
            heading = line.lstrip(_HEADING_MARK).strip()
    if current:
        tables.append(_guide_table(heading, current))
    return tables


def _backticked_or_plain(cell: str) -> str:
    quoted = _BACKTICKED.search(cell)
    return cell if quoted is None else quoted.group(1)


def _settings_tables(guide_tables: list[GuideTable]) -> list[GuideTable]:
    return [
        table
        for table in guide_tables
        if table.header and table.header[0] in _SETTINGS_FIRST_COLUMNS
    ]


def _default_findings(table: GuideTable, settings: Mapping[str, SettingDoc]) -> list[str]:
    if _DEFAULT_COLUMN not in table.header:
        return []
    column = table.header.index(_DEFAULT_COLUMN)
    messages: list[str] = []
    for row in table.rows:
        setting = settings.get(_backticked_or_plain(row[0]))
        if setting is None or column >= len(row):
            continue
        cell = row[column]
        written = None if cell in _NO_DEFAULT_CELLS else cell
        if written != setting.default:
            messages.append(
                f"setting {setting.name} has the default {cell!r} in the guide, "
                f"{setting.default!r} in the settings code"
            )
    return messages


def settings_findings(
    guide_tables: list[GuideTable], settings: tuple[SettingDoc, ...]
) -> list[str]:
    """The settings the guide's settings tables and `settings` disagree on, one finding each.

    A table counts when its first column is `Name` or `Variable`. A setting the code reads
    that no such table names, a name no setting has, and, in a table with a `Default`
    column, a default other than the setting's (`None` written empty or `none`) are findings.
    Without such a table there is nothing to compare, and no finding.
    """
    tables = _settings_tables(guide_tables)
    if not tables:
        return []
    by_name = {setting.name: setting for setting in settings}
    named = [_backticked_or_plain(row[0]) for table in tables for row in table.rows if row]
    messages = [
        f"setting {setting.name} is read by the settings code and missing from the guide"
        for setting in settings
        if setting.name not in named
    ]
    messages += [
        f"setting {name} is named by the guide and not read by the settings code"
        for name in named
        if name not in by_name
    ]
    for table in tables:
        messages += _default_findings(table, by_name)
    return messages


def _is_refusal_table(table: GuideTable) -> bool:
    return (
        table.heading == REFUSALS_HEADING
        and bool(table.header)
        and table.header[0] == _REFUSAL_FIRST_COLUMN
    )


def _quoted_refusal(row: tuple[str, ...]) -> str | None:
    if not row:
        return None
    quoted = _BACKTICKED.search(row[0])
    return None if quoted is None else quoted.group(1)


def _is_held(refusal: str, settings_source: str) -> bool:
    pieces = _PLACEHOLDER.split(refusal)
    return all(
        piece in settings_source for piece in pieces if len(piece) >= _SHORTEST_CHECKED_PIECE
    )


def refusal_findings(guide_tables: list[GuideTable], settings_source: str) -> list[str]:
    """The refusal texts the guide quotes that `settings_source` does not hold, one each.

    Only tables headed `The refusals` whose first column is `Refusal` count; a refusal is
    the backticked text of its first cell. Its `<placeholder>`s are cut out, and every
    remaining piece of three characters or more must occur in the source.
    """
    refusals = [
        _quoted_refusal(row)
        for table in guide_tables
        if _is_refusal_table(table)
        for row in table.rows
    ]
    return [
        f"refusal `{refusal}` is not held by the settings code"
        for refusal in refusals
        if refusal is not None and not _is_held(refusal, settings_source)
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


def _section_lines(text: str, headings: Sequence[str]) -> set[int]:
    lines: set[int] = set()
    for found in sections(text):
        if found.heading in headings:
            lines.update(range(found.start, found.end))
    return lines


def _without_replaced_section(text: str) -> str:
    exempt = _section_lines(text, (REPLACED_SECTION,))
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


def _is_address(text: str) -> bool:
    # A web address (`https://host/x`) or a scp-style git address (`git@host:owner/name.git`)
    # names its scheme or host before the first `/`.
    before_first_separator = text.split(_PATH_SEPARATOR, 1)[0]
    return _ADDRESS_SEPARATOR in before_first_separator


def _is_path(text: str, top_level: frozenset[str]) -> bool:
    if _PATH_SEPARATOR not in text or any(character.isspace() for character in text):
        return False
    if text.startswith((_PATH_SEPARATOR, _HOME)) or _is_address(text):
        return False
    segments = text.rstrip(_PATH_SEPARATOR).split(_PATH_SEPARATOR)
    return segments[0] in top_level or _FILE_EXTENSION.fullmatch(segments[-1]) is not None


def _is_module_name(text: str) -> bool:
    return _MODULE_NAME.fullmatch(text) is not None and not text.endswith(_FILE_NAME_EXTENSIONS)


def _backticked_kind(text: str, top_level: frozenset[str]) -> ReferenceKind | None:
    if any(marker in text for marker in _PLACEHOLDER_OR_GLOB):
        return None
    if _is_module_name(text):
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
    for quoted in _BACKTICKED.findall(line):
        if _SHELL_EXPRESSION_MARK in quoted:
            continue
        # A pytest node id names its test file before the separator.
        text = quoted.split(_NODE_ID_SEPARATOR, 1)[0]
        kind = _backticked_kind(text, top_level)
        if kind is not None:
            references.append(Reference(document=document, line=number, name=text, kind=kind))
    for target in _LINK_TARGET.findall(line):
        name = _link_name(document, target)
        if name is not None:
            references.append(Reference(document=document, line=number, name=name, kind="link"))
    return references


def _checked_lines(text: str) -> list[int]:
    exempt = _section_lines(text, UNCHECKED_SECTIONS)
    lines = split_lines(text)
    return [index for index in lines_outside_blocks(lines) if index not in exempt]


def named_references(document: str, text: str, top_level: frozenset[str]) -> list[Reference]:
    """The backticked `factory.` names and repository paths and the relative links of a document.

    Fenced blocks and the sections under `UNCHECKED_SECTIONS` are left out; a path counts
    when its first segment is in `top_level` or its last segment has a file extension, and
    a link's target is resolved against the document's folder, without its fragment. A
    backticked text that holds `$` is a shell expression and left out, a pytest node id
    names the path before its `::`, a text whose first `:` comes before its first `/`, such
    as `git@host:owner/name.git`, is an address and no path, and a dotted `factory.` name
    that ends in a file extension, such as `factory.env` or `factory.log`, is a file name
    and no module.
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


CHECKED_DOCUMENTS: Final = "docs/checked-documents.txt"
_COMMENT_MARK = "#"


class GatedFinding(BaseModel):
    """A finding of the name, settings or example check, which blocks only in a listed document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    line: str


class SplitFindings(BaseModel):
    """The lines that fail the check, and those it only reports."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    blocking: list[str]
    reported: list[str]


def read_checked_documents(text: str) -> list[str]:
    """The paths of the list of checked documents, in order; blank and `#` lines give none."""
    stripped = (line.strip() for line in split_lines(text))
    return [line for line in stripped if line and not line.startswith(_COMMENT_MARK)]


def checked_list_findings(listed: Sequence[str], documents: Collection[str]) -> list[str]:
    """One finding per listed path that is none of `documents`, the documents the check reads."""
    return [
        f"{CHECKED_DOCUMENTS}: {path} is no document of the check"
        for path in listed
        if path not in documents
    ]


def split_findings(findings: Sequence[GatedFinding], checked: Collection[str]) -> SplitFindings:
    """The findings in a `checked` document block, the others are reported; order is kept."""
    return SplitFindings(
        blocking=[finding.line for finding in findings if finding.document in checked],
        reported=[finding.line for finding in findings if finding.document not in checked],
    )


CONSOLE: Final = "console"
DEFAULT_FIXTURE: Final = "checkout"
INSTANCE_FIXTURE: Final = "instance"
UNRUN_MARKS: Final = ("vm", "github", "model")
SUITE: Final = "suite"
ANY_LINES: Final = "..."
_COMMAND_PROMPT = "$ "
_FIXTURE_OPTION = "fixture="
_SUITE_TARGETS = ("make check", "make test")
_RUNNER_PREFIX = ("uv", "run")
_PYTEST = "pytest"
_LIST_OPERATORS = re.compile(r"\|\||&&|[|;&]")
_REDIRECTION = re.compile(r"\d*[<>]+&?\d*")
_OPTION_MARK = "-"
_TEST_SELECTOR = "::"
_TEST_FILE_SUFFIX = ".py"


class Command(BaseModel):
    """One `$ ` line of a `console` block: its line, the command and the lines it prints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    line: int
    command: str
    expected: list[str]


class Example(BaseModel):
    """A runnable `console` block: its opening line, the fixture it runs on, its commands."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    line: int
    fixture: str
    commands: list[Command]


class Skipped(BaseModel):
    """A `console` block that is not run: its opening line and why (`vm`, `suite`, ...)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    line: int
    kind: str


class Examples(BaseModel):
    """The `console` blocks of one document, the runnable ones and the skipped ones, in order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    runnable: list[Example]
    skipped: list[Skipped]


def _info_words(line: str) -> list[str]:
    fence = opening_fence(line)
    if fence is None:
        return []
    return line.lstrip(" \t")[len(fence) :].split()


def _commands(lines: Sequence[str], first: int) -> list[Command]:
    prompts = [index for index, line in enumerate(lines) if line.startswith(_COMMAND_PROMPT)]
    ends = [*prompts[1:], len(lines)]
    return [
        Command(
            line=first + start,
            command=lines[start][len(_COMMAND_PROMPT) :],
            expected=list(lines[start + 1 : end]),
        )
        for start, end in zip(prompts, ends, strict=True)
    ]


def _simple_commands(command: str) -> list[tuple[str, ...]]:
    # A redirection such as `2>&1` holds `&`, so it goes before the line is split at operators.
    without_redirections = _REDIRECTION.sub(" ", command)
    return [tuple(part.split()) for part in _LIST_OPERATORS.split(without_redirections)]


def _names_a_test_file(word: str) -> bool:
    if word.startswith(_OPTION_MARK):
        return False
    return word.split(_TEST_SELECTOR, 1)[0].endswith(_TEST_FILE_SUFFIX)


def _simple_command_runs_the_suite(words: tuple[str, ...]) -> bool:
    if words[: len(_RUNNER_PREFIX)] == _RUNNER_PREFIX:
        words = words[len(_RUNNER_PREFIX) :]
    if " ".join(words[:2]) in _SUITE_TARGETS:
        return True
    if not words or words[0] != _PYTEST:
        return False
    return not any(_names_a_test_file(word) for word in words[1:])


def runs_the_suite(command: str) -> bool:
    """Whether `command` runs the whole test suite: `make check`, `make test`, a bare `pytest`.

    Every simple command of the line counts. A `pytest` runs the suite unless one of its
    words names a test file; a folder, an option or an option's value names none.
    """
    return any(_simple_command_runs_the_suite(words) for words in _simple_commands(command))


def _skipped_kind(options: Sequence[str], commands: Sequence[Command]) -> str | None:
    marks = [option for option in options if option in UNRUN_MARKS]
    if marks:
        return marks[0]
    if any(runs_the_suite(command.command) for command in commands):
        return SUITE
    return None


def _fixture(options: Sequence[str]) -> str:
    named = [option for option in options if option.startswith(_FIXTURE_OPTION)]
    return named[0].removeprefix(_FIXTURE_OPTION) if named else DEFAULT_FIXTURE


def examples(text: str) -> Examples:
    """The `console` blocks of a document, in order; lines are counted from 1.

    A block's `$ ` lines are its commands and the lines below each its expected output. A
    block marked `vm`, `github` or `model`, or one with a command that runs the suite, is
    skipped with that kind; any other runs on the fixture its `fixture=` names, `checkout`
    when it names none.
    """
    lines = split_lines(text)
    runnable: list[Example] = []
    skipped: list[Skipped] = []
    for block in code_blocks(lines):
        words = _info_words(lines[block.start])
        if not words or words[0] != CONSOLE:
            continue
        end = len(lines) if block.end is None else block.end
        line = block.start + 1
        commands = _commands(lines[block.start + 1 : end], line + 1)
        options = words[1:]
        kind = _skipped_kind(options, commands)
        if kind is None:
            runnable.append(Example(line=line, fixture=_fixture(options), commands=commands))
        else:
            skipped.append(Skipped(line=line, kind=kind))
    return Examples(runnable=runnable, skipped=skipped)


def _line_matches(expected: str, actual: str) -> bool:
    pieces = (re.escape(piece) for piece in _PLACEHOLDER.split(expected))
    return re.fullmatch(".*".join(pieces), actual) is not None


def _with_any_lines_passed(expected: Sequence[str], states: set[int]) -> set[int]:
    # `...` may stand for no line, so a state before it is also a state after it.
    closed = set(states)
    pending = list(states)
    while pending:
        state = pending.pop()
        if state < len(expected) and expected[state] == ANY_LINES and state + 1 not in closed:
            closed.add(state + 1)
            pending.append(state + 1)
    return closed


def _next_states(expected: Sequence[str], states: set[int], actual: str) -> set[int]:
    following: set[int] = set()
    for state in states:
        if state >= len(expected):
            continue
        if expected[state] == ANY_LINES:
            following.add(state)
        elif _line_matches(expected[state], actual):
            following.add(state + 1)
    return _with_any_lines_passed(expected, following)


def first_difference(expected: Sequence[str], actual: Sequence[str]) -> int | None:
    """The index of the first line of `actual` that `expected` cannot match, or `None`.

    When every line matches but `expected` wants more, the index is `len(actual)`.
    """
    states = _with_any_lines_passed(expected, {0})
    for index, line in enumerate(actual):
        states = _next_states(expected, states, line)
        if not states:
            return index
    return None if len(expected) in states else len(actual)


def matches(expected: Sequence[str], actual: Sequence[str]) -> bool:
    """Whether `actual` is `expected` line by line, with its two placeholders.

    A line `...` stands for any number of lines, and `<placeholder>` for any text in a line.
    """
    return first_difference(expected, actual) is None
