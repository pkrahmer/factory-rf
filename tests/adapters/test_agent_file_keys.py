"""An agent file holds only the keys the agent runtime applies; any other key is refused."""

from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.agent_runs import APPLIED_AGENT_KEYS, KEY_NOT_APPLIED
from factory.domain.errors import AgentDefinitionInvalid
from git_support import write_agent

APPLIED = "model: opus\ntools: [Read, Edit]\neffort: medium\nbudget_usd: 4\n"


def _agent_file(front_matter: str) -> str:
    return f"---\n{front_matter}---\nNever edit tests.\n"


def _refused(agent_home: Path, front_matter: str) -> AgentDefinitionInvalid:
    write_agent(agent_home, "coder", _agent_file(front_matter))
    with pytest.raises(AgentDefinitionInvalid) as caught:
        FrontmatterAgentDefinitionReader(agent_home).read("coder")
    return caught.value


def _assert_refused_for(error: AgentDefinitionInvalid, key: str) -> None:
    assert error.name == "coder"
    assert error.key == key
    assert error.fault == f"key not applied by the agent runtime: {key}"
    assert key in str(error)


def test_the_applied_keys_are_model_tools_effort_and_budget() -> None:
    assert frozenset({"model", "tools", "effort", "budget_usd"}) == APPLIED_AGENT_KEYS
    assert KEY_NOT_APPLIED == "key not applied by the agent runtime"


def test_a_file_with_only_applied_keys_is_read(agent_home: Path) -> None:
    write_agent(agent_home, "coder", _agent_file(APPLIED))

    agent = FrontmatterAgentDefinitionReader(agent_home).read("coder")

    assert agent.model == "opus"
    assert agent.tools == ["Read", "Edit"]
    assert agent.effort == "medium"
    assert agent.budget_usd == Decimal(4)
    assert agent.instructions == "Never edit tests."


@pytest.mark.parametrize(
    ("key", "line"),
    [
        ("name", "name: coder\n"),
        ("description", "description: Writes the code.\n"),
        ("permissionMode", "permissionMode: auto\n"),
        ("hooks", "hooks: {}\n"),
        ("background", "background: true\n"),
        ("disallowedTools", "disallowedTools: [Bash]\n"),
        ("skills", "skills: [factory-rules]\n"),
    ],
)
def test_a_key_the_runner_does_not_apply_is_refused(agent_home: Path, key: str, line: str) -> None:
    _assert_refused_for(_refused(agent_home, APPLIED + line), key)


@pytest.mark.parametrize(
    ("key", "line"),
    [("colour", "colour: red\n"), ("Model", "Model: opus\n")],
    ids=["unknown", "another-case"],
)
def test_an_unknown_key_or_a_key_in_another_case_is_refused(
    agent_home: Path, key: str, line: str
) -> None:
    _assert_refused_for(_refused(agent_home, APPLIED + line), key)


def test_the_first_unapplied_key_in_the_file_is_named(agent_home: Path) -> None:
    error = _refused(agent_home, f"hooks: {{}}\n{APPLIED}description: Writes the code.\n")

    _assert_refused_for(error, "hooks")


@pytest.mark.parametrize(
    "front_matter",
    [
        "colour: red\ntools: [Read]\nbudget_usd: 4\n",
        "model: opus\ntools: [Read]\ncolour: red\nbudget_usd: 0\n",
    ],
    ids=["no-model", "budget-zero"],
)
def test_an_unapplied_key_is_refused_before_the_applied_keys_are_validated(
    agent_home: Path, front_matter: str
) -> None:
    _assert_refused_for(_refused(agent_home, front_matter), "colour")
