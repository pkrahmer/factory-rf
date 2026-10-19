"""The rule on a project's own skills and agents in the shipped agents' rules."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body

SKILLS_RULE = (
    "R15. A project may bring its own skills under `.claude/skills/` and its own agents under "
    "`factory/agents/`; both are the human's files, like `CLAUDE.md`, and you never write them. "
    "When your tools include `Skill`, load a project skill whose description fits your work. "
    "Where a skill contradicts these instructions (it runs `make check` in the background, "
    "commits, pushes, or writes outside your write paths), these instructions win: follow them, "
    "and name in your entry the skill and the step you set aside."
)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_the_rules_hold_the_skills_rule_once_right_after_r14(name: str) -> None:
    lines = (section_text(agent_body(name), "Rules") or "").splitlines()

    assert lines.count(SKILLS_RULE) == 1
    [r14] = [index for index, line in enumerate(lines) if line.startswith("R14. ")]
    following = [line for line in lines[r14 + 1 :] if line.strip()]
    assert following[0] == SKILLS_RULE
