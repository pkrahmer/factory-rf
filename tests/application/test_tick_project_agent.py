"""A tick runs a stage with the project's own agent of its role, the installed one otherwise."""

import dataclasses
from decimal import Decimal
from pathlib import Path

import pytest

from agent_definition_support import (
    BACKLOG_PATH,
    COMPLETED,
    STORY,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.application.project_agents import ProjectAgentDefinitions
from factory.application.tick import Tick
from factory.entry.wiring import handler_factory
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from stage_run_support import INSTANCE
from wiring_support import ENVIRONMENT

PROJECT_INTAKE = "---\nmodel: opus\ntools: [Read]\nbudget_usd: 2\n---\nThe project's intake.\n"


@pytest.mark.parametrize(
    ("project_file", "model", "tools", "budget", "instructions"),
    [
        pytest.param(True, "opus", ["Read"], Decimal(2), "The project's intake.", id="project"),
        pytest.param(
            False, "sonnet", ["Read", "Write"], Decimal(1), "Do the work.", id="installed"
        ),
    ],
)
def test_the_stage_runs_the_project_agent_of_its_role(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    agent_runtime: FakeAgentRuntime,
    project_file: bool,
    model: str,
    tools: list[str],
    budget: Decimal,
    instructions: str,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    if project_file:
        human.push_file("main", "factory/agents/intake.md", PROJECT_INTAKE)
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    project = dataclasses.replace(
        boundaries,
        agent_definitions=ProjectAgentDefinitions(boundaries.git, boundaries.agent_definitions),
    )
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    Tick(project, INSTANCE, handler_factory(project, INSTANCE, ENVIRONMENT)).run()

    [request] = agent_runtime.requests()
    assert request.agent.name == "intake"
    assert request.agent.instructions == instructions
    assert (request.agent.model, request.agent.tools) == (model, tools)
    assert request.agent.budget_usd == budget
