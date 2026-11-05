"""After the agent, the early stall reads the run alone: no check of the checkout's branch."""

import ast
from datetime import timedelta
from pathlib import Path

import pytest

import factory.pipeline.application.stage
from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.agents.domain.agent_runs import AgentRunResult
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.stage import AfterAgent, AgentAftermath
from factory.pipeline.application.stalls import StallResult
from factory.work.domain.decisions import StallReason
from factory.work.domain.work_item import WorkItemState
from support.definition_support import pipeline_definition
from support.git_support import install_agents
from support.human_clone import HumanClone
from support.stage_run_support import INSTANCE, completed
from support.stall_support import CREATED, launched_stage, open_work_item


@pytest.mark.parametrize(
    ("result", "reason"),
    [
        pytest.param(
            AgentRunResult(end_reason="died", duration=timedelta(minutes=3)), "died", id="died"
        ),
        pytest.param(
            AgentRunResult(end_reason="time_limit", duration=timedelta(minutes=3)),
            "time_limit",
            id="time-limit",
        ),
        pytest.param(completed("doing"), None, id="completed-doing"),
    ],
)
def test_the_early_stall_reads_only_the_runs_own_end(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    result: AgentRunResult,
    reason: StallReason | None,
) -> None:
    install_agents(agent_home, ["tester"])
    open_work_item(boundaries, human, WorkItemState(stage="tests", journal=[CREATED]))
    launched = launched_stage(boundaries, agent_runtime, ScriptedRun(result=result))

    processed = AfterAgent(boundaries, INSTANCE, pipeline_definition(boundaries)).process(launched)

    if reason is None:
        assert isinstance(processed, AgentAftermath)
        assert processed.decision == "doing"
    else:
        assert isinstance(processed, StallResult)
        assert processed.reason == reason


def test_the_stage_module_calls_no_status() -> None:
    path = Path(factory.pipeline.application.stage.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "status"
    ]

    assert calls == []
