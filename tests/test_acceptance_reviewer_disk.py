"""The shipped acceptance reviewer compares the disk records its prompt carries."""

from shipped_agents import front_matter_and_body

SENTENCE = (
    "When your prompt has a Disk now line, compare it with the Disk at the previous record line, "
    "whose occasion it names, and name any growth that the feature's changes do not explain."
)


def test_the_slow_checks_of_the_acceptance_reviewer_end_with_the_disk_comparison() -> None:
    _, body = front_matter_and_body("acceptance-reviewer")

    [check] = [line for line in body.splitlines() if line.startswith("7. **The slow checks.**")]

    assert check.endswith(SENTENCE)
