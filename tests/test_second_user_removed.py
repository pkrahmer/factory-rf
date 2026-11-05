"""The names of the second user are gone from every layer."""

import inspect
from collections.abc import Callable

import pytest

from factory.agents.adapters import agent_launch
from factory.agents.adapters.agent_launch import Starters
from factory.agents.adapters.claude_runtime import ClaudeCodeRuntime
from factory.agents.adapters.opencode_runtime import OpencodeRuntime
from factory.agents.domain.agent_runs import AgentRunRequest
from factory.entry import wiring
from factory.entry.wiring import build_boundaries
from factory.machine.adapters import make_commands
from factory.machine.adapters.make_commands import MakeProjectCommands
from factory.machine.application import preflight
from factory.shared.domain import settings
from factory.shared.domain.settings import InstanceSettings


def _parameters(callable_: Callable[..., object]) -> list[str]:
    return list(inspect.signature(callable_).parameters)


@pytest.mark.parametrize(
    "gone",
    [
        *(
            pytest.param(lambda name=name: hasattr(agent_launch, name), id=f"agent-launch-{name}")
            for name in (
                "SUDO_EXECUTABLE",
                "SUDO_PREFIX",
                "TIMEOUT_EXECUTABLE",
                "SUDO_GRACE",
                "RUN_FILE_MODE",
                "CONTAINER_OS_USER",
                "sudo_prefix",
            )
        ),
        pytest.param(lambda: list(Starters.model_fields) != ["login_files"], id="starters-fields"),
        pytest.param(lambda: hasattr(make_commands, "CommandUser"), id="command-user"),
        pytest.param(lambda: "os_user" in AgentRunRequest.model_fields, id="request-os-user"),
        pytest.param(
            lambda: "agent_user" in InstanceSettings.model_fields, id="settings-agent-user"
        ),
        pytest.param(lambda: hasattr(settings, "AGENT_USER_VARIABLE"), id="agent-user-variable"),
        pytest.param(lambda: hasattr(preflight, "agent_user_item"), id="agent-user-item"),
        pytest.param(
            lambda: hasattr(wiring, "project_command_environment"),
            id="project-command-environment",
        ),
        *(
            pytest.param(
                lambda runtime=runtime: hasattr(runtime, "sudo_executable"),
                id=f"{runtime.__name__}-sudo-executable",
            )
            for runtime in (ClaudeCodeRuntime, OpencodeRuntime)
        ),
        pytest.param(
            lambda: _parameters(build_boundaries) != ["settings", "token", "hosting", "images"],
            id="build-boundaries-parameters",
        ),
        pytest.param(
            lambda: "user" in _parameters(MakeProjectCommands.__init__),
            id="make-commands-user",
        ),
    ],
)
def test_the_second_user_s_names_are_gone(gone: Callable[[], bool]) -> None:
    assert not gone()
