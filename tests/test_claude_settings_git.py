"""The git commands the shipped settings allow and deny, and the commit rule of the agents."""

import json

import pytest

from factory.domain.sections import section_text
from shipped_agents import AGENT_HOME, SHIPPED_NAMES, front_matter_and_body


def _permissions(kind: str) -> list[str]:
    settings = json.loads((AGENT_HOME / "settings.json").read_text(encoding="utf-8"))
    entries: list[str] = settings["permissions"][kind]
    return entries


def test_allow_list_holds_no_git_add_or_commit() -> None:
    allowed = _permissions("allow")

    assert [
        entry
        for entry in allowed
        if entry.startswith("Bash(git add") or entry.startswith("Bash(git commit")
    ] == []


@pytest.mark.parametrize(
    "entry",
    [
        "Bash(git status*)",
        "Bash(git diff*)",
        "Bash(git log*)",
        "Bash(git show*)",
        "Bash(git rev-parse*)",
    ],
)
def test_allow_list_keeps_the_read_git_commands(entry: str) -> None:
    assert entry in _permissions("allow")


@pytest.mark.parametrize(
    "entry",
    ["Bash(git add*)", "Bash(git commit*)", "Bash(git push*)", "Bash(gh *)"],
)
def test_deny_list_holds_git_add_and_commit_beside_push_and_gh(entry: str) -> None:
    assert entry in _permissions("deny")


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_section_still_forbids_the_agent_to_commit(name: str) -> None:
    _, body = front_matter_and_body(name)

    assert "You do not commit either" in (section_text(body, "Rules") or "")
