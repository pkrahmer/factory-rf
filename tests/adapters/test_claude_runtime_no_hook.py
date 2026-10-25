"""The `claude -p` runtime registers no write hook, with or without guard settings."""

from collections.abc import Callable
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_os_user import REPLY
from confine_support import Layout, run_request
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentRunRequest


def _unconfined(layout: Layout, claude: Path) -> ClaudeCodeRuntime:
    return ClaudeCodeRuntime(str(claude), layout.state)


def _guarded(layout: Layout) -> AgentRunRequest:
    return run_request(layout)


def _unguarded(layout: Layout) -> AgentRunRequest:
    return run_request(layout).model_copy(update={"guard": None})


@pytest.mark.parametrize(
    ("runtime_of", "request_of"),
    [
        pytest.param(_unconfined, _guarded, id="unconfined-guarded"),
        pytest.param(_unconfined, _unguarded, id="unconfined-unguarded"),
    ],
)
def test_no_run_registers_a_hook(
    layout: Layout,
    runtime_of: Callable[[Layout, Path], ClaudeCodeRuntime],
    request_of: Callable[[Layout], AgentRunRequest],
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])

    result = runtime_of(layout, claude).run(request_of(layout))

    [call] = read_calls(layout.stand_in)
    assert "--settings" not in call.arguments
    assert not [name for name in call.files if Path(name).name.startswith(("guard-", "hooks-"))]
    assert result.end_reason == "completed"
