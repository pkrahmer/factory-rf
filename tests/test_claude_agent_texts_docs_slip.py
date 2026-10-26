"""A slip in a document goes from the smoke test to docs: the template and the shipped agents."""

from collections.abc import Callable

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body, template_definition

REWORK_RULE = (
    "R12. Rework rounds (review → doing, docs → doing, smoke-test → doing, smoke-test → docs, "
    "and the human's close at the approval) share the work item's `round`, capped by the "
    "stage's `round_cap` in the pipeline definition. Your prompt names the round; on a rework "
    "round the latest entries name the findings. When the cap is passed, the factory asks the "
    "human instead of looping."
)

OLD_REWORK_RULE = REWORK_RULE.replace("smoke-test → docs, ", "")

SLIP_STEP = (
    "5. Findings that are each a slip in a document the documenter writes (`README.md` or a "
    "file under `docs/`: the command read that document and found a sentence the code "
    "contradicts, or the contradicted criterion is the `docs:` criterion), while the code does "
    "what the work item says: add them as a numbered list (command, expected, observed, "
    "criterion if any) and end with `docs`."
)

OTHER_FINDINGS_STEP = (
    "6. Any other findings: add them as a numbered list (command, expected, observed, criterion "
    "if any) and end with `doing`. When some findings are slips in a document and others are "
    "not, all of them go to `doing`."
)

OLD_FINDINGS_STEP = (
    "Findings: add them as a numbered list (command, expected, observed, criterion if any) and "
    "end with `doing`."
)

DOCUMENTER_SENTENCE = (
    "When the latest entry is the smoke tester's and it ended with `docs`, its numbered findings "
    "are slips in the documents: fix exactly those, run the commands they name again, and end "
    "with `smoke-test`."
)


def _stage_section(name: str) -> str:
    return section_text(agent_body(name), "Stage") or ""


def test_the_template_lets_the_smoke_test_hand_a_slip_to_docs_and_keeps_every_other_next() -> None:
    definition = template_definition()

    smoke_test = definition.stages["smoke-test"]
    assert smoke_test.next == ["approval", "doing", "docs"]
    assert smoke_test.round_cap == 3
    others = {name: stage.next for name, stage in definition.stages.items() if name != "smoke-test"}
    assert others == {
        "intake": ["tests"],
        "tests": ["doing"],
        "doing": ["review", "tests"],
        "review": ["docs", "doing"],
        "docs": ["smoke-test", "doing"],
        "acceptance": ["approval"],
        "approval": ["done", "doing"],
        "done": [],
    }


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_every_shipped_agent_names_the_smoke_test_to_docs_rework(name: str) -> None:
    body = agent_body(name)

    assert body.count(REWORK_RULE) == 1
    assert OLD_REWORK_RULE not in body


@pytest.mark.parametrize(
    "holds",
    [
        pytest.param(lambda text: text.count(SLIP_STEP) == 1, id="slip-step"),
        pytest.param(lambda text: text.count(OTHER_FINDINGS_STEP) == 1, id="other-findings-step"),
        pytest.param(
            lambda text: 0 <= text.find(SLIP_STEP) < text.find(OTHER_FINDINGS_STEP),
            id="slip-step-first",
        ),
        pytest.param(lambda text: text.count("end with `docs`") == 1, id="docs-once"),
        pytest.param(lambda text: text.count("end with `approval`") == 1, id="approval-once"),
        pytest.param(lambda text: OLD_FINDINGS_STEP not in text, id="old-step-gone"),
    ],
)
def test_the_smoke_tester_ends_with_docs_only_for_slips_in_a_document(
    holds: Callable[[str], bool],
) -> None:
    assert holds(_stage_section("smoke-tester"))


def test_the_documenter_fixes_the_slips_of_the_smoke_test_and_hands_back_to_it() -> None:
    steps = [line for line in _stage_section("documenter").splitlines() if line.startswith("1. ")]

    assert len(steps) == 1
    assert steps[0].endswith(f" {DOCUMENTER_SENTENCE}")
    assert "end with `smoke-test`" in steps[0]
