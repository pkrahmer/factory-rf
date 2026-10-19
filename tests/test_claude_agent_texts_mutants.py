"""The reading of a mutation report, in the reviewer's and the acceptance reviewer's texts."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import agent_body

_REVIEWER_MUTANTS = (
    "When the coder's latest entry has the line of a mutation report (`` `mutants`: ``), read "
    "the survived and timed-out mutants of the modules the diff changed as part of item 1, "
    "listing and showing them as the project's `CLAUDE.md` says; do not run the report "
    "yourself, the factory ran it after the coder. A survivor in a line the diff added or "
    "changed, whose change breaks a rule the work item states, is a finding under item 1: name "
    "the mutant, the rule, and the test that would notice it. A survivor that changes no "
    "behaviour, changes only a message text, or sits in a line the diff did not change is a "
    "note, at any round: one line per group under `Notes:`, for the feature's acceptance. A "
    "report line that says `partial`, or that the factory stopped the report at its time limit, "
    "is a note too, never a pass of the mutants it did not reach."
)
_MUTATION_SCORE_HEADING = "3. **Mutation score.**"
_ACCEPTANCE_MUTATION_SCORE = (
    f"{_MUTATION_SCORE_HEADING} Run `make mutants` if the project has the target, and run it "
    "again while its last line says `partial`, at most three runs in all; read the survivors "
    "(`uv run mutmut show <id>` for a few of each kind). A survivor is a line the tests would "
    "not notice breaking; group survivors by module and rule into missing acceptance criteria. "
    "When the coder entries of the archived stories carry the line of a mutation report, their "
    "reviews have read the survivors of their own modules already: say which groups those "
    "reviews passed on as notes and which are new. Report the score from the last run's last "
    "line, say whether it is partial, and give the groups."
)
_OLD_ACCEPTANCE_SENTENCE = "Run `make mutants` if the project has the target; read the survivors"


@pytest.mark.parametrize(
    ("name", "text"),
    [
        pytest.param("reviewer", _REVIEWER_MUTANTS, id="reviewer-mutants"),
        pytest.param("acceptance-reviewer", _ACCEPTANCE_MUTATION_SCORE, id="acceptance-score"),
    ],
)
def test_agent_role_holds_the_mutation_report_text(name: str, text: str) -> None:
    assert text in (section_text(agent_body(name), "Role") or "")


def test_reviewer_mutants_paragraph_sits_between_item_6_and_the_findings_paragraph() -> None:
    body = agent_body("reviewer")
    lines = body.split("\n")
    item_6 = next(i for i, line in enumerate(lines) if line.startswith("6. **Earlier tests**:"))
    paragraph = lines.index(_REVIEWER_MUTANTS)
    findings = next(
        i
        for i, line in enumerate(lines)
        if line.startswith("Write findings as a numbered list in your entry")
    )

    assert item_6 < paragraph < findings


@pytest.mark.parametrize(
    ("text", "count"),
    [
        pytest.param(_OLD_ACCEPTANCE_SENTENCE, 0, id="old-sentence-gone"),
        pytest.param(_MUTATION_SCORE_HEADING, 1, id="heading-once"),
    ],
)
def test_acceptance_reviewer_holds_the_mutation_score_check_once(text: str, count: int) -> None:
    assert agent_body("acceptance-reviewer").count(text) == count
