"""An agent file's text parsed without a file: the same definition and faults as a read."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.agent_runs import AgentDefinition
from factory.domain.errors import AgentDefinitionError, AgentDefinitionInvalid
from git_support import AGENT_FILE, COLOURED_AGENT_FILE, write_agent

Outcome = AgentDefinition | tuple[str, str, str, str]


def _outcome(call: Callable[[], AgentDefinition]) -> Outcome:
    try:
        return call()
    except AgentDefinitionError as error:
        key = error.key if isinstance(error, AgentDefinitionInvalid) else ""
        return (type(error).__name__, error.name, error.fault, key)


@pytest.mark.parametrize(
    ("name", "text", "expected"),
    [
        pytest.param("coder", AGENT_FILE, None, id="valid"),
        pytest.param("coder", COLOURED_AGENT_FILE, "AgentDefinitionInvalid", id="unapplied-key"),
        pytest.param("coder", "Do the work.\n", "AgentDefinitionInvalid", id="no-front-matter"),
        pytest.param(
            "coder", "---\nmodel: [\n---\nx\n", "AgentDefinitionInvalid", id="invalid-yaml"
        ),
        pytest.param(
            "coder",
            AGENT_FILE.replace("budget_usd: 1\n", ""),
            "AgentDefinitionInvalid",
            id="no-budget",
        ),
        pytest.param(
            "coder",
            AGENT_FILE.replace("budget_usd: 1\n", "budget_usd: 0\n"),
            "AgentDefinitionInvalid",
            id="zero-budget",
        ),
        pytest.param(
            "coder",
            AGENT_FILE.replace("tools: [Read, Write]\n", "tools: 3\n"),
            "AgentDefinitionInvalid",
            id="wrong-tools",
        ),
        pytest.param("Coder", AGENT_FILE, "AgentDefinitionMissing", id="not-a-name"),
    ],
)
def test_parse_gives_what_read_gives_for_the_same_text_in_a_file(
    agent_home: Path, *, name: str, text: str, expected: str | None
) -> None:
    write_agent(agent_home, "coder", text)
    reader = FrontmatterAgentDefinitionReader(agent_home)

    parsed = _outcome(lambda: reader.parse(name, text))

    assert parsed == _outcome(lambda: reader.read(name))
    if expected is None:
        assert isinstance(parsed, AgentDefinition)
    else:
        assert isinstance(parsed, tuple)
        assert parsed[0] == expected
    if name == "Coder":
        assert parsed == ("AgentDefinitionMissing", "Coder", "not an agent name: Coder", "")
