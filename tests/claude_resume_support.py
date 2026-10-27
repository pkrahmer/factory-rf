"""The replies, request and runtime of the `claude -p` resume tests, shared by its other tests."""

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from adapters.claude_stand_in import Step, write_stand_in
from factory.adapters.claude_runtime import (
    VERSION_TIME_LIMIT,
    ClaudeCodeRuntime,
)
from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
)
from factory.domain.kill_points import KillPoints

LIMIT = timedelta(seconds=30)


def _reply(**changes: object) -> str:
    reply: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 3,
        "total_cost_usd": 0.25,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_input_tokens": 7,
            "cache_creation_input_tokens": 2,
        },
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
    reply.update(changes)
    return json.dumps(reply)


def _budget_reply(**changes: object) -> str:
    reply: dict[str, object] = {
        "type": "result",
        "subtype": "error_max_budget_usd",
        "is_error": True,
        "num_turns": 5,
        "total_cost_usd": 3.0,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 70,
            "cache_creation_input_tokens": 20,
        },
        "permission_denials": [],
    }
    reply.update(changes)
    return json.dumps(reply)


def _request(tmp_path: Path, *, time_limit: timedelta = LIMIT) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    agent = AgentDefinition(
        name="coder",
        model="sonnet",
        tools=["Read", "Edit"],
        effort="high",
        budget_usd=Decimal("3"),
        instructions="Write the code.\nKeep it small.",
    )
    return AgentRunRequest(
        agent=agent,
        prompt="Stage: doing",
        allowed_decisions=["review", "doing", "question"],
        time_limit=time_limit,
        working_directory=work,
        environment={},
    )


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    kill_points: KillPoints | None = None,
    *,
    version_time_limit: timedelta = VERSION_TIME_LIMIT,
) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    return ClaudeCodeRuntime(
        str(executable),
        tmp_path / "state",
        kill_points,
        version_time_limit=version_time_limit,
    )


def _after(arguments: list[str], flag: str) -> str:
    return arguments[arguments.index(flag) + 1]
