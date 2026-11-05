"""The documenter's lesson on the sources of a decision log entry's reasons."""

import pytest

from factory.shared.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body

_BULLET = (
    '- In `docs/decisions.md`, write a "Why" or a "Rejected" only from what the story names: its '
    "Description, its Interface, its docs criterion and its journal, where the human's answers "
    "stand. Never add a reason or a rejected option of your own reading of the code or the "
    'documents. When the story names no rejected option for an entry, write no "Rejected" line, '
    "and name that entry in your journal entry."
)
_GUIDE_BULLET_START = "- The project guide is an index plus one file for each domain"
_TEMPORARY_BULLET_START = "- Make every file you need outside the repository in a temporary"
_DOCUMENTS_ONLY_BULLET_START = "- When every file you changed is a document"


@pytest.fixture
def lesson_lines() -> list[str]:
    lessons = section_text(agent_body("documenter"), "Lessons") or ""
    return [line for line in lessons.strip().splitlines() if line.strip()]


def test_documenter_lessons_hold_the_decision_log_bullet(lesson_lines: list[str]) -> None:
    assert _BULLET in lesson_lines


def test_decision_log_bullet_stands_between_the_guide_and_temporary_bullets(
    lesson_lines: list[str],
) -> None:
    place = lesson_lines.index(_BULLET)

    assert 0 < place < len(lesson_lines) - 1
    assert lesson_lines[place - 1].startswith(_GUIDE_BULLET_START)
    assert lesson_lines[place + 1].startswith(_TEMPORARY_BULLET_START)
    assert lesson_lines[-1].startswith(_DOCUMENTS_ONLY_BULLET_START)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_only_the_documenter_holds_the_decision_log_bullet(name: str) -> None:
    assert (_BULLET in agent_body(name)) == (name == "documenter")
