"""The rule on write paths of every shipped agent names no hook."""

import pytest

from shipped_agents import SHIPPED_NAMES, agent_body


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_no_shipped_agent_names_a_hook(name: str) -> None:
    assert "hook" not in agent_body(name)
