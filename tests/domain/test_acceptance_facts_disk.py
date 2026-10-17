"""The acceptance reviewer's facts carry the disk record of now and the one before it."""

import pytest

from factory.domain.acceptance import AcceptanceFacts, FeatureFiles, acceptance_facts

COST_LINE = "1 runs"
DISK_NOW = "disk acceptance: /work 1.0 GB free, 0.1 GB used"
DISK_BEFORE = "disk start: /work 1.2 GB free, 0.05 GB used"
TODAY = [
    "Archived stories: F0001-S0001",
    "Next free story number: F0001-S0002",
    "Cost of the stories: 1 runs",
]


def _facts(disk_now: str | None, disk_before: str | None) -> AcceptanceFacts:
    return AcceptanceFacts(
        archived=["F0001-S0001"],
        next_story="F0001-S0002",
        cost_line=COST_LINE,
        disk_now=disk_now,
        disk_before=disk_before,
    )


@pytest.mark.parametrize(
    ("disk_before", "last_line"),
    [
        (None, "Disk at the previous record: none"),
        (DISK_BEFORE, f"Disk at the previous record: {DISK_BEFORE}"),
    ],
    ids=["no-previous", "previous"],
)
def test_facts_with_a_disk_now_give_the_two_disk_lines_after_the_three_of_today(
    disk_before: str | None, last_line: str
) -> None:
    assert _facts(DISK_NOW, disk_before).lines() == [*TODAY, f"Disk now: {DISK_NOW}", last_line]


def test_acceptance_facts_pass_the_disk_values_on() -> None:
    files = FeatureFiles(feature="F0001", done=["F0001-S0001-a.md"])

    facts = acceptance_facts(files, COST_LINE, disk_now=DISK_NOW, disk_before=DISK_BEFORE)

    assert (facts.disk_now, facts.disk_before) == (DISK_NOW, DISK_BEFORE)


@pytest.mark.parametrize("disk_before", [None, DISK_BEFORE], ids=["no-previous", "previous"])
def test_facts_without_a_disk_now_give_the_three_lines_of_today(disk_before: str | None) -> None:
    assert _facts(None, disk_before).lines() == TODAY
