"""The loader reads the project's own agents through the boundaries and stops on a faulty one."""

import dataclasses
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PipelineLoader
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.errors import AgentDefinitionInvalid, PipelineDefinitionInvalid
from factory.domain.stops import RepositoryStop
from git_support import AGENT_FILE, COLOURED_AGENT_FILE, PIPELINE_YAML, install_agents
from human_clone import HumanClone

CODER_FILE = "factory/agents/coder.md"


@pytest.fixture
def project_boundaries(boundaries: Boundaries, agent_home: Path) -> Boundaries:
    """The boundaries with the project's agents, every role of the definition installed."""
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    return dataclasses.replace(
        boundaries,
        agent_definitions=ProjectAgentDefinitions(boundaries.git, boundaries.agent_definitions),
    )


@pytest.mark.parametrize("project_file", [True, False], ids=["project-coder", "no-coder"])
def test_a_role_without_an_installed_agent_loads_with_the_project_agent_alone(
    project_boundaries: Boundaries, agent_home: Path, human: HumanClone, *, project_file: bool
) -> None:
    (agent_home / "agents" / "coder.md").unlink()
    if project_file:
        human.push_file("main", CODER_FILE, AGENT_FILE)
        project_boundaries.git.fetch()
        definition = project_boundaries.pipeline_reader.parse(PIPELINE_YAML)

        assert PipelineLoader(project_boundaries).load() == definition
    else:
        with pytest.raises(PipelineDefinitionInvalid) as caught:
            PipelineLoader(project_boundaries).load()

        assert caught.value.fault == "role coder: agent is not installed"


def test_a_faulty_project_agent_stops_the_load_until_main_holds_a_valid_one(
    project_boundaries: Boundaries, human: HumanClone, clock: ManualClock
) -> None:
    human.push_file("main", CODER_FILE, COLOURED_AGENT_FILE)
    project_boundaries.git.fetch()
    loader = PipelineLoader(project_boundaries)

    with pytest.raises(AgentDefinitionInvalid):
        loader.load()

    assert project_boundaries.health.read().stops == [
        RepositoryStop(
            scope="repository",
            reason="agent_definition_invalid",
            detail=(
                "coder: factory/agents/coder.md at origin/main: "
                "key not applied by the agent runtime: colour"
            ),
            at=clock.now(),
        )
    ]
    human.push_file("main", CODER_FILE, AGENT_FILE)
    project_boundaries.git.fetch()

    assert loader.load() == project_boundaries.pipeline_reader.parse(PIPELINE_YAML)
    assert project_boundaries.health.read().stops == []
