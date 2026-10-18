"""The acceptance reviewer's facts carry the human's waits of the stories after their cost."""

import pytest

from factory.domain.acceptance import AcceptanceFacts, FeatureFiles, acceptance_facts

COST_LINE = "1 runs"
HUMAN_LINE = "1 questions answered (question 1), 1.5 h waited"
DISK_NOW = "disk acceptance: /work 1.0 GB free, 0.1 GB used"
DISK_BEFORE = "disk start: /work 1.2 GB free, 0.05 GB used"
TODAY = [
    "Archived stories: F0001-S0001",
    "Next free story number: F0001-S0002",
    "Cost of the stories: 1 runs",
]
HUMAN = f"Human interventions of the stories: {HUMAN_LINE}"
DISK = [f"Disk now: {DISK_NOW}", f"Disk at the previous record: {DISK_BEFORE}"]


@pytest.mark.parametrize(
    ("human_line", "disk_now", "expected"),
    [
        pytest.param(HUMAN_LINE, None, [*TODAY, HUMAN], id="human-without-disk"),
        pytest.param(HUMAN_LINE, DISK_NOW, [*TODAY, HUMAN, *DISK], id="human-with-disk"),
        pytest.param(None, None, TODAY, id="no-human-without-disk"),
        pytest.param(None, DISK_NOW, [*TODAY, *DISK], id="no-human-with-disk"),
    ],
)
def test_the_human_line_follows_the_cost_line_and_precedes_the_disk_lines(
    human_line: str | None, disk_now: str | None, expected: list[str]
) -> None:
    facts = AcceptanceFacts(
        archived=["F0001-S0001"],
        next_story="F0001-S0002",
        cost_line=COST_LINE,
        human_line=human_line,
        disk_now=disk_now,
        disk_before=DISK_BEFORE,
    )

    assert facts.lines() == expected


def test_acceptance_facts_pass_the_human_line_on() -> None:
    files = FeatureFiles(feature="F0001", done=["F0001-S0001-a.md"])

    facts = acceptance_facts(files, COST_LINE, human_line="x")

    assert facts.human_line == "x"
