"""A stage run in the fake world reads its agent from the shipped `agents/agents/<role>.md`."""

import shutil
from pathlib import Path

from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.entry.wiring import handler_factory
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.tick import Tick
from support.agent_definition_support import COMPLETED
from support.git_support import PIPELINE_YAML, install_agents
from support.human_clone import HumanClone
from support.shipped_agents import AGENT_HOME, agent_body
from support.stage_run_support import BACKLOG_PATH, INSTANCE, STORY
from support.wiring_support import ENVIRONMENT

ROLE = "intake"


def test_a_stage_run_reads_its_agent_from_the_agent_folder(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    agent_runtime: FakeAgentRuntime,
) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    shutil.copyfile(AGENT_HOME / "agents" / f"{ROLE}.md", agent_home / "agents" / f"{ROLE}.md")
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    agent_runtime.queue(ScriptedRun(result=COMPLETED))

    Tick(boundaries, INSTANCE, handler_factory(boundaries, INSTANCE, ENVIRONMENT)).run()

    [request] = agent_runtime.requests()
    assert request.agent.name == ROLE
    assert request.agent.instructions.strip() == agent_body(ROLE)
