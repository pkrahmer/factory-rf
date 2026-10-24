"""The machine's checks of a container instance look for no runtime executable and no make."""

from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from git_support import install_agents
from wiring_support import every_tool

CONTAINER = {
    "stage_environment": "container",
    "dataset": "tank/factory/vm",
    "workspace": "/srv/factory/vm/work",
    "stage_image": "factory-stage:1",
}
CONTAINER_ITEMS = ["tool:git", "tool:uv", "hosting-service", "agents", "agent-runtime-version"]
INLINE_CLAUDE_ITEMS = [
    "tool:git",
    "tool:uv",
    "tool:make",
    "tool:claude",
    "hosting-service",
    "agents",
    "agent-runtime-version",
]
EXTRA = "extra"


@pytest.fixture
def installed(boundaries: Boundaries, agent_home: Path) -> Boundaries:
    """Return boundaries whose agents are installed in the test's agent home."""
    install_agents(agent_home, ["coder"])
    return replace(boundaries, agent_definitions=FrontmatterAgentDefinitionReader(agent_home))


def _extra() -> PreflightItem:
    return PreflightItem(name=EXTRA, passed=True)


@pytest.mark.parametrize(
    ("fields", "names", "executable"),
    [
        pytest.param(
            {**CONTAINER, "agent_runtime": "claude"}, CONTAINER_ITEMS, "claude", id="container"
        ),
        pytest.param(
            {**CONTAINER, "agent_runtime": "opencode", "pinned_opencode_version": "fake"},
            CONTAINER_ITEMS,
            "opencode",
            id="container-opencode",
        ),
        pytest.param({"agent_runtime": "claude"}, INLINE_CLAUDE_ITEMS, None, id="inline"),
    ],
)
def test_a_container_instance_checks_git_and_uv_but_no_make_and_no_runtime_executable(
    installed: Boundaries,
    agent_home: Path,
    *,
    fields: dict[str, object],
    names: list[str],
    executable: str | None,
) -> None:
    asked: list[str] = []

    def which(name: str) -> str | None:
        asked.append(name)
        return every_tool(name)

    settings = InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_home": agent_home,
            "claude_executable": "claude",
            "opencode_executable": "opencode",
            "pinned_agent_version": "fake",
            **fields,
        }
    )

    report = MachineChecks(installed, settings, which, extra=[_extra]).run()

    assert [item.name for item in report.items] == [*names, EXTRA]
    if executable is not None:
        assert executable not in asked
