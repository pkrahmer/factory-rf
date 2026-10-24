"""The machine's checks look for the executable and the pin of the runtime in force."""

from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks
from factory.domain.settings import InstanceSettings
from wiring_support import every_tool

MISMATCH = "the agent runtime reports 1.19.4, the image pins 1.19.3; "


def _settings(agent_home: Path, **fields: object) -> InstanceSettings:
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_home": agent_home,
            "claude_executable": "claude",
            "opencode_executable": "opencode",
            **fields,
        }
    )


@pytest.mark.parametrize(
    ("runtime", "tools"),
    [
        pytest.param(
            "opencode", ["tool:git", "tool:uv", "tool:make", "tool:opencode"], id="opencode"
        ),
        pytest.param("claude", ["tool:git", "tool:uv", "tool:make", "tool:claude"], id="claude"),
    ],
)
def test_the_last_required_tool_is_the_runtime_s_executable(
    installed: Boundaries, agent_home: Path, *, runtime: str, tools: list[str]
) -> None:
    asked: list[str] = []

    def which(name: str) -> str | None:
        asked.append(name)
        return every_tool(name)

    report = MachineChecks(installed, _settings(agent_home, agent_runtime=runtime), which).run()

    assert [item.name for item in report.items[:4]] == tools
    assert asked[:4] == [tool.removeprefix("tool:") for tool in tools]


@pytest.mark.parametrize(
    ("fields", "reported", "passed", "detail"),
    [
        pytest.param(
            {"agent_runtime": "opencode", "pinned_opencode_version": "1.19.3"},
            "1.19.3",
            True,
            None,
            id="opencode-pinned",
        ),
        pytest.param(
            {"agent_runtime": "opencode", "pinned_opencode_version": "1.19.3"},
            "1.19.4",
            False,
            MISMATCH,
            id="opencode-other",
        ),
        pytest.param(
            {"agent_runtime": "opencode", "pinned_agent_version": "1.19.3"},
            "1.19.3",
            False,
            "the image does not pin a version: FACTORY_OPENCODE_VERSION is not set",
            id="opencode-no-pin",
        ),
        pytest.param(
            {"pinned_agent_version": "2.1.296", "pinned_opencode_version": "1.19.3"},
            "2.1.296",
            True,
            None,
            id="claude-pinned",
        ),
        pytest.param(
            {"pinned_opencode_version": "2.1.296"},
            "2.1.296",
            False,
            "the image does not pin a version: FACTORY_CLAUDE_VERSION is not set",
            id="claude-no-pin",
        ),
    ],
)
def test_the_version_item_compares_against_the_pin_of_the_runtime_in_force(
    installed: Boundaries,
    agent_home: Path,
    *,
    fields: dict[str, object],
    reported: str,
    passed: bool,
    detail: str | None,
) -> None:
    boundaries = replace(installed, agent_runtime=FakeAgentRuntime(version=reported))

    report = MachineChecks(boundaries, _settings(agent_home, **fields), every_tool).run()

    item = next(item for item in report.items if item.name == "agent-runtime-version")
    assert item.passed == passed
    if detail is None:
        assert item.detail == ""
    else:
        assert item.detail.startswith(detail)
