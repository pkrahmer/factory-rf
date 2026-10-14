"""The pull request description the human reads at the approval."""

from collections.abc import Sequence

from factory.domain.git import CommitInfo
from factory.domain.journal import entry_text, last_record
from factory.domain.sections import ACCEPTANCE_CRITERIA, DESCRIPTION, section_text
from factory.domain.work_item import WorkItemDocument

HAND_OVER_CLOSING = (
    "Merge to accept the story. To send it back, close the pull request with a comment that says "
    "what should change; a close without one is answered with a question. Comments written while "
    "the story waits here are recorded in its journal and become the reason if you then close."
)
REPORT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Tests", "tester"),
    ("Review", "reviewer"),
    ("Documentation", "documenter"),
    ("Smoke test", "smoke-tester"),
)

_NONE = "none"
_FENCE = "```"
_SHORT_ID_LENGTH = 7


def _part(title: str, text: str | None) -> str:
    return f"## {title}\n\n{text or _NONE}"


def _report_text(document: WorkItemDocument, speaker: str) -> str | None:
    # The speaker comes from the record, never from the visible line, which anyone can write.
    record = last_record(document, speaker=speaker, kind="result")
    return None if record is None else entry_text(document, record.number)


def _commits_block(commits: Sequence[CommitInfo]) -> str:
    lines = [f"{commit.commit[:_SHORT_ID_LENGTH]} {commit.subject}" for commit in commits]
    return "\n".join([_FENCE, *lines, _FENCE])


def hand_over_description(document: WorkItemDocument, commits: Sequence[CommitInfo]) -> str:
    """The description: the story's sections, the latest reports, the commits and the closing."""
    parts = [
        _part(DESCRIPTION, section_text(document.body, DESCRIPTION)),
        _part(ACCEPTANCE_CRITERIA, section_text(document.body, ACCEPTANCE_CRITERIA)),
        *(_part(title, _report_text(document, speaker)) for title, speaker in REPORT_SECTIONS),
        f"## Commits\n\n{_commits_block(commits)}",
        HAND_OVER_CLOSING,
    ]
    return "\n\n".join(parts) + "\n"
