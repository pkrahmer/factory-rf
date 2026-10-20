"""The `claude -p` runtime, against a stand-in executable written into a temporary directory."""

import json
import time
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import StandInCall, Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import ENTRY_DESCRIPTION, ClaudeCodeRuntime
from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
    AgentRunResult,
    GuardSettings,
    PermissionDenial,
    TokenCounts,
)
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints

LIMIT = timedelta(seconds=30)
SWITCHES = {
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}
RUN_FILES = ("instructions-*.md",)


def _reply(**changes: object) -> str:
    reply: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 3,
        "total_cost_usd": 0.25,
        "duration_ms": 1200,
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


def _without(*keys: str) -> str:
    reply = json.loads(_reply())
    for key in keys:
        del reply[key]
    return json.dumps(reply)


def _guard(tmp_path: Path) -> GuardSettings:
    return GuardSettings(
        root=tmp_path / "work",
        write_paths=["src/", "tests/"],
        protected_paths=["factory/"],
    )


def _request(
    tmp_path: Path,
    *,
    effort: str | None = "high",
    tools: tuple[str, ...] = ("Read", "Edit"),
    guard: bool = True,
    environment: dict[str, str] | None = None,
    time_limit: timedelta = LIMIT,
) -> AgentRunRequest:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    agent = AgentDefinition(
        name="coder",
        model="sonnet",
        tools=list(tools),
        effort=effort,
        budget_usd=Decimal("3"),
        instructions="Write the code.\nKeep it small.",
    )
    return AgentRunRequest(
        agent=agent,
        prompt="Stage: doing",
        allowed_decisions=["review", "doing", "question"],
        time_limit=time_limit,
        working_directory=work,
        environment={} if environment is None else environment,
        guard=_guard(tmp_path) if guard else None,
    )


def _runtime(
    tmp_path: Path,
    steps: list[Step],
    kill_points: KillPoints | None = None,
    state: Path | None = None,
) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    return ClaudeCodeRuntime(str(executable), state or tmp_path / "state", kill_points)


def _run(tmp_path: Path, stdout: str, exit_status: int = 0) -> AgentRunResult:
    runtime = _runtime(tmp_path, [Step(stdout=stdout, exit_status=exit_status)])
    return runtime.run(_request(tmp_path))


def _only_call(tmp_path: Path) -> StandInCall:
    calls = read_calls(tmp_path / "bin")
    assert len(calls) == 1
    return calls[0]


def _after(arguments: list[str], flag: str) -> str:
    return arguments[arguments.index(flag) + 1]


def _left_over(state: Path) -> list[Path]:
    if not state.exists():
        return []
    return [path for pattern in RUN_FILES for path in state.glob(pattern)]


def test_call_passes_every_flag_in_order(tmp_path: Path) -> None:
    state = tmp_path / "state"
    _runtime(tmp_path, [Step(stdout=_reply())]).run(_request(tmp_path))

    arguments = _only_call(tmp_path).arguments
    session = _after(arguments, "--session-id")

    assert str(uuid.UUID(session)) == session
    assert arguments == [
        "-p",
        "Stage: doing",
        "--model",
        "sonnet",
        "--effort",
        "high",
        "--tools",
        "Read,Edit",
        "--session-id",
        session,
        "--append-system-prompt-file",
        str(state / f"instructions-{session}.md"),
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "--strict-mcp-config",
        "--max-budget-usd",
        "3",
        "--output-format",
        "json",
        "--json-schema",
        _after(arguments, "--json-schema"),
    ]
    mode = arguments.index("--permission-mode")
    assert arguments[mode : mode + 4] == [
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
    ]


def test_call_without_effort_guard_or_tools_leaves_those_flags_out(tmp_path: Path) -> None:
    request = _request(tmp_path, effort=None, tools=(), guard=False)
    _runtime(tmp_path, [Step(stdout=_reply())]).run(request)

    arguments = _only_call(tmp_path).arguments

    assert "--effort" not in arguments
    assert "--settings" not in arguments
    assert _after(arguments, "--tools") == ""


def test_json_schema_asks_for_an_allowed_decision_and_an_entry(tmp_path: Path) -> None:
    _runtime(tmp_path, [Step(stdout=_reply())]).run(_request(tmp_path))

    schema = json.loads(_after(_only_call(tmp_path).arguments, "--json-schema"))

    assert schema == {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["review", "doing", "question"]},
            "entry": {"type": "string", "description": ENTRY_DESCRIPTION},
        },
        "required": ["decision", "entry"],
        "additionalProperties": False,
    }


def test_call_runs_in_the_requests_working_directory(tmp_path: Path) -> None:
    _runtime(tmp_path, [Step(stdout=_reply())]).run(_request(tmp_path))

    directory = _only_call(tmp_path).working_directory

    assert directory.resolve() == (tmp_path / "work").resolve()


def test_call_gets_only_the_requests_environment_and_the_switches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_LEAK_PROBE", "leaked")
    given = {"LC_ALL": "C.UTF-8", "TOKEN_PROBE": "x"}
    runtime = _runtime(tmp_path, [Step(stdout=_reply()), Step(stdout=_reply())])

    runtime.run(_request(tmp_path, environment=given))
    runtime.run(_request(tmp_path, environment={}))
    first, second = read_calls(tmp_path / "bin")

    assert set(first.environment) <= {*given, *SWITCHES, "LC_CTYPE"}
    assert {key: first.environment.get(key) for key in given} == given
    assert {key: first.environment.get(key) for key in SWITCHES} == SWITCHES
    assert "FACTORY_LEAK_PROBE" not in first.environment
    assert "PATH" not in second.environment


@pytest.mark.parametrize("state_name", ["state", "state dir"])
def test_call_sees_the_instructions_file_and_no_guard_or_hooks_file(
    tmp_path: Path, state_name: str
) -> None:
    state = tmp_path / state_name
    request = _request(tmp_path)
    _runtime(tmp_path, [Step(stdout=_reply())], state=state).run(request)

    call = _only_call(tmp_path)
    session = _after(call.arguments, "--session-id")

    assert call.files[str(state / f"instructions-{session}.md")] == request.agent.instructions
    assert str(state / f"guard-{session}.json") not in call.files
    assert str(state / f"hooks-{session}.json") not in call.files


def test_run_files_are_removed_after_a_result(tmp_path: Path) -> None:
    state = tmp_path / "state"
    _runtime(tmp_path, [Step(stdout=_reply())]).run(_request(tmp_path))

    assert _only_call(tmp_path).files
    assert _left_over(state) == []


def test_run_files_are_removed_after_an_injected_kill(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    state = tmp_path / "state"
    kill_points.arm(KillPoint.AGENT_RUN)
    runtime = _runtime(tmp_path, [Step(stdout=_reply())], kill_points)

    with pytest.raises(InjectedKill):
        runtime.run(_request(tmp_path))

    assert _left_over(state) == []


def test_run_files_are_removed_after_a_missing_executable(tmp_path: Path) -> None:
    state = tmp_path / "state"
    runtime = ClaudeCodeRuntime("/no/such/claude", state)

    with pytest.raises(AgentRuntimeError):
        runtime.run(_request(tmp_path))

    assert _left_over(state) == []


def test_success_reply_gives_decision_entry_and_measures(tmp_path: Path) -> None:
    denial = {"tool_name": "Bash", "tool_input": {"command": "git push"}}

    result = _run(tmp_path, _reply(permission_denials=[denial]))

    assert result.end_reason == "completed"
    assert result.decision == "doing"
    assert result.entry == "Done."
    assert result.turns == 3
    assert result.cost_usd == Decimal("0.25")
    assert result.tokens == TokenCounts(input=10, output=5, cache_read=7, cache_creation=2)
    assert result.permission_denials == [
        PermissionDenial(tool="Bash", detail='{"command": "git push"}')
    ]


def test_duration_is_measured_by_the_factory(tmp_path: Path) -> None:
    step = Step(stdout=_reply(duration_ms=99999), wait_seconds=0.3)

    result = _runtime(tmp_path, [step]).run(_request(tmp_path))

    assert result.duration >= timedelta(seconds=0.3)
    assert result.duration < timedelta(seconds=99.999)


def test_measures_missing_from_the_reply_are_unknown(tmp_path: Path) -> None:
    result = _run(tmp_path, _without("num_turns", "total_cost_usd", "usage"))

    assert result.turns is None
    assert result.cost_usd is None
    assert result.tokens is None


def test_usage_with_input_tokens_only_gives_unknown_tokens(tmp_path: Path) -> None:
    result = _run(tmp_path, _reply(usage={"input_tokens": 10}))

    assert result.tokens is None


@pytest.mark.parametrize(
    "reply",
    [
        _without("structured_output"),
        _reply(structured_output={"decision": "accept", "entry": "Done."}),
        _reply(structured_output={"decision": "doing", "entry": "  \n"}),
    ],
    ids=["no structured output", "decision not allowed", "blank entry"],
)
def test_reply_without_a_usable_decision_is_no_result(tmp_path: Path, reply: str) -> None:
    result = _run(tmp_path, reply)

    assert result.end_reason == "no_result"
    assert result.decision is None
    assert result.entry is None


@pytest.mark.parametrize(
    ("stdout", "exit_status"),
    [(_reply(), 1), ("not json\n", 0)],
    ids=["exit status 1", "not json"],
)
def test_failed_call_died(tmp_path: Path, stdout: str, exit_status: int) -> None:
    result = _run(tmp_path, stdout, exit_status)

    assert result.end_reason == "died"


def test_error_reply_died_with_its_cost(tmp_path: Path) -> None:
    reply = _reply(subtype="error_during_execution", is_error=True, total_cost_usd=0.4)

    result = _run(tmp_path, reply)

    assert result.end_reason == "died"
    assert result.cost_usd == Decimal("0.4")


@pytest.mark.parametrize("missing", ["subtype", "is_error"])
def test_reply_without_a_required_field_died(tmp_path: Path, missing: str) -> None:
    result = _run(tmp_path, _without(missing))

    assert result.end_reason == "died"


def test_call_over_its_time_limit_is_killed_with_unknown_measures(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=_reply(), wait_seconds=60)])
    request = _request(tmp_path, time_limit=timedelta(seconds=1))

    started = time.monotonic()
    result = runtime.run(request)
    elapsed = time.monotonic() - started

    assert elapsed < 6
    assert result.end_reason == "time_limit"
    assert result.decision is None
    assert result.turns is None
    assert result.tokens is None
    assert result.cost_usd is None


@pytest.mark.parametrize(
    ("stdout", "exit_status"), [(_reply(), 0), (_reply(), 1)], ids=["completed", "died"]
)
def test_armed_kill_point_fires_after_the_calls_writes(
    tmp_path: Path, kill_points: KillPoints, stdout: str, exit_status: int
) -> None:
    written = tmp_path / "work" / "written.txt"
    step = Step(writes={str(written): "written"}, stdout=stdout, exit_status=exit_status)
    kill_points.arm(KillPoint.AGENT_RUN)
    runtime = _runtime(tmp_path, [step], kill_points)
    request = _request(tmp_path)

    with pytest.raises(InjectedKill):
        runtime.run(request)

    assert written.read_text(encoding="utf-8") == "written"


def test_unarmed_kill_point_is_reached_once(tmp_path: Path, kill_points: KillPoints) -> None:
    with_points = _runtime(tmp_path, [Step(stdout=_reply()), Step(stdout=_reply())], kill_points)
    without_points = ClaudeCodeRuntime(str(tmp_path / "bin" / "claude"), tmp_path / "state")

    first = with_points.run(_request(tmp_path))
    second = without_points.run(_request(tmp_path))

    assert first.end_reason == "completed"
    assert kill_points.reached(KillPoint.AGENT_RUN) == 1
    assert second.end_reason == "completed"


def test_missing_executable_is_a_runtime_error(tmp_path: Path, kill_points: KillPoints) -> None:
    runtime = ClaudeCodeRuntime("/no/such/claude", tmp_path / "state", kill_points)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(_request(tmp_path))

    assert "/no/such/claude" in raised.value.detail
    assert kill_points.reached(KillPoint.AGENT_RUN) == 0


def test_unwritable_state_directory_is_a_runtime_error(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory", encoding="utf-8")
    state = blocker / "state"
    runtime = _runtime(tmp_path, [Step(stdout=_reply())], kill_points, state=state)

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(_request(tmp_path))

    assert str(state) in raised.value.detail
    assert read_calls(tmp_path / "bin") == []
    assert kill_points.reached(KillPoint.AGENT_RUN) == 0


def test_cache_counts_default_to_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, _reply(usage={"input_tokens": 10, "output_tokens": 5}))

    assert result.tokens == TokenCounts(input=10, output=5, cache_read=0, cache_creation=0)


def test_denial_detail_is_json_with_sorted_keys(tmp_path: Path) -> None:
    denial = {"tool_name": "Edit", "tool_input": {"b": 1, "a": 2}}

    result = _run(tmp_path, _reply(permission_denials=[denial]))

    assert result.permission_denials == [PermissionDenial(tool="Edit", detail='{"a": 2, "b": 1}')]


def _usage(**changes: int) -> dict[str, int]:
    usage = {
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_read_input_tokens": 7,
        "cache_creation_input_tokens": 2,
    }
    usage.update(changes)
    return usage


def _assert_died_without_measures(result: AgentRunResult) -> None:
    assert result.end_reason == "died"
    assert result.turns is None
    assert result.tokens is None
    assert result.cost_usd is None


def test_negative_turns_died_with_unknown_measures(tmp_path: Path) -> None:
    result = _run(tmp_path, _reply(num_turns=-1))

    _assert_died_without_measures(result)


@pytest.mark.parametrize(
    "field",
    [
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    ],
)
def test_negative_token_count_died_with_unknown_measures(tmp_path: Path, field: str) -> None:
    result = _run(tmp_path, _reply(usage=_usage(**{field: -1})))

    _assert_died_without_measures(result)


def test_negative_cost_died_with_unknown_measures(tmp_path: Path) -> None:
    result = _run(tmp_path, _reply(total_cost_usd=-0.01))

    _assert_died_without_measures(result)


def test_zero_measures_are_valid(tmp_path: Path) -> None:
    zero = _usage(
        input_tokens=0, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0
    )

    result = _run(tmp_path, _reply(num_turns=0, total_cost_usd=0, usage=zero))

    assert result.end_reason == "completed"
    assert result.turns == 0
    assert result.tokens == TokenCounts(input=0, output=0, cache_read=0, cache_creation=0)
    assert result.cost_usd == Decimal(0)


def test_reply_with_negative_measures_removes_run_files_and_reaches_the_kill_point(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    state = tmp_path / "state"
    runtime = _runtime(tmp_path, [Step(stdout=_reply(num_turns=-1))], kill_points)

    result = runtime.run(_request(tmp_path))

    assert result.end_reason == "died"
    assert _only_call(tmp_path).files
    assert _left_over(state) == []
    assert kill_points.reached(KillPoint.AGENT_RUN) == 1
