"""The `claude -p` runtime registers no write hook."""

from pathlib import Path

from adapters.claude_stand_in import REPLY, Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from run_layout_support import Layout, run_request


def test_no_run_registers_a_hook(layout: Layout) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])

    result = ClaudeCodeRuntime(str(claude), layout.state).run(run_request(layout))

    [call] = read_calls(layout.stand_in)
    assert "--settings" not in call.arguments
    assert not [name for name in call.files if Path(name).name.startswith(("guard-", "hooks-"))]
    assert result.end_reason == "completed"
