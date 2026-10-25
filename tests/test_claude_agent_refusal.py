"""The rule on write paths that every shipped agent carries explains what becomes of a write."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, WRITE_PATHS_RULE, agent_body

_OLD_ENDING = (
    "the kernel refuses every other write, by any tool and any command you run, and the factory "
    "undoes any other write after the stage."
)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_hold_the_write_paths_rule_as_one_line(name: str) -> None:
    rules = section_text(agent_body(name), "Rules") or ""

    assert WRITE_PATHS_RULE in rules.splitlines()


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_old_ending_of_the_write_paths_rule_is_gone(name: str) -> None:
    assert _OLD_ENDING not in agent_body(name)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_write_paths_rule_appears_once(name: str) -> None:
    lines = [line for line in agent_body(name).splitlines() if line.startswith("R14. ")]

    assert len(lines) == 1
