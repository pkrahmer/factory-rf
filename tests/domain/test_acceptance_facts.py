"""The acceptance reviewer's facts, its prompt and the head of a new acceptance report."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.acceptance import (
    AcceptanceFacts,
    AcceptanceState,
    FeatureFiles,
    acceptance_facts,
    acceptance_head,
    acceptance_prompt,
)
from factory.domain.work_item import initial_state
from source_search import imported_modules, modules

COST_LINE = "19 runs, 7.1 min, 3.33 USD"
DONE = ["F0002-S0001-a.md", "F0002-S0002-b.md", "F0002-S0004-d.md"]
ARCHIVED = ["F0002-S0001", "F0002-S0002", "F0002-S0004"]


@pytest.fixture
def facts() -> AcceptanceFacts:
    """Return the facts of three archived stories and a backlog story 6."""
    files = FeatureFiles(feature="F0002", backlog=["F0002-S0006-x.md", ".gitkeep"], done=list(DONE))
    return acceptance_facts(files, COST_LINE)


def test_the_facts_hold_the_archived_stories_and_the_number_after_the_highest(
    facts: AcceptanceFacts,
) -> None:
    assert facts.archived == ARCHIVED
    assert facts.next_story == "F0002-S0007"
    assert facts.cost_line == COST_LINE


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (FeatureFiles(feature="F0002", done=["F0002-S0009-i.md"]), "F0002-S0010"),
        (
            FeatureFiles(
                feature="F0002", in_progress=["F0002-S0011-k.md"], done=["F0002-S0009-i.md"]
            ),
            "F0002-S0012",
        ),
        (
            FeatureFiles(
                feature="F0002",
                in_progress=["F0002-A0020-acceptance.md", "notes.md"],
                done=["F0002-S0009-i.md"],
            ),
            "F0002-S0010",
        ),
        (FeatureFiles(feature="F0002", backlog=[".gitkeep"]), "F0002-S0001"),
    ],
    ids=["power-of-ten", "in-progress-story", "acceptance-report", "no-story"],
)
def test_the_next_story_number_has_four_digits_and_counts_only_story_files(
    files: FeatureFiles, expected: str
) -> None:
    assert acceptance_facts(files, COST_LINE).next_story == expected


@pytest.mark.parametrize(
    ("highest", "expected"),
    [("F0002-S9998-y.md", "F0002-S9999"), ("F0002-S9999-z.md", None)],
    ids=["9998", "9999"],
)
def test_the_next_story_number_ends_at_9999(highest: str, expected: str | None) -> None:
    files = FeatureFiles(feature="F0002", done=["F0002-S0001-a.md", highest])
    if expected is None:
        with pytest.raises(ValueError):
            acceptance_facts(files, COST_LINE)
    else:
        assert acceptance_facts(files, COST_LINE).next_story == expected


def test_the_facts_are_three_lines(facts: AcceptanceFacts) -> None:
    assert facts.lines() == [
        "Archived stories: F0002-S0001, F0002-S0002, F0002-S0004",
        "Next free story number: F0002-S0007",
        f"Cost of the stories: {COST_LINE}",
    ]


def test_the_prompt_is_the_base_an_empty_line_and_the_facts(facts: AcceptanceFacts) -> None:
    assert acceptance_prompt("Judge the feature.", facts) == "\n".join(
        [
            "Judge the feature.",
            "",
            "Archived stories: F0002-S0001, F0002-S0002, F0002-S0004",
            "Next free story number: F0002-S0007",
            f"Cost of the stories: {COST_LINE}",
        ]
    )


def test_the_head_is_an_initial_acceptance_state_a_title_and_an_empty_journal() -> None:
    head = acceptance_head("Todo service", "acceptance", ["F0001-S0001"])

    assert isinstance(head.state, AcceptanceState)
    assert head.state == AcceptanceState(
        **initial_state("acceptance").model_dump(), stories=["F0001-S0001"]
    )
    assert head.state.stage == "acceptance"
    assert head.state.stories == ["F0001-S0001"]
    assert head.state.outcome is None
    counters = (head.state.round, head.state.attempts, head.state.crashes)
    assert counters == (0, 0, 0)
    assert head.state.claim is None
    assert head.state.pull_request is None
    assert head.state.journal == []
    assert head.body == "# Acceptance of Todo service\n\n## Journal\n"


def test_the_head_builds_its_journal_heading_from_the_section_name() -> None:
    tree = modules()["factory.domain.acceptance"]

    assert "factory.domain.sections.JOURNAL" in imported_modules(tree)


@pytest.mark.parametrize(
    ("values", "accepted"),
    [
        ({"next_story": "F0002-S0007"}, True),
        ({"next_story": "F0002-A0007"}, False),
        ({"archived": ["F0002-S0001"]}, True),
        ({"archived": ["F002-S0001"]}, False),
        ({"unknown": 1}, False),
    ],
    ids=["story-id", "acceptance-id", "archived", "malformed-archived", "unknown-key"],
)
def test_the_facts_are_closed_and_typed(values: dict[str, object], accepted: bool) -> None:
    model: type[BaseModel] = AcceptanceFacts
    complete: dict[str, object] = {
        "archived": [],
        "next_story": "F0002-S0001",
        "cost_line": COST_LINE,
        **values,
    }
    if accepted:
        model(**complete)
    else:
        with pytest.raises(ValidationError):
            model(**complete)


def test_the_facts_refuse_an_assignment(facts: AcceptanceFacts) -> None:
    field = "next_story"
    with pytest.raises(ValidationError):
        setattr(facts, field, "F0002-S0008")
