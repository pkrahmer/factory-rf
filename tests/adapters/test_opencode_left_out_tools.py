"""The opencode runtime leaves out `Skill` and still refuses every other unmapped tool."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import StandInCall, read_calls
from adapters.opencode_stand_in import (
    MODELS,
    REPLY,
    opencode_request,
    stand_in_runtime,
    write_opencode,
)
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.opencode_runtime import (
    CONFIG_VARIABLE,
    OPENCODE_TOOLS,
    TOOL_NAMES,
    OpencodeRuntime,
)
from factory.domain.agent_runs import AgentRunRequest
from factory.domain.errors import AgentRuntimeError
from shipped_agents import AGENT_HOME, SHIPPED_AGENTS, SHIPPED_NAMES, ShippedAgent

SHIPPED_MODELS = {**MODELS, "opus": "anthropic/claude-opus-5-5"}


def _tools_of(call: StandInCall, agent: str) -> dict[str, bool]:
    config = json.loads(call.files[call.environment[CONFIG_VARIABLE]])
    tools: dict[str, bool] = config["agent"][f"factory-{agent}"]["tools"]
    return tools


@pytest.mark.parametrize(
    ("tools", "expected"),
    [
        pytest.param(("Read", "Skill"), {"read"}, id="read-and-skill"),
        pytest.param(("Skill",), set(), id="skill-alone"),
        pytest.param(
            ("Read", "NotebookEdit"),
            "the opencode runtime has no tool for NotebookEdit",
            id="notebook-edit-refused",
        ),
        pytest.param(("Skill", "Read"), {"read"}, id="skill-first"),
        pytest.param(("Skill", "Read", "Bash"), {"read", "bash"}, id="skill-before-two"),
        pytest.param(("Read", "Skill", "Grep"), {"read", "grep"}, id="skill-in-the-middle"),
        pytest.param(
            ("Skill", "NotebookEdit"),
            "the opencode runtime has no tool for NotebookEdit",
            id="notebook-edit-after-skill-refused",
        ),
    ],
)
def test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused(
    tmp_path: Path, tools: tuple[str, ...], expected: set[str] | str
) -> None:
    runtime = stand_in_runtime(tmp_path, [REPLY])
    request = opencode_request(tmp_path / "work", tools=tools)

    if isinstance(expected, str):
        with pytest.raises(AgentRuntimeError) as raised:
            runtime.run(request)
        assert raised.value.detail == expected
        assert read_calls(tmp_path / "bin") == []
    else:
        result = runtime.run(request)
        assert result.end_reason == "completed"
        [call] = read_calls(tmp_path / "bin")
        assert _tools_of(call, "coder") == {name: name in expected for name in OPENCODE_TOOLS}


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_each_shipped_agent_runs_with_its_tools_but_skill(
    tmp_path: Path, agent: ShippedAgent
) -> None:
    executable = write_opencode(tmp_path / "bin", [REPLY])
    state = tmp_path / "state"
    state.mkdir()
    runtime = OpencodeRuntime(str(executable), state, models=SHIPPED_MODELS)
    work = tmp_path / "work"
    work.mkdir()
    definition = FrontmatterAgentDefinitionReader(AGENT_HOME).read(agent.name)

    result = runtime.run(
        AgentRunRequest(
            agent=definition,
            prompt="Stage: doing",
            allowed_decisions=["doing", "question"],
            time_limit=timedelta(seconds=30),
            working_directory=work,
        )
    )

    assert result.end_reason == "completed"
    [call] = read_calls(tmp_path / "bin")
    enabled = {TOOL_NAMES[tool] for tool in agent.tools if tool != "Skill"}
    assert _tools_of(call, agent.name) == {name: name in enabled for name in OPENCODE_TOOLS}
