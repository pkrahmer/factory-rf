"""The undo removes a `.claude` folder an agent wrote inside a write path, and keeps the rest."""

from factory.application.boundaries import Boundaries
from git_support import write_files
from human_clone import HumanClone
from undo_support import start_stage, undo_stage
from work_item_support import checkout_text

NESTED_SKILL = "src/.claude/skills/x/SKILL.md"
LOOKALIKE = "src/.claudex/notes.md"
SOURCE = "src/a.py"
AGENT_TEXT = "written by the agent\n"


def test_the_undo_removes_a_nested_claude_folder_and_keeps_the_rest(
    boundaries: Boundaries, human: HumanClone
) -> None:
    start = start_stage(boundaries, human, write_paths=["src/*"])
    write_files(
        boundaries.checkout,
        {NESTED_SKILL: AGENT_TEXT, LOOKALIKE: AGENT_TEXT, SOURCE: AGENT_TEXT},
    )

    report = undo_stage(boundaries, start)

    assert checkout_text(boundaries, NESTED_SKILL) is None
    assert checkout_text(boundaries, LOOKALIKE) == AGENT_TEXT
    assert checkout_text(boundaries, SOURCE) == AGENT_TEXT
    assert report.deleted == [NESTED_SKILL]
