"""After the agent, the early stall reads the run alone: no check of the checkout's branch."""

import ast
from datetime import timedelta
from pathlib import Path

import pytest

import factory.application.stage
from definition_support import pipeline_definition
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.stage import AfterAgent, AgentAftermath
from factory.application.stalls import StallResult
from factory.domain.agent_runs import AgentRunResult
from factory.domain.decisions import StallReason
from factory.domain.work_item import WorkItemState
from git_support import install_agents
from human_clone import HumanClone
from stage_run_support import INSTANCE, completed
from stall_support import CREATED, launched_stage, open_work_item


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
    path = Path(factory.application.stage.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "status"
    ]

    assert calls == []
