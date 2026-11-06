"""The docs route in the shipped agents: the intake's choice, the documenter and the reviewer."""

import pytest

from support.shipped_agents import stage_section

ROUTING_RULE = (
    "Choose `docs-only` when every path the Interface changes is one the documenter may write "
    "(`README.md`, `docs/*`, `operator/README.md`); otherwise `tests`. A story on the docs route "
    "has no tests stage and no doing stage, so its criteria are about documents only."
)

DOCS_DIFF = "`git diff main...HEAD -- README.md docs operator/README.md`"


def _stage_subsection(name: str, stage: str) -> str:
    lines = stage_section(name).splitlines()
    heading = f"### {stage}"
    starts = [index for index, line in enumerate(lines) if line.strip() == heading]
    assert len(starts) == 1, f"{name}.md has {len(starts)} `{heading}` headings in its Stage"
    rest = lines[starts[0] + 1 :]
    end = next((index for index, line in enumerate(rest) if line.startswith("#")), len(rest))
    return "\n".join(rest[:end])


def test_the_intake_routes_a_documents_only_story_to_docs_only_and_every_other_to_tests() -> None:
    assert stage_section("intake").count(ROUTING_RULE) == 1


@pytest.mark.parametrize(
    "named",
    [
        pytest.param("`make documents`", id="make-documents"),
        pytest.param("`docs-review`", id="ends-with-docs-review"),
    ],
)
def test_the_documenter_in_docs_only_writes_the_documents_and_hands_to_review_or_tests(
    named: str,
) -> None:
    assert named in _stage_subsection("documenter", "docs-only")


def test_the_documenter_in_docs_only_hands_a_change_outside_the_documents_to_tests() -> None:
    bullets = [
        line
        for line in _stage_subsection("documenter", "docs-only").splitlines()
        if "outside the documents" in line
    ]

    assert len(bullets) == 1
    assert "end with `tests`" in bullets[0]
    assert "entry names that change" in bullets[0]


@pytest.mark.parametrize(
    "named",
    [
        pytest.param(DOCS_DIFF, id="diff-command"),
        pytest.param("work item", id="work-item"),
        pytest.param("`docs/project-guide/style.md`", id="style-page"),
        pytest.param("`docs-approval`", id="ends-with-docs-approval"),
        pytest.param("`docs-only`", id="sends-back-with-docs-only"),
        pytest.param("numbered", id="numbered-findings"),
    ],
)
def test_the_reviewer_in_docs_review_reads_the_documents_diff_and_approves_or_sends_back(
    named: str,
) -> None:
    assert named in _stage_subsection("reviewer", "docs-review")


STYLE_PAGE_SENTENCE = (
    "Judge the writing against `docs/project-guide/style.md`: its rules for all documents "
    "and the section for the kind of document the diff changes."
)


@pytest.mark.parametrize(
    ("text", "count"),
    [
        pytest.param(STYLE_PAGE_SENTENCE, 1, id="style-page-sentence"),
        pytest.param("until", 0, id="no-until"),
        pytest.param(
            "Write for a reader without the history: no feature or story IDs, no version names.",
            0,
            id="no-old-rule-history",
        ),
        pytest.param(
            "One idea per sentence, at most about 25 words, at most one parenthesis.",
            0,
            id="no-old-rule-one-idea",
        ),
        pytest.param(
            "Explain each factory word once, in the glossary.", 0, id="no-old-rule-glossary"
        ),
        pytest.param("What to do comes first, the details after.", 0, id="no-old-rule-what-first"),
        pytest.param("Round numbers.", 0, id="no-old-rule-round-numbers"),
        pytest.param("Examples are real and were run.", 0, id="no-old-rule-examples"),
        pytest.param("Only the current truth.", 0, id="no-old-rule-current-truth"),
    ],
)
def test_the_reviewer_in_docs_review_judges_the_writing_by_the_style_page_alone(
    text: str, count: int
) -> None:
    assert _stage_subsection("reviewer", "docs-review").count(text) == count


def test_the_documenter_in_docs_only_replaces_the_steps_of_the_stage() -> None:
    assert "In the stage `docs-only`, these bullets replace steps 1 to 6" in _stage_subsection(
        "documenter", "docs-only"
    )


def test_the_documenter_back_from_docs_review_fixes_exactly_the_findings_and_hands_back() -> None:
    bullets = [
        line
        for line in _stage_subsection("documenter", "docs-only").splitlines()
        if "the reviewer's from `docs-review`" in line
    ]

    assert len(bullets) == 1
    assert "fix exactly its numbered findings" in bullets[0]
    assert "end with `docs-review`" in bullets[0]


@pytest.mark.parametrize(
    "named",
    [
        pytest.param(
            "In the stage `docs-review`, this subsection replaces the Role's scope",
            id="replaces-the-scope",
        ),
        pytest.param("its checklist", id="replaces-the-checklist"),
        pytest.param("its decisions, and steps 1 to 3", id="replaces-decisions-and-steps"),
        pytest.param("Judge the facts against the code and the criteria", id="judges-the-facts"),
    ],
)
def test_the_reviewer_in_docs_review_replaces_its_code_review_and_judges_the_facts(
    named: str,
) -> None:
    assert named in _stage_subsection("reviewer", "docs-review")
