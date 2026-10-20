"""A `.claude` folder is a protected path at any depth, and only as a whole segment."""

from pathlib import Path

import pytest

from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import PROTECTED_PATHS, matches_any, refusal


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (".claude/settings.json", True),
        (".claude/skills/x/SKILL.md", True),
        ("src/.claude/skills/x/SKILL.md", True),
        ("src/factory/.claude/commands/c.md", True),
        ("docs/.claude/settings.json", True),
        ("a/b/c/.claude/d", True),
        ("src/.claudex/a", False),
        ("src/x.claude/a", False),
        ("src/claude/a", False),
        ("claude/agents/coder.md", False),
        ("src/.claude", False),
        (".claudex/a", False),
    ],
)
def test_a_claude_folder_is_protected_at_any_depth_and_only_as_a_whole_segment(
    path: str, expected: bool
) -> None:
    assert matches_any(path, PROTECTED_PATHS) is expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "src/.claude/skills/x/SKILL.md",
            "src/.claude/skills/x/SKILL.md is owned by the human; a change there is a question.",
        ),
        (
            "src/factory/.claude/settings.json",
            "src/factory/.claude/settings.json is owned by the human;"
            " a change there is a question.",
        ),
        ("src/.claudex/a.md", None),
        ("src/a.py", None),
    ],
)
def test_the_guard_refuses_a_nested_claude_folder_although_a_write_path_matches_it(
    path: str, expected: str | None
) -> None:
    guard = GuardSettings(
        root=Path("/work"), write_paths=["src/*"], protected_paths=list(PROTECTED_PATHS)
    )

    assert refusal(path, guard) == expected
