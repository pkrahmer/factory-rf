"""The shipped agent files live in `agents/`, and the old folder is gone."""

import pytest

from support.shipped_agents import AGENT_HOME, ROOT, SHIPPED_NAMES

AGENT_FILE_NAMES = sorted(f"{name}.md" for name in SHIPPED_NAMES)


def test_the_old_agent_folder_is_gone() -> None:
    assert [path for path in (ROOT / "claude").rglob("*") if path.is_file()] == []


@pytest.mark.parametrize("name", AGENT_FILE_NAMES)
def test_the_agent_folder_holds_each_agent_file(name: str) -> None:
    assert (AGENT_HOME / "agents" / name).is_file()


def test_the_agent_folder_holds_no_other_agent_file() -> None:
    assert sorted(path.name for path in (AGENT_HOME / "agents").iterdir()) == AGENT_FILE_NAMES
