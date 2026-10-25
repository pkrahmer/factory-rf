"""Every shipped agent carries the rule on write paths that the take keeps and no kernel promise."""

import pytest

from shipped_agents import AGENT_HOME, SHIPPED_NAMES, WRITE_PATHS_RULE


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_each_agent_holds_the_take_s_r14_once_and_no_kernel_promise(name: str) -> None:
    text = (AGENT_HOME / "agents" / f"{name}.md").read_text(encoding="utf-8")

    assert text.splitlines().count(WRITE_PATHS_RULE) == 1
    assert "the kernel refuses every other write" not in text
    assert "$TMPDIR" not in text
