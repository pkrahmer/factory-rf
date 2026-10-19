"""The built boundaries read the project's own agents before the agent home's."""

from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from git_support import AGENT_FILE, install_agents
from human_clone import HumanClone
from wiring_support import CREDENTIAL

PROJECT_CODER = AGENT_FILE.replace("Do the work.", "The project's coder.")


@pytest.mark.parametrize(
    ("name", "instructions"),
    [("coder", "The project's coder."), ("tester", "Do the work.")],
)
def test_the_built_agent_definitions_read_the_project_agents_first(
    remote: Path,
    human: HumanClone,
    local_settings: InstanceSettings,
    *,
    name: str,
    instructions: str,
) -> None:
    human.push_file("main", "factory/agents/coder.md", PROJECT_CODER)
    GitCli(local_settings.checkout).clone(str(remote))
    install_agents(local_settings.agent_home, ["coder", "tester"])

    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    assert isinstance(boundaries.agent_definitions, ProjectAgentDefinitions)
    assert boundaries.agent_definitions.read(name).instructions == instructions
