"""Each key of each shipped agent file shows in the call `ClaudeCodeRuntime` makes."""

import json
import re
from datetime import timedelta
from decimal import Decimal

import pytest

from adapters.claude_stand_in import StandInCall, Step, read_calls, write_stand_in
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.work_item_markdown import RuamelYamlHandler, split_front_matter
from factory.domain.agent_runs import AgentRunRequest
from shipped_agents import AGENT_HOME, SHIPPED_AGENTS, SHIPPED_NAMES, ShippedAgent

REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.25,
        "duration_ms": 1200,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)


@pytest.fixture(scope="module")
def calls(tmp_path_factory: pytest.TempPathFactory) -> dict[str, StandInCall]:
    """The one call the runtime makes for each shipped agent, read from its file."""
    reader = FrontmatterAgentDefinitionReader(AGENT_HOME)
    made: dict[str, StandInCall] = {}
    for name in SHIPPED_NAMES:
        root = tmp_path_factory.mktemp(name)
        work = root / "work"
        work.mkdir()
        executable = write_stand_in(root / "bin", [Step(stdout=REPLY)])
        runtime = ClaudeCodeRuntime(str(executable), root / "state", None)
        runtime.run(
            AgentRunRequest(
                agent=reader.read(name),
                prompt="Stage: doing",
                allowed_decisions=["doing", "question"],
                time_limit=timedelta(seconds=30),
                working_directory=work,
            )
        )
        recorded = read_calls(root / "bin")
        assert len(recorded) == 1
        made[name] = recorded[0]
    return made


def _after(call: StandInCall, flag: str) -> str:
    return call.arguments[call.arguments.index(flag) + 1]


def _body(name: str) -> str:
    text = (AGENT_HOME / "agents" / f"{name}.md").read_text(encoding="utf-8")
    split = split_front_matter(RuamelYamlHandler(), text)
    assert split is not None
    return split[1].strip()


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_call_passes_the_agent_model(calls: dict[str, StandInCall], agent: ShippedAgent) -> None:
    assert _after(calls[agent.name], "--model") == agent.model


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_call_passes_the_agent_effort(calls: dict[str, StandInCall], agent: ShippedAgent) -> None:
    assert _after(calls[agent.name], "--effort") == agent.effort


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_call_passes_exactly_the_agent_tools(
    calls: dict[str, StandInCall], agent: ShippedAgent
) -> None:
    passed = {tool for tool in re.split(r"[,\s]+", _after(calls[agent.name], "--tools")) if tool}

    assert passed == set(agent.tools)


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_call_passes_the_agent_budget(calls: dict[str, StandInCall], agent: ShippedAgent) -> None:
    assert Decimal(_after(calls[agent.name], "--max-budget-usd")) == agent.budget_usd


@pytest.mark.parametrize("agent", SHIPPED_AGENTS, ids=SHIPPED_NAMES)
def test_instructions_file_holds_the_agent_body(
    calls: dict[str, StandInCall], agent: ShippedAgent
) -> None:
    call = calls[agent.name]
    instructions = call.files[_after(call, "--append-system-prompt-file")]

    assert _body(agent.name) in instructions
