"""The reviewer's notes from round 1 on and its added criterion, in the shipped agent texts."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import agent_body

_RECOMMENDATION = (
    "Your recommendation is your decision: `docs` passes, `doing` sends the work item back. "
    'Never both, and never "pass with remarks": a remark worth writing is a finding, except for '
    "the notes from round 1 on below."
)
_NOTES = (
    "From round 1 on (your prompt names the round; the first review, at round 0, still sends "
    "such a point back), a point that is only about the quality of a test file the diff adds "
    "(a copied helper, a name, a duplicate test) is a note, not a finding: write the notes under "
    "`Notes:` after the findings, or after `no findings`, one line each with its location; they "
    "do not send the work item back. This holds for the copied helper and the separate test "
    "functions your lessons count as findings, when they are in a test file the diff adds. A "
    "point on an acceptance criterion (an untested side of a stated limit among them), the "
    "architecture, security or anything under `src/` is still a finding and sends it back with "
    "`doing`."
)
_ADDED_CRITERION = (
    "When the diff builds a behaviour that no criterion names, and pinning it needs no change "
    "under `src/`, add the criterion yourself instead of asking the human: write it into the "
    "work item's `## Acceptance criteria` before the two closing ones and renumber those, name "
    "it in your entry as the finding `criterion <n> added: it needs its test`, and end with "
    "`doing`. The coder hands it to the tester, who writes the test. A criterion that needs a "
    "code change stays a finding or a question."
)
_CODER = (
    "When the reviewer's latest entry adds a criterion that needs only its test, change no code: "
    "end with `tests` and an entry naming the criterion."
)
_TESTER = (
    "When the coder's entry names a criterion the reviewer added that needs only its test, there "
    "is no test to edit: write the test of that criterion as the role section describes, run "
    "`make test` once, and end with `doing`."
)
_ACCEPTANCE_REVIEWER = (
    "Your prompt's `Human interventions of the stories` line counts the questions the human "
    "answered, by cause, and the hours the stories waited for them: give both in the cost "
    "section, and name the story that needed the human most when its journal shows why."
)


@pytest.mark.parametrize(
    ("name", "heading", "text"),
    [
        pytest.param("reviewer", "Role", _RECOMMENDATION, id="reviewer-recommendation"),
        pytest.param("reviewer", "Role", _NOTES, id="reviewer-notes"),
        pytest.param("reviewer", "Role", _ADDED_CRITERION, id="reviewer-added-criterion"),
        pytest.param("coder", "Stage", _CODER, id="coder"),
        pytest.param("tester", "Stage", _TESTER, id="tester"),
        pytest.param("acceptance-reviewer", "Role", _ACCEPTANCE_REVIEWER, id="acceptance"),
    ],
)
def test_agent_section_holds_the_review_leave_text(name: str, heading: str, text: str) -> None:
    assert text in (section_text(agent_body(name), heading) or "")


def test_reviewer_no_longer_holds_the_old_recommendation_sentence() -> None:
    old = 'Never both, never "pass with remarks": a remark worth writing is a finding.'

    assert old not in agent_body("reviewer")


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        pytest.param(_RECOMMENDATION, _NOTES, id="notes-follow-recommendation"),
        pytest.param(_NOTES, _ADDED_CRITERION, id="added-criterion-follows-notes"),
    ],
)
def test_reviewer_paragraph_follows_the_one_before_it(earlier: str, later: str) -> None:
    body = agent_body("reviewer")

    assert f"{earlier}\n\n{later}" in body
