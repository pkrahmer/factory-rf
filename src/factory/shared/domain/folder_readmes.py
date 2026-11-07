"""The folders that must have a README, and the form such a README keeps."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from factory.shared.domain.documents import relative_link_targets
from factory.shared.domain.sections import code_blocks, lines_outside_blocks, split_lines

FOLDER_READMES: Final[tuple[str, ...]] = (
    "agents/README.md",
    "docs/README.md",
    "operator/bin/README.md",
    "operator/claude/README.md",
    "operator/job/README.md",
    "operator/lib/README.md",
    "operator/opencode/README.md",
    "operator/skill/README.md",
    "operator/template/README.md",
    "operator/vm/README.md",
    "security/README.md",
    "src/factory/README.md",
    "src/factory/agents/README.md",
    "src/factory/entry/README.md",
    "src/factory/hosting/README.md",
    "src/factory/machine/README.md",
    "src/factory/pipeline/README.md",
    "src/factory/shared/README.md",
    "src/factory/watching/README.md",
    "src/factory/work/README.md",
    "tests/README.md",
    "tests/support/README.md",
    "tests/guards/README.md",
)

OPENING_SENTENCES: Final = 2
SUBFOLDER_LINE_SENTENCES: Final = 1
SUBFOLDER_LINE_WORDS: Final = 25
BASE_LINES: Final = 10

_HEADING = re.compile(r"#+ ")
_TITLE = re.compile(r"# \S")
_SUBFOLDER_LINE = re.compile(r"- `(?P<name>[^`]+)/`(?P<rest>.*)")
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")


# Mutable, so that one pass over the lines can classify each line once.
@dataclass
class _Reading:
    named: list[str] = field(default_factory=list)
    long_lines: list[str] = field(default_factory=list)
    opening: list[str] = field(default_factory=list)
    free_lines: list[int] = field(default_factory=list)
    has_section: bool = False
    has_code_block: bool = False
    has_link: bool = False
    past_opening: bool = False


def _sentences(text: str) -> int:
    return len(_SENTENCE_END.findall(text))


def _read_subfolder_line(reading: _Reading, name: str, rest: str) -> None:
    reading.past_opening = True
    sentence = rest.strip()
    if not rest.startswith(" ") or not sentence.endswith("."):
        return
    reading.named.append(name)
    too_many_sentences = _sentences(sentence) > SUBFOLDER_LINE_SENTENCES
    if too_many_sentences or len(sentence.split()) > SUBFOLDER_LINE_WORDS:
        reading.long_lines.append(name)


def _read_line(reading: _Reading, number: int, line: str) -> None:
    if not line.strip():
        return
    if _HEADING.match(line):
        reading.has_section = True
        return
    subfolder = _SUBFOLDER_LINE.fullmatch(line)
    if relative_link_targets(line):
        reading.has_link = True
        if subfolder is None:
            reading.past_opening = True
            return
    if subfolder is not None:
        _read_subfolder_line(reading, subfolder["name"], subfolder["rest"])
    elif reading.past_opening:
        reading.free_lines.append(number)
    else:
        reading.opening.append(line)


def _read(readme: str) -> _Reading:
    lines = split_lines(readme)
    has_title = bool(lines) and _TITLE.match(lines[0]) is not None
    # Without a title there is no opening: every line, the first included, must fit the form.
    reading = _Reading(has_code_block=bool(code_blocks(lines)), past_opening=not has_title)
    for index in lines_outside_blocks(lines):
        if index > 0 or not has_title:
            _read_line(reading, index + 1, lines[index])
    return reading


def _subfolder_problems(folder: str, named: Sequence[str], subfolders: Sequence[str]) -> list[str]:
    not_named = (f"{folder}: {name}/ is not named" for name in subfolders if name not in named)
    missing = (f"{folder}: {name}/ does not exist" for name in named if name not in subfolders)
    return [*not_named, *missing]


def _form_problems(folder: str, readme: str, reading: _Reading, subfolders: int) -> list[str]:
    problems = [f"{folder}: {name}/ has a long line" for name in reading.long_lines]
    problems += [f"{folder}: line {number} is no part of the form" for number in reading.free_lines]
    if reading.has_section:
        problems.append(f"{folder}: has a section")
    if reading.has_code_block:
        problems.append(f"{folder}: has a code block")
    if _sentences(" ".join(reading.opening)) > OPENING_SENTENCES:
        problems.append(f"{folder}: the opening is longer than two sentences")
    if not reading.has_link:
        problems.append(f"{folder}: links to no guide")
    limit = BASE_LINES + subfolders
    if sum(1 for line in readme.splitlines() if line.strip()) > limit:
        problems.append(f"{folder}: is longer than {limit} lines")
    return problems


def readme_problems(folder: str, readme: str | None, subfolders: Sequence[str]) -> list[str]:
    """What a folder's README and its subfolders disagree on, one line each, sorted."""
    if readme is None:
        return [f"{folder}: no README.md"]
    reading = _read(readme)
    return sorted(
        [
            *_subfolder_problems(folder, reading.named, subfolders),
            *_form_problems(folder, readme, reading, len(subfolders)),
        ]
    )
