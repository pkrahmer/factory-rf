"""The title, the `## ` sections and the fenced code blocks of a Markdown body."""

import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, NonNegativeInt

from factory.domain.errors import WorkItemFormatError

ACCEPTANCE_CRITERIA = "Acceptance criteria"
SMOKE_TEST = "Smoke test"
JOURNAL = "Journal"

_HEADING_PREFIX = "## "
_TITLE_PREFIX = "# "
_FENCE_OPENING = re.compile(r"^[ \t]*(`{3,}|~{3,})")


class Section(BaseModel):
    """A `## ` section: its heading text and the range of lines it covers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    start: NonNegativeInt
    end: NonNegativeInt


class CodeBlock(BaseModel):
    """A fenced code block: its opening line and its closing line, if it has one."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    start: NonNegativeInt
    end: NonNegativeInt | None


def split_lines(body: str) -> list[str]:
    """The lines of a body; a final newline adds no empty last line."""
    lines = body.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _closes(line: str, fence: str) -> bool:
    run = line.lstrip(" \t").rstrip()
    return len(run) >= len(fence) and run == fence[0] * len(run)


def _closing_index(lines: Sequence[str], opening: int, fence: str) -> int | None:
    for index in range(opening + 1, len(lines)):
        if _closes(lines[index], fence):
            return index
    return None


def code_blocks(lines: Sequence[str]) -> list[CodeBlock]:
    """The fenced code blocks among the lines, in order."""
    blocks: list[CodeBlock] = []
    index = 0
    while index < len(lines):
        opening = _FENCE_OPENING.match(lines[index])
        if opening is None:
            index += 1
            continue
        end = _closing_index(lines, index, opening.group(1))
        blocks.append(CodeBlock(start=index, end=end))
        if end is None:
            break
        index = end + 1
    return blocks


def _lines_outside_blocks(lines: Sequence[str]) -> list[int]:
    inside: set[int] = set()
    for block in code_blocks(lines):
        last = len(lines) - 1 if block.end is None else block.end
        inside.update(range(block.start, last + 1))
    return [index for index in range(len(lines)) if index not in inside]


def title(body: str) -> str | None:
    """The text of the first `# ` line outside the fenced blocks, if there is one."""
    lines = split_lines(body)
    for index in _lines_outside_blocks(lines):
        if lines[index].startswith(_TITLE_PREFIX):
            return lines[index][len(_TITLE_PREFIX) :].strip()
    return None


def sections(body: str) -> list[Section]:
    """The `## ` sections outside the fenced blocks, each up to the next heading."""
    lines = split_lines(body)
    starts = [
        index for index in _lines_outside_blocks(lines) if lines[index].startswith(_HEADING_PREFIX)
    ]
    ends = [*starts[1:], len(lines)] if starts else []
    return [
        Section(heading=lines[start][len(_HEADING_PREFIX) :].strip(), start=start, end=end)
        for start, end in zip(starts, ends, strict=True)
    ]


def _first_section(body: str, heading: str) -> Section | None:
    return next((found for found in sections(body) if found.heading == heading), None)


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _without_leading_blank_lines(lines: Sequence[str]) -> list[str]:
    first = next((index for index, line in enumerate(lines) if not _is_blank(line)), len(lines))
    return list(lines[first:])


def section_text(body: str, heading: str) -> str | None:
    """The text under the first section with this exact heading, blank edges trimmed."""
    found = _first_section(body, heading)
    if found is None:
        return None
    content = split_lines(body)[found.start + 1 : found.end]
    trimmed = _without_leading_blank_lines(content)
    return "\n".join(reversed(_without_leading_blank_lines(trimmed[::-1])))


def insert_paragraph(body: str, heading: str, paragraph: str) -> str:
    """The body with the paragraph placed first under the first section with this heading."""
    if _is_blank(paragraph):
        raise ValueError("the paragraph to insert is blank")
    found = _first_section(body, heading)
    if found is None:
        raise WorkItemFormatError(f"missing section: {_HEADING_PREFIX}{heading}")
    lines = split_lines(body)
    rest = _without_leading_blank_lines(lines[found.start + 1 :])
    inserted = [*lines[: found.start + 1], "", *split_lines(paragraph)]
    if rest:
        inserted += ["", *rest]
    final_newline = "\n" if body.endswith("\n") else ""
    return "\n".join(inserted) + final_newline


def required_sections(form: str) -> list[str]:
    """The headings of the project's story form, in order: every one is required."""
    return [found.heading for found in sections(form)]
