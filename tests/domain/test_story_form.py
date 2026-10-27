"""The check of a story's form: one finding for each rule the story breaks."""

import pytest
from pydantic import ValidationError

from factory.domain.paths import LifecycleFolder
from factory.domain.story_form import FormFinding, check_story_form
from factory.domain.work_item import WorkItemDocument, WorkItemState
from story_form_support import FORM, SMOKE, _state

FORM_WITHOUT_JOURNAL = (
    "# Story form\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n## Smoke test\n"
)
TITLE = "# A story"
CRITERIA = "1. It works.\n2. make check stays green.\n3. docs: none, nothing changes."

NO_TITLE = "the story has no title line"
SECOND_TO_LAST = 'the second-to-last criterion must contain "make check" and "green"'
LAST = 'the last criterion must start with "docs:"'
NO_BLOCK = "the Smoke test has no code block"
NO_STATE = "the story has no state"
BACKLOG_ENTRIES = "a backlog story carries no journal entries"


def _body(
    *,
    title_line: str | None = TITLE,
    description: str | None = "Text.",
    interface: str | None = "None.",
    criteria: str | None = CRITERIA,
    smoke: str | None = SMOKE,
    journal: str | None = "",
) -> str:
    parts = [] if title_line is None else [title_line, ""]
    for heading, content in (
        ("Description", description),
        ("Interface", interface),
        ("Acceptance criteria", criteria),
        ("Smoke test", smoke),
        ("Journal", journal),
    ):
        if content is None:
            continue
        parts += [f"## {heading}", ""]
        if content:
            parts += [content, ""]
    return "\n".join(parts) + "\n"


def _line(body: str, text: str) -> int:
    return body.split("\n").index(text) + 1


def _check(
    body: str,
    *,
    folder: LifecycleFolder = "backlog",
    state: WorkItemState | None = None,
    ignored_keys: list[str] | None = None,
    form: str = FORM,
) -> list[FormFinding]:
    document = WorkItemDocument(state=state, body=body, ignored_keys=ignored_keys or [])
    return check_story_form(document, form, folder=folder)


def _expect_missing(line: int) -> str:
    return f'the code block opened at line {line} is not followed by an "Expect:" line'


def _expect_findings(findings: list[FormFinding]) -> list[FormFinding]:
    return [finding for finding in findings if '"Expect:"' in finding.message]


def test_a_complete_backlog_story_gives_no_finding() -> None:
    assert _check(_body()) == []


@pytest.mark.parametrize("line", [None, 1])
def test_a_finding_takes_no_line_or_a_positive_one(line: int | None) -> None:
    finding = FormFinding(line=line, message="x")

    assert finding.line == line
    assert finding.message == "x"


def test_a_finding_refuses_line_zero() -> None:
    with pytest.raises(ValidationError):
        FormFinding(line=0, message="x")


def test_a_body_without_a_title_line_has_no_title() -> None:
    assert _check(_body(title_line=None)) == [FormFinding(line=None, message=NO_TITLE)]


def test_a_title_line_inside_a_code_block_is_no_title() -> None:
    body = _body(title_line=None, description="```\n# A story\n```")

    assert _check(body) == [FormFinding(line=None, message=NO_TITLE)]


def test_each_missing_section_of_the_form_is_reported_in_the_forms_order() -> None:
    body = _body(interface=None, journal=None)

    assert _check(body) == [
        FormFinding(line=None, message="missing section: ## Interface"),
        FormFinding(line=None, message="missing section: ## Journal"),
    ]


def test_a_section_added_to_the_form_is_required() -> None:
    assert _check(_body(), form=FORM + "\n## Notes\n") == [
        FormFinding(line=None, message="missing section: ## Notes")
    ]


def test_a_heading_only_inside_a_code_block_is_a_missing_section() -> None:
    body = _body(smoke="```bash\n## Journal\n```\nExpect: it works.", journal=None)

    assert _check(body) == [FormFinding(line=None, message="missing section: ## Journal")]


@pytest.mark.parametrize(
    ("criteria", "wrong_item", "message"),
    [
        (
            "1. a\n2. make check stays green.\n4. docs: none.",
            "4. docs: none.",
            "criterion numbered 4 where 3 is expected",
        ),
        (
            "2. a\n3. make check stays green.\n4. docs: none.",
            "2. a",
            "criterion numbered 2 where 1 is expected",
        ),
        (
            "1. make check stays green.\n1. docs: none.",
            "1. docs: none.",
            "criterion numbered 1 where 2 is expected",
        ),
    ],
)
def test_the_first_misnumbered_criterion_is_reported_on_its_line(
    criteria: str, wrong_item: str, message: str
) -> None:
    body = _body(criteria=criteria)

    assert _check(body) == [FormFinding(line=_line(body, wrong_item), message=message)]


def test_indented_and_fenced_numbered_lines_are_no_criteria() -> None:
    criteria = "1. a\n   2. x\n```\n3. y\n```\n2. make check stays green.\n3. docs: none."

    assert _check(_body(criteria=criteria)) == []


def test_an_acceptance_criteria_section_without_items_gives_no_finding() -> None:
    assert _check(_body(criteria="")) == []


@pytest.mark.parametrize("item", ["2. It stays green.", "2. make check passes."])
def test_a_second_to_last_criterion_without_make_check_and_green_is_reported(item: str) -> None:
    body = _body(criteria=f"1. It works.\n{item}\n3. docs: none.")

    assert _check(body) == [FormFinding(line=_line(body, item), message=SECOND_TO_LAST)]


def test_a_second_to_last_criterion_spread_over_two_lines_is_read_whole() -> None:
    body = _body(criteria="1. It works.\n2. make check\n   stays green.\n3. docs: none.")

    assert _check(body) == []


@pytest.mark.parametrize("item", ["3. Docs: x", "3. done"])
def test_a_last_criterion_not_starting_with_docs_is_reported(item: str) -> None:
    body = _body(criteria=f"1. It works.\n2. make check stays green.\n{item}")

    assert _check(body) == [FormFinding(line=_line(body, item), message=LAST)]


def test_a_last_criterion_starting_with_docs_gives_no_finding() -> None:
    assert _check(_body(criteria="1. It works.\n2. make check stays green.\n3. docs: none")) == []


def test_two_criteria_are_checked_for_both_closing_criteria() -> None:
    body = _body(criteria="1. a\n2. b")

    assert _check(body) == [
        FormFinding(line=_line(body, "1. a"), message=SECOND_TO_LAST),
        FormFinding(line=_line(body, "2. b"), message=LAST),
    ]


@pytest.mark.parametrize("criteria", ["1. a", ""])
def test_fewer_than_two_criteria_get_no_closing_finding(criteria: str) -> None:
    assert _check(_body(criteria=criteria)) == []


def test_a_smoke_test_without_a_code_block_is_reported_on_its_heading() -> None:
    body = _body(smoke="No block here.")

    assert _check(body) == [FormFinding(line=_line(body, "## Smoke test"), message=NO_BLOCK)]


@pytest.mark.parametrize(
    "smoke",
    [
        "```bash\nuv run factory\n```\nSome prose.\nExpect: it works.",
        "```bash\nuv run factory\n```",
        "```bash\nuv run factory",
    ],
)
def test_a_code_block_without_an_expect_line_is_reported_on_its_opening(smoke: str) -> None:
    body = _body(smoke=smoke)
    opening = _line(body, "```bash")

    assert _expect_findings(_check(body)) == [
        FormFinding(line=opening, message=_expect_missing(opening))
    ]


def test_blank_lines_may_stand_between_a_code_block_and_its_expect_line() -> None:
    body = _body(smoke="```bash\nuv run factory\n```\n\n\nExpect: it works.")

    assert _check(body) == []


def test_of_two_code_blocks_only_the_one_without_expect_is_reported() -> None:
    body = _body(
        smoke="```bash\nuv run factory\n```\nExpect: it works.\n\n```sh\nuv run other\n```"
    )
    opening = _line(body, "```sh")

    assert _check(body) == [FormFinding(line=opening, message=_expect_missing(opening))]


def test_headings_and_comments_inside_a_smoke_test_block_leave_the_story_whole() -> None:
    smoke = "```bash\n## start the server\n# comment\nuv run factory\n```\nExpect: it works."

    assert _check(_body(title_line=None, smoke=smoke)) == [FormFinding(line=None, message=NO_TITLE)]
    assert _check(_body(smoke=smoke)) == []


def test_the_first_misnumbered_journal_entry_is_reported_on_its_line() -> None:
    body = _body(journal="1. human: created.\n3. intake: accepted.")

    assert _check(body, folder="done", state=_state(2, "done")) == [
        FormFinding(
            line=_line(body, "3. intake: accepted."),
            message="journal entry numbered 3 where 2 is expected",
        )
    ]


def test_indented_lines_in_a_journal_entry_are_no_entries() -> None:
    body = _body(journal="1. human: created.\n   3. an indented line\n2. intake: accepted.")

    assert _check(body, folder="done", state=_state(2, "done")) == []


def test_a_journal_without_entries_gives_no_finding() -> None:
    assert _check(_body(), folder="done", state=_state(0, "done")) == []


def test_a_backlog_story_with_front_matter_is_reported_with_its_keys() -> None:
    assert _check(_body(), ignored_keys=["stage", "attempts"]) == [
        FormFinding(line=None, message="a backlog story carries no front matter: stage, attempts")
    ]


@pytest.mark.parametrize("folder", ["in-progress", "done"])
def test_a_started_story_without_state_is_reported(folder: LifecycleFolder) -> None:
    assert _check(_body(), folder=folder) == [FormFinding(line=None, message=NO_STATE)]


@pytest.mark.parametrize("folder", ["in-progress", "done"])
def test_a_started_story_with_a_state_has_one(folder: LifecycleFolder) -> None:
    assert _check(_body(), folder=folder, state=_state(0)) == []


@pytest.mark.parametrize(
    ("journal", "form", "shown"),
    [
        ("1. human: created.\n2. intake: accepted.\n3. tests: doing.", FORM, 3),
        (None, FORM_WITHOUT_JOURNAL, 0),
    ],
)
def test_journal_data_and_text_that_disagree_are_reported(
    journal: str | None, form: str, shown: int
) -> None:
    body = _body(journal=journal)

    assert _check(body, folder="in-progress", state=_state(2), form=form) == [
        FormFinding(
            line=None, message=f"the journal data lists 2 entries but the text shows {shown}"
        )
    ]


def test_journal_data_and_text_that_agree_give_no_finding() -> None:
    body = _body(journal="1. human: created.\n2. intake: accepted.")

    assert _check(body, folder="in-progress", state=_state(2)) == []


def test_the_backlog_gets_no_finding_about_the_journal_data() -> None:
    assert _check(_body(), state=_state(2)) == []


def test_a_backlog_story_with_journal_entries_is_reported_on_the_first() -> None:
    body = _body(journal="1. human: created.\n2. intake: accepted.")

    assert _check(body) == [
        FormFinding(line=_line(body, "1. human: created."), message=BACKLOG_ENTRIES)
    ]


def test_a_backlog_story_without_a_journal_section_has_no_entries() -> None:
    assert _check(_body(journal=None), form=FORM_WITHOUT_JOURNAL) == []


def test_a_started_story_may_carry_journal_entries() -> None:
    body = _body(journal="1. human: created.\n2. intake: accepted.")

    assert _check(body, folder="in-progress", state=_state(2)) == []


def _broken_body() -> str:
    return _body(
        title_line=None,
        description=None,
        criteria="1. a\n3. b\n4. c",
        smoke="No block.",
        journal="1. x\n3. y",
    )


def _findings_of_the_body(body: str) -> list[FormFinding]:
    return [
        FormFinding(line=None, message=NO_TITLE),
        FormFinding(line=None, message="missing section: ## Description"),
        FormFinding(line=_line(body, "3. b"), message="criterion numbered 3 where 2 is expected"),
        FormFinding(line=_line(body, "3. b"), message=SECOND_TO_LAST),
        FormFinding(line=_line(body, "4. c"), message=LAST),
        FormFinding(line=_line(body, "## Smoke test"), message=NO_BLOCK),
        FormFinding(
            line=_line(body, "3. y"), message="journal entry numbered 3 where 2 is expected"
        ),
    ]


def test_a_backlog_story_gets_all_its_findings_in_the_order_of_the_rules() -> None:
    body = _broken_body()

    assert _check(body, ignored_keys=["stage"]) == [
        *_findings_of_the_body(body),
        FormFinding(line=None, message="a backlog story carries no front matter: stage"),
        FormFinding(line=_line(body, "1. x"), message=BACKLOG_ENTRIES),
    ]


def test_a_started_story_gets_all_its_findings_in_the_order_of_the_rules() -> None:
    body = _broken_body()

    assert _check(body, folder="in-progress", state=_state(1)) == [
        *_findings_of_the_body(body),
        FormFinding(line=None, message="the journal data lists 1 entries but the text shows 2"),
    ]
