"""The check of a story's form: one finding for each rule the story breaks."""

import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.domain.identifiers import (
    feature_of,
    is_acceptance,
    parse_feature_directory_name,
    parse_work_item_file_name,
)
from factory.domain.paths import (
    FEATURE_FILE_NAME,
    FEATURES_DIRECTORY,
    LIFECYCLE_FOLDERS,
    LifecycleFolder,
)
from factory.domain.sections import (
    ACCEPTANCE_CRITERIA,
    JOURNAL,
    SMOKE_TEST,
    Section,
    code_blocks,
    lines_outside_blocks,
    required_sections,
    sections,
    split_lines,
    title,
)
from factory.domain.work_item import WorkItemDocument

_NUMBERED_ITEM = re.compile(r"^(\d+)\. ")
_DOCS_PREFIX = "docs:"
_EXPECT_PREFIX = "Expect:"
_NOT_A_LOCATION = (
    f"not a work item location: expected {FEATURES_DIRECTORY}/<feature>/"
    f"<{'|'.join(LIFECYCLE_FOLDERS)}>/<file>.md"
)


class FormFinding(BaseModel):
    """A rule a story breaks: its fixed message and, where it applies, a line of the body."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    line: PositiveInt | None
    message: str


class _Item(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    number: int
    start: int
    end: int


class _Body(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    lines: list[str]
    sections: list[Section]
    outside: frozenset[int]

    def section(self, heading: str) -> Section | None:
        return next((found for found in self.sections if found.heading == heading), None)


def _read_body(text: str) -> _Body:
    lines = split_lines(text)
    return _Body(
        text=text,
        lines=lines,
        sections=sections(text),
        outside=frozenset(lines_outside_blocks(lines)),
    )


def _items(body: _Body, heading: str) -> list[_Item]:
    found = body.section(heading)
    if found is None:
        return []
    starts: list[tuple[int, int]] = []
    for index in range(found.start + 1, found.end):
        match = _NUMBERED_ITEM.match(body.lines[index])
        if index in body.outside and match is not None:
            starts.append((index, int(match.group(1))))
    ends = [*(start for start, _ in starts[1:]), found.end] if starts else []
    return [
        _Item(number=number, start=start, end=end)
        for (start, number), end in zip(starts, ends, strict=True)
    ]


def _first_misnumbered(items: Sequence[_Item]) -> tuple[_Item, int] | None:
    for expected, item in enumerate(items, start=1):
        if item.number != expected:
            return item, expected
    return None


def _check_title(body: _Body) -> list[FormFinding]:
    if title(body.text) is None:
        return [FormFinding(line=None, message="the story has no title line")]
    return []


def _check_sections(body: _Body, form: str) -> list[FormFinding]:
    present = {found.heading for found in body.sections}
    return [
        FormFinding(line=None, message=f"missing section: ## {heading}")
        for heading in required_sections(form)
        if heading not in present
    ]


def _check_numbering(items: Sequence[_Item], name: str) -> list[FormFinding]:
    misnumbered = _first_misnumbered(items)
    if misnumbered is None:
        return []
    item, expected = misnumbered
    message = f"{name} numbered {item.number} where {expected} is expected"
    return [FormFinding(line=item.start + 1, message=message)]


def _item_text(body: _Body, item: _Item) -> str:
    return "\n".join(body.lines[item.start : item.end])


def _check_closing_criteria(body: _Body, criteria: Sequence[_Item]) -> list[FormFinding]:
    if len(criteria) < 2:
        return []
    findings: list[FormFinding] = []
    second_to_last, last = criteria[-2], criteria[-1]
    second_to_last_text = _item_text(body, second_to_last)
    if "make check" not in second_to_last_text or "green" not in second_to_last_text:
        message = 'the second-to-last criterion must contain "make check" and "green"'
        findings.append(FormFinding(line=second_to_last.start + 1, message=message))
    last_text = _NUMBERED_ITEM.sub("", _item_text(body, last), count=1)
    if not last_text.startswith(_DOCS_PREFIX):
        message = 'the last criterion must start with "docs:"'
        findings.append(FormFinding(line=last.start + 1, message=message))
    return findings


def _is_followed_by_expect(body: _Body, closing: int | None, section_end: int) -> bool:
    if closing is None:
        return False
    following = (line for line in body.lines[closing + 1 : section_end] if line.strip())
    first = next(following, None)
    return first is not None and first.startswith(_EXPECT_PREFIX)


def _check_smoke_test(body: _Body) -> list[FormFinding]:
    found = body.section(SMOKE_TEST)
    if found is None:
        return []
    blocks = [block for block in code_blocks(body.lines) if found.start < block.start < found.end]
    if not blocks:
        return [FormFinding(line=found.start + 1, message="the Smoke test has no code block")]
    return [
        FormFinding(
            line=block.start + 1,
            message=(
                f"the code block opened at line {block.start + 1} "
                f'is not followed by an "{_EXPECT_PREFIX}" line'
            ),
        )
        for block in blocks
        if not _is_followed_by_expect(body, block.end, found.end)
    ]


def _check_backlog(document: WorkItemDocument, entries: Sequence[_Item]) -> list[FormFinding]:
    findings: list[FormFinding] = []
    if document.ignored_keys:
        keys = ", ".join(document.ignored_keys)
        findings.append(
            FormFinding(line=None, message=f"a backlog story carries no front matter: {keys}")
        )
    if entries:
        message = "a backlog story carries no journal entries"
        findings.append(FormFinding(line=entries[0].start + 1, message=message))
    return findings


def _check_started(document: WorkItemDocument, entries: Sequence[_Item]) -> list[FormFinding]:
    if document.state is None:
        return [FormFinding(line=None, message="the story has no state")]
    recorded = len(document.state.journal)
    if recorded != len(entries):
        message = f"the journal data lists {recorded} entries but the text shows {len(entries)}"
        return [FormFinding(line=None, message=message)]
    return []


def check_story_form(
    document: WorkItemDocument, form: str, *, folder: LifecycleFolder
) -> list[FormFinding]:
    """Return every finding against the story form, in the order of the rules."""
    body = _read_body(document.body)
    criteria = _items(body, ACCEPTANCE_CRITERIA)
    entries = _items(body, JOURNAL)
    findings = [
        *_check_title(body),
        *_check_sections(body, form),
        *_check_numbering(criteria, "criterion"),
        *_check_closing_criteria(body, criteria),
        *_check_smoke_test(body),
        *_check_numbering(entries, "journal entry"),
    ]
    if folder == "backlog":
        findings += _check_backlog(document, entries)
    else:
        findings += _check_started(document, entries)
    return findings


def _story_id_of_file_name(name: str) -> str | None:
    parsed = parse_work_item_file_name(name)
    if parsed is None or is_acceptance(parsed.id):
        return None
    return parsed.id


def lifecycle_folder_of_location(path: str) -> LifecycleFolder | None:
    """Return the lifecycle folder of a path in a work item location, whatever its names."""
    parts = path.split("/")
    if len(parts) != 5 or "/".join(parts[:2]) != FEATURES_DIRECTORY:
        return None
    for folder in LIFECYCLE_FOLDERS:
        if parts[3] == folder:
            return folder
    return None


def _finding(message: str) -> FormFinding:
    return FormFinding(line=None, message=message)


def check_story_place(path: str, *, feature_file_exists: bool) -> list[FormFinding]:
    """Return every finding against where a story file sits, given its repository path."""
    if lifecycle_folder_of_location(path) is None:
        return [_finding(_NOT_A_LOCATION)]
    _, _, directory, _, name = path.split("/")
    story = _story_id_of_file_name(name)
    feature = parse_feature_directory_name(directory)
    findings: list[FormFinding] = []
    if story is None:
        findings.append(_finding(f'the file name "{name}" is not F0000-S0000[-slug].md'))
    if feature is None:
        findings.append(_finding(f'the feature directory "{directory}" is not F0000[-slug]'))
    if story is not None and feature is not None and feature_of(story) != feature.id:
        message = f"the story {story} is in the directory of feature {feature.id}"
        findings.append(_finding(message))
    if not feature_file_exists:
        message = (
            f"the feature file {FEATURE_FILE_NAME} is missing in {FEATURES_DIRECTORY}/{directory}"
        )
        findings.append(_finding(message))
    return findings
