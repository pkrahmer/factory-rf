"""The loader reads every role's agent file and reports an agent file it refuses."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PIPELINE_REF, PipelineLoader
from factory.domain.errors import AgentDefinitionInvalid, PipelineDefinitionInvalid
from factory.domain.stops import RepositoryStop
from git_support import COLOURED_AGENT_FILE, PIPELINE_YAML, install_agents, write_agent
from human_clone import HumanClone

PIPELINE_FILE = "factory/pipeline.yml"
WITHOUT_CONTRACT = PIPELINE_YAML.replace('contract: "1.0"\n', "")
# The definition lists tester before coder, the reverse of their alphabetical order.
FIRST_ROLE = "tester"
SECOND_ROLE = "coder"


pytestmark = pytest.mark.usefixtures("installed_agents")


def _agent_stop(role: str, clock: ManualClock) -> RepositoryStop:
    return RepositoryStop(
        scope="repository",
        reason="agent_definition_invalid",
        detail=f"{role}: key not applied by the agent runtime: colour",
        at=clock.now(),
    )


def _refused(loader: PipelineLoader, ref: str = PIPELINE_REF) -> AgentDefinitionInvalid:
    with pytest.raises(AgentDefinitionInvalid) as caught:
        loader.load(ref)
    return caught.value


def test_the_agent_file_of_a_later_role_is_read_too(
    boundaries: Boundaries, agent_home: Path
) -> None:
    write_agent(agent_home, SECOND_ROLE, COLOURED_AGENT_FILE)

    error = _refused(PipelineLoader(boundaries))

    assert error.name == SECOND_ROLE
    assert error.key == "colour"


def test_of_two_refused_agent_files_the_first_role_is_named(
    boundaries: Boundaries, agent_home: Path
) -> None:
    for role in [SECOND_ROLE, FIRST_ROLE]:
        write_agent(agent_home, role, COLOURED_AGENT_FILE)

    assert _refused(PipelineLoader(boundaries)).name == FIRST_ROLE


def test_a_missing_agent_is_refused_before_any_agent_file_is_read(
    boundaries: Boundaries, agent_home: Path
) -> None:
    (agent_home / "agents" / f"{SECOND_ROLE}.md").unlink()
    write_agent(agent_home, FIRST_ROLE, COLOURED_AGENT_FILE)

    with pytest.raises(PipelineDefinitionInvalid) as caught:
        PipelineLoader(boundaries).load()

    assert caught.value.fault == f"role {SECOND_ROLE}: agent is not installed"


def test_a_refused_agent_file_on_main_raises_one_stop(
    boundaries: Boundaries, agent_home: Path, clock: ManualClock
) -> None:
    write_agent(agent_home, SECOND_ROLE, COLOURED_AGENT_FILE)
    clock.advance(timedelta(seconds=5))

    _refused(PipelineLoader(boundaries))

    assert boundaries.health.read().stops == [_agent_stop(SECOND_ROLE, clock)]


def test_a_good_load_on_main_clears_the_agent_stop(
    boundaries: Boundaries, agent_home: Path
) -> None:
    write_agent(agent_home, SECOND_ROLE, COLOURED_AGENT_FILE)
    loader = PipelineLoader(boundaries)
    _refused(loader)
    install_agents(agent_home, [SECOND_ROLE])

    loader.load()

    assert boundaries.health.read().stops == []


def test_a_refused_agent_file_after_a_refused_definition_leaves_only_the_agent_stop(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    human: HumanClone,
    checkout: GitCli,
    clock: ManualClock,
) -> None:
    human.push_file("main", PIPELINE_FILE, WITHOUT_CONTRACT)
    checkout.fetch()
    loader = PipelineLoader(boundaries)
    with pytest.raises(PipelineDefinitionInvalid):
        loader.load()
    human.push_file("main", PIPELINE_FILE, PIPELINE_YAML)
    checkout.fetch()
    write_agent(agent_home, SECOND_ROLE, COLOURED_AGENT_FILE)

    _refused(loader)

    assert boundaries.health.read().stops == [_agent_stop(SECOND_ROLE, clock)]


def test_a_refused_agent_file_at_a_commit_leaves_the_health_status_as_it_was(
    boundaries: Boundaries,
    *,
    agent_home: Path,
    checkout: GitCli,
    clock: ManualClock,
) -> None:
    write_agent(agent_home, FIRST_ROLE, COLOURED_AGENT_FILE)
    loader = PipelineLoader(boundaries)
    _refused(loader)
    status = boundaries.health.read()
    install_agents(agent_home, [FIRST_ROLE])
    write_agent(agent_home, SECOND_ROLE, COLOURED_AGENT_FILE)
    clock.advance(timedelta(seconds=5))
    commit = checkout.resolve("origin/main")
    assert commit is not None

    error = _refused(loader, commit)

    assert (error.name, error.key) == (SECOND_ROLE, "colour")
    assert boundaries.health.read() == status
