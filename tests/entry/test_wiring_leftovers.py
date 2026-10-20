"""The wiring builds every agent runtime with the command of the leftovers program."""

import sys

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries, leftovers_command
from wiring_support import CREDENTIAL

COMMAND = [sys.executable, "-I", "-m", "factory.entry.leftovers"]


@pytest.mark.parametrize(
    ("agent_runtime", "expected_type", "end_leftovers", "expected"),
    [
        pytest.param("claude", ClaudeCodeRuntime, None, COMMAND, id="claude-default"),
        pytest.param("claude", ClaudeCodeRuntime, False, None, id="claude-off"),
        pytest.param("opencode", OpencodeRuntime, None, COMMAND, id="opencode-default"),
        pytest.param("opencode", OpencodeRuntime, False, None, id="opencode-off"),
    ],
)
def test_the_built_runtime_starts_the_leftovers_program_unless_it_is_turned_off(
    local_settings: InstanceSettings,
    agent_runtime: str,
    expected_type: type[object],
    end_leftovers: bool | None,
    expected: list[str] | None,
) -> None:
    settings = local_settings.model_copy(update={"agent_runtime": agent_runtime})

    if end_leftovers is None:
        boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())
    else:
        boundaries = build_boundaries(
            settings, CREDENTIAL, hosting=FakeHostingService(), end_leftovers=end_leftovers
        )

    runtime = boundaries.agent_runtime
    assert type(runtime) is expected_type
    assert isinstance(runtime, ClaudeCodeRuntime | OpencodeRuntime)
    assert runtime.leftovers == expected
    assert leftovers_command() == COMMAND
