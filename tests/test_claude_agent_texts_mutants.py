"""No shipped agent runs or reads mutation testing; \
the acceptance's check 3 says it is done by sweep."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import ROOT, agent_body

_MUTATION_TESTING_HEADING = "3. **Mutation testing.**"
_ACCEPTANCE_MUTATION_TESTING = (
    f"{_MUTATION_TESTING_HEADING} Not run here: mutation testing runs only as sweeps outside the "
    "factory. Never run `make mutants` or mutmut, whatever the project offers; write `By sweep, "
    "not run here.` under this check's heading and nothing more."
)
_ACCEPTANCE_SLOW_CHECKS = (
    "7. **The slow checks.** Whatever the project offers beyond `make check` (an image scan, an "
    "SBOM), but not `make mutants` (check 3); today usually nothing. Say so."
)
_TEMPLATE_MAKEFILE_MUTANTS = (
    "# `make mutants FEATURE=F0001`. Slow, so not part of `check`; a sweep by hand runs it, "
    "never a stage,"
)


@pytest.mark.parametrize(
    ("heading", "text"),
    [
        pytest.param("Role", _ACCEPTANCE_MUTATION_TESTING, id="check-3"),
        pytest.param("Role", _ACCEPTANCE_SLOW_CHECKS, id="check-7"),
        pytest.param(
            "Role",
            "(no finding of weight; proposed stories at most for noticed items)",
            id="recommendation",
        ),
        pytest.param("Role", "a documentation repair — not one per remark.", id="proposals"),
        pytest.param(
            "Stage", "Run the feature's smoke test for real; paste what it printed.", id="step-1"
        ),
        pytest.param(
            "Stage",
            "the entry `<recommendation>; <n> stories proposed`, followed by the eight findings "
            "in short",
            id="step-3",
        ),
    ],
)
def test_acceptance_reviewer_leaves_mutation_testing_to_sweeps(heading: str, text: str) -> None:
    assert text in (section_text(agent_body("acceptance-reviewer"), heading) or "")


@pytest.mark.parametrize(
    ("text", "count"),
    [
        pytest.param("3. **Mutation score.**", 0, id="old-heading"),
        pytest.param("Run `make mutants` if the project has the target", 0, id="old-check-3"),
        pytest.param("and `make mutants` for real", 0, id="old-step-1"),
        pytest.param("make mutants <killed>/<total>", 0, id="old-step-3"),
        pytest.param("mutmut show", 0, id="mutmut-show"),
        pytest.param("one per mutant", 0, id="one-per-mutant"),
        pytest.param("for survivors", 0, id="for-survivors"),
        pytest.param(_MUTATION_TESTING_HEADING, 1, id="new-heading-once"),
    ],
)
def test_acceptance_reviewer_holds_no_old_mutation_text(text: str, count: int) -> None:
    assert agent_body("acceptance-reviewer").count(text) == count


def test_acceptance_reviewer_mutation_testing_is_the_third_check() -> None:
    lines = agent_body("acceptance-reviewer").split("\n")
    check_3 = next(i for i, line in enumerate(lines) if line.startswith(_MUTATION_TESTING_HEADING))

    assert lines[check_3 + 1].startswith("4. **What the stories noticed.**")


@pytest.mark.parametrize("word", ["mutant", "mutmut", "mutation"])
def test_reviewer_names_no_mutation_testing(word: str) -> None:
    assert agent_body("reviewer").lower().count(word) == 0


def test_reviewer_item_6_is_followed_by_the_findings_paragraph() -> None:
    lines = agent_body("reviewer").split("\n")
    item_6 = next(i for i, line in enumerate(lines) if line.startswith("6. **Earlier tests**:"))

    assert lines[item_6 + 1] == ""
    assert lines[item_6 + 2].startswith("Write findings as a numbered list in your entry")


@pytest.mark.parametrize(
    ("text", "count"),
    [
        pytest.param(_TEMPLATE_MAKEFILE_MUTANTS, 1, id="sweep-by-hand"),
        pytest.param("the feature acceptance runs it", 0, id="old-acceptance"),
    ],
)
def test_template_makefile_leaves_mutants_to_a_sweep_by_hand(text: str, count: int) -> None:
    makefile = (ROOT / "template" / "Makefile").read_text(encoding="utf-8")

    assert makefile.count(text) == count
