"""The rule on write paths of every shipped agent names no hook."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body
from test_claude_agent_refusal import _WRITE_PATHS_RULE

_KERNEL_ONLY = (
    "the kernel refuses every other write, by any tool and any command you run, and the factory "
    "undoes any other write after the stage."
)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_the_write_paths_rule_says_only_the_kernel_refuses(name: str) -> None:
    rules = section_text(agent_body(name), "Rules") or ""

    assert _KERNEL_ONLY in _WRITE_PATHS_RULE
    assert _WRITE_PATHS_RULE in rules.splitlines()


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_no_shipped_agent_names_a_hook(name: str) -> None:
    assert "hook" not in agent_body(name)
