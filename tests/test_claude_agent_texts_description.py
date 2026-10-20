"""The reviewer's correction of a stale Description, in the shipped agent texts."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body

_CORRECTION = (
    "When the work item's `## Description` has gone stale against what the story built, and the "
    "human's answers in the journal, the Interface or the criteria already settle what it should "
    "say, rewrite the stale sentences of the Description yourself and change nothing else in the "
    "work item. Name the correction in your entry as `description corrected: <what it said> -> "
    "<what it says now>`, one line each. A correction is not a finding: with no other finding, "
    "end with `docs`. A Description that the code contradicts while neither the journal nor the "
    "Interface nor the criteria settle which is right stays a finding, or a question when no "
    "stage can fix it."
)
_ADDED_CRITERION_END = "A criterion that needs a code change stays a finding or a question."
_CHECKLIST_ITEM_5 = (
    "5. **Work item hygiene**: the journal explains the main decision and what was rejected; the "
    "`## Description` matches what was built; the docs criterion still describes what the reader "
    "must know after this story (the documenter writes it next, from that criterion)."
)


def test_reviewer_role_holds_the_description_correction() -> None:
    assert _CORRECTION in (section_text(agent_body("reviewer"), "Role") or "")


@pytest.mark.parametrize(
    "joint",
    [
        pytest.param(f"{_ADDED_CRITERION_END}\n\nWhen the work item's", id="after-added-criterion"),
        pytest.param("when no stage can fix it.\n\n## Stage", id="before-stage"),
    ],
)
def test_description_correction_sits_between_added_criterion_and_stage(joint: str) -> None:
    assert joint in agent_body("reviewer")


@pytest.mark.parametrize(
    ("name", "count"),
    [pytest.param(name, 1 if name == "reviewer" else 0, id=name) for name in SHIPPED_NAMES],
)
def test_only_the_reviewer_names_a_description_correction(name: str, count: int) -> None:
    assert agent_body(name).count("description corrected:") == count


def test_reviewer_checklist_keeps_its_work_item_hygiene_item() -> None:
    assert (section_text(agent_body("reviewer"), "Role") or "").count(_CHECKLIST_ITEM_5) == 1
