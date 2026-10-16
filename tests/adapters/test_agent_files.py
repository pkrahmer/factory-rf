"""The agent files read from the agent home: which agents exist and what each one says."""

from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.agent_runs import AgentDefinition
from factory.domain.errors import (
    AgentDefinitionError,
    AgentDefinitionInvalid,
    AgentDefinitionMissing,
)

CODER_FILE = (
    "---\nmodel: sonnet\ntools: [Read, Write]\neffort: low\nbudget_usd: 0.1\n---\n"
    "The agent's instructions.\n"
)


def _agent_file(front_matter: str, body: str = "Do the work.\n") -> str:
    return f"---\n{front_matter}---\n{body}"


def _agents(agent_home: Path) -> Path:
    agents = agent_home / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    return agents


def _write(agent_home: Path, name: str, text: str) -> None:
    (_agents(agent_home) / f"{name}.md").write_text(text, encoding="utf-8")


def _read(agent_home: Path, name: str, text: str) -> AgentDefinition:
    _write(agent_home, name, text)
    return FrontmatterAgentDefinitionReader(agent_home).read(name)


def _invalid(agent_home: Path, text: str) -> AgentDefinitionInvalid:
    _write(agent_home, "coder", text)
    with pytest.raises(AgentDefinitionInvalid) as caught:
        FrontmatterAgentDefinitionReader(agent_home).read("coder")
    assert caught.value.name == "coder"
    return caught.value


def test_names_are_the_sorted_agent_file_stems_alone(agent_home: Path) -> None:
    agents = _agents(agent_home)
    for name in ["tester", "coder", "README", "Coder"]:
        (agents / f"{name}.md").write_text(CODER_FILE, encoding="utf-8")
    (agents / "notes.txt").write_text(CODER_FILE, encoding="utf-8")
    (agents / "nested.md").mkdir()
    (agents / "sub").mkdir()
    (agents / "sub" / "deep.md").write_text(CODER_FILE, encoding="utf-8")

    assert FrontmatterAgentDefinitionReader(agent_home).names() == ["coder", "tester"]


@pytest.mark.parametrize("agents_is_a_file", [False, True], ids=["absent", "regular-file"])
def test_names_without_an_agents_directory_is_an_error(
    agent_home: Path, *, agents_is_a_file: bool
) -> None:
    agent_home.mkdir()
    if agents_is_a_file:
        (agent_home / "agents").write_text("", encoding="utf-8")

    with pytest.raises(AgentDefinitionError) as caught:
        FrontmatterAgentDefinitionReader(agent_home).names()

    assert caught.value.name == ""
    assert caught.value.fault.startswith("no agents directory at ")


def test_an_agent_file_is_read_into_its_definition(agent_home: Path) -> None:
    agent = _read(agent_home, "coder", CODER_FILE)

    assert agent.name == "coder"
    assert agent.model == "sonnet"
    assert agent.tools == ["Read", "Write"]
    assert agent.effort == "low"
    assert agent.budget_usd == Decimal("0.1")
    assert agent.instructions == "The agent's instructions."


def test_effort_left_out_is_none_and_tools_may_be_empty(agent_home: Path) -> None:
    without_effort = _read(
        agent_home, "coder", _agent_file("model: sonnet\ntools: [Read]\nbudget_usd: 1\n")
    )
    no_tools = _read(agent_home, "tester", _agent_file("model: sonnet\ntools: []\nbudget_usd: 1\n"))

    assert without_effort.effort is None
    assert no_tools.tools == []


def test_front_matter_is_read_as_yaml_one_point_two(agent_home: Path) -> None:
    agent = _read(agent_home, "coder", _agent_file("model: on\ntools: [Read]\nbudget_usd: 1\n"))

    assert agent.model == "on"


def test_a_line_of_hyphens_in_the_body_belongs_to_the_instructions(agent_home: Path) -> None:
    body = "\n\n  First part.\n---\nSecond part.\n\n"
    agent = _read(
        agent_home, "coder", _agent_file("model: sonnet\ntools: [Read]\nbudget_usd: 1\n", body)
    )

    assert agent.instructions == "First part.\n---\nSecond part."


@pytest.mark.parametrize(
    ("content", "fault"),
    [
        (b"No front matter here.\n", "no front matter"),
        (b"---\nmodel: [\n---\nBody.\n", "front matter is not valid YAML"),
        (b"---\n- model\n- tools\n---\nBody.\n", "front matter is not a mapping"),
        (b"---\nmodel: \xff\xfe\n---\nBody.\n", "cannot read: "),
    ],
    ids=["no-front-matter", "not-yaml", "a-list", "not-utf-8"],
)
def test_a_file_that_is_not_an_agent_file_is_invalid_as_a_whole(
    agent_home: Path, content: bytes, fault: str
) -> None:
    (_agents(agent_home) / "coder.md").write_bytes(content)

    with pytest.raises(AgentDefinitionInvalid) as caught:
        FrontmatterAgentDefinitionReader(agent_home).read("coder")

    assert caught.value.name == "coder"
    assert caught.value.key == ""
    if fault.endswith(": "):
        assert caught.value.fault.startswith(fault)
    else:
        assert caught.value.fault == fault


REQUIRED = {"model": "model: sonnet\n", "tools": "tools: [Read]\n", "budget_usd": "budget_usd: 1\n"}


@pytest.mark.parametrize("key", list(REQUIRED))
def test_a_required_key_left_out_is_named(agent_home: Path, key: str) -> None:
    front_matter = "".join(line for name, line in REQUIRED.items() if name != key)

    error = _invalid(agent_home, _agent_file(front_matter))

    assert error.key == key
    assert error.fault == f"missing key: {key}"


@pytest.mark.parametrize(
    ("key", "line"),
    [("model", "model: 3\n"), ("tools", "tools: Read\n"), ("effort", "effort: 3\n")],
)
def test_a_value_of_the_wrong_type_is_named_with_its_key(
    agent_home: Path, key: str, line: str
) -> None:
    lines = {**REQUIRED, key: line}

    error = _invalid(agent_home, _agent_file("".join(lines.values())))

    assert error.key == key
    assert error.fault.startswith(f"invalid {key}:")


@pytest.mark.parametrize("value", ["0", "-1", "high", "true"])
def test_a_budget_that_is_not_a_positive_number_is_refused(agent_home: Path, value: str) -> None:
    front_matter = f"model: sonnet\ntools: [Read]\nbudget_usd: {value}\n"

    error = _invalid(agent_home, _agent_file(front_matter))

    assert error.key == "budget_usd"
    assert error.fault == "budget_usd must be greater than 0"


def test_a_budget_of_one_cent_is_accepted(agent_home: Path) -> None:
    agent = _read(
        agent_home, "coder", _agent_file("model: sonnet\ntools: [Read]\nbudget_usd: 0.01\n")
    )

    assert agent.budget_usd == Decimal("0.01")


def test_a_missing_key_is_reported_before_an_invalid_value(agent_home: Path) -> None:
    error = _invalid(agent_home, _agent_file("tools: Read\nbudget_usd: 1\n"))

    assert error.key == "model"
    assert error.fault == "missing key: model"


def test_an_agent_without_a_file_is_missing(agent_home: Path) -> None:
    (_agents(agent_home) / "coder.md").mkdir()
    reader = FrontmatterAgentDefinitionReader(agent_home)

    for name in ["nobody", "coder"]:
        with pytest.raises(AgentDefinitionMissing) as caught:
            reader.read(name)
        assert caught.value.name == name
        assert caught.value.fault.startswith("no agent file ")


@pytest.mark.parametrize("name", ["../x", "a/b", "Coder"])
def test_a_name_that_is_not_an_agent_name_is_missing_without_reading_a_file(
    agent_home: Path, name: str
) -> None:
    agents = _agents(agent_home)
    (agent_home / "x.md").write_text(CODER_FILE, encoding="utf-8")
    (agents / "a").mkdir()
    (agents / "a" / "b.md").write_text(CODER_FILE, encoding="utf-8")
    (agents / "Coder.md").write_text(CODER_FILE, encoding="utf-8")

    with pytest.raises(AgentDefinitionMissing) as caught:
        FrontmatterAgentDefinitionReader(agent_home).read(name)

    assert caught.value.name == name
    assert caught.value.fault.startswith("not an agent name: ")
