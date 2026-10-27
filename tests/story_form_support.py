"""The story form and its smoke test, shared by the story form tests."""

from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemState

FORM = (
    "# Story form\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n"
    "## Smoke test\n\n## Journal\n"
)


SMOKE = "```bash\nuv run factory\n```\nExpect: it works."


def _state(records: int, stage: str = "review") -> WorkItemState:
    journal = [
        JournalRecord(number=number, speaker="factory", kind="result")
        for number in range(1, records + 1)
    ]
    return WorkItemState(stage=stage, journal=journal)
