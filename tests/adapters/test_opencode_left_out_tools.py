"""The opencode runtime leaves out `Skill` and still refuses every other unmapped tool."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import StandInCall, Step, read_calls
from adapters.opencode_stand_in import (
    MODELS,
    opencode_request,
    result_text,
    stand_in_runtime,
    stdout,
    step_finish,
    step_start,
    text,
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

REPLY = stdout(step_start(), text(result_text()), step_finish())
SHIPPED_MODELS = {**MODELS, "opus": "anthropic/claude-opus-5-5"}


def _tools_of(call: StandInCall, agent: str) -> dict[str, bool]:
    config = json.loads(call.files[call.environment[CONFIG_VARIABLE]])
    tools: dict[str, bool] = config["agent"][f"factory-{agent}"]["tools"]
    return tools


@pytest.mark.parametrize(
    ("tools", "enabled"),
    [
        pytest.param(("Read", "Skill"), {"read"}, id="read-and-skill"),
        pytest.param(("Skill",), set(), id="skill-alone"),
    ],
)
def test_skill_turns_on_no_opencode_tool_and_is_not_refused(
    tmp_path: Path, tools: tuple[str, ...], enabled: set[str]
) -> None:
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY)])

    result = runtime.run(opencode_request(tmp_path / "work", tools=tools))

    assert result.end_reason == "completed"
    [call] = read_calls(tmp_path / "bin")
    assert _tools_of(call, "coder") == {name: name in enabled for name in OPENCODE_TOOLS}


def test_another_tool_without_an_opencode_name_is_still_refused_before_anything_starts(
    tmp_path: Path,
) -> None:
    runtime = stand_in_runtime(tmp_path, [Step(stdout=REPLY)])

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(opencode_request(tmp_path / "work", tools=("Read", "NotebookEdit")))

    assert raised.value.detail == "the opencode runtime has no tool for NotebookEdit"
    assert read_calls(tmp_path / "bin") == []


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_each_shipped_agent_runs_with_its_tools_but_skill(
    tmp_path: Path, agent: ShippedAgent
) -> None:
    executable = write_opencode(tmp_path / "bin", [Step(stdout=REPLY)])
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
