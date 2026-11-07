"""The references of a document to a heading of another page, and those the page lacks."""

import re
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.shared.domain.documents import checked_lines, link_name
from factory.shared.domain.sections import lines_outside_blocks, split_lines

_REFERENCE = re.compile(
    r"(?:\*(?=\S)(?P<italic>[^*]+?)(?<=\S)\*|\"(?=\S)(?P<quoted>[^\"]+?)(?<=\S)\")"
    r"[),]?\s+(?:in|of)\s+\[[^\]]*\]\((?P<target>[^)\s]+)\)"
)
_CODE_MARKS = re.compile(r"[`*]")
_HEADING_LINE = re.compile(r"#+\s+(?P<heading>.+)")
_FRAGMENT = "#"
_DOCUMENT_SUFFIX = ".md"


class HeadingReference(BaseModel):
    """A reference on one line of a document to a heading of another page."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    line: PositiveInt
    heading: str
    target: str


def _without_code_marks(text: str) -> str:
    return _CODE_MARKS.sub("", text).strip()


def _target(document: str, link: str) -> str | None:
    # A link with an anchor already names its section; the anchor is not checked here.
    if _FRAGMENT in link or not link.endswith(_DOCUMENT_SUFFIX):
        return None
    target = link_name(document, link)
    return None if target == document else target


def _line_references(document: str, number: int, line: str) -> list[HeadingReference]:
    references: list[HeadingReference] = []
    for found in _REFERENCE.finditer(line):
        target = _target(document, found.group("target"))
        if target is None:
            continue
        heading = found.group("italic") or found.group("quoted")
        references.append(
            HeadingReference(
                document=document,
                line=number,
                heading=_without_code_marks(heading),
                target=target,
            )
        )
    return references


def heading_references(document: str, text: str) -> list[HeadingReference]:
    """The references of one document to a heading of another page, with their lines.

    A reference is a heading in italics or double quotes, an optional `)` or `,`, then
    `in` or `of` and a relative link to a `.md` file without an anchor; the link is
    resolved against the document's folder. The lines the name check leaves out are left
    out here too.
    """
    lines = split_lines(text)
    return [
        reference
        for index in checked_lines(text)
        for reference in _line_references(document, index + 1, lines[index])
    ]


def page_headings(text: str) -> set[str]:
    """The headings of one page's heading lines, with only their backticks and asterisks removed."""
    lines = split_lines(text)
    matches = (_HEADING_LINE.fullmatch(lines[index]) for index in lines_outside_blocks(lines))
    return {_without_code_marks(found.group("heading")) for found in matches if found is not None}


def unresolved_headings(
    references: list[HeadingReference], headings: Callable[[str], set[str] | None]
) -> list[str]:
    """One finding per reference whose heading the linked page does not have.

    `headings` gives the linked page's headings, or `None` for a page that is no document
    of the check, which gives no finding. Each reads
    `<document>:<line>: <heading> is no heading of <target>`.
    """
    findings: list[str] = []
    for reference in references:
        page = headings(reference.target)
        if page is not None and reference.heading not in page:
            findings.append(
                f"{reference.document}:{reference.line}: "
                f"{reference.heading} is no heading of {reference.target}"
            )
    return findings
