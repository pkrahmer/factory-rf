"""The `claude -p` runtime's budget resume and version query, against a stand-in executable."""

import json
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import StandInCall, Step, read_calls, write_stand_in
from factory.adapters.claude_runtime import (
    FINISH_MESSAGE,
    VERSION_TIME_LIMIT,
    ClaudeCodeRuntime,
    resume_budget,
)
from factory.application.agent_runtime import AgentRuntime
from factory.domain.agent_runs import (
    AgentDefinition,
    AgentRunRequest,
    GuardSettings,
    PermissionDenial,
    TokenCounts,
)
from factory.domain.errors import AgentRuntimeError
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from run_process_recorder import Recorder
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

LIMIT = timedelta(seconds=30)
RUN_FILES = ("instructions-*.md", "guard-*.json", "hooks-*.json")
VERSION_LINE = "2.1.289 (Claude Code)\n"


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


def _without(reply: str, *keys: str) -> str:
    fields = json.loads(reply)
    for key in keys:
        del fields[key]
    return json.dumps(fields)


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
        guard=GuardSettings(
            root=work, write_paths=["src/", "tests/"], protected_paths=["factory/"]
        ),
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


def _calls(tmp_path: Path) -> list[StandInCall]:
    return read_calls(tmp_path / "bin")


def _after(arguments: list[str], flag: str) -> str:
    return arguments[arguments.index(flag) + 1]


def _left_over(state: Path) -> list[Path]:
    if not state.exists():
        return []
    return [path for pattern in RUN_FILES for path in state.glob(pattern)]


@pytest.mark.parametrize(
    ("budget", "expected"),
    [
        ("4", "1.00"),
        ("3", "0.75"),
        ("2", "0.50"),
        ("1", "0.50"),
        ("0.40", "0.50"),
        ("2.04", "0.51"),
        ("2.02", "0.51"),
        ("2.10", "0.53"),
    ],
)
def test_resume_budget_is_a_quarter_at_least_fifty_cents_rounded_half_up(
    budget: str, expected: str
) -> None:
    result = resume_budget(Decimal(budget))

    assert result == Decimal(expected)
    assert str(result) == expected


def test_budget_stop_resumes_the_same_session_with_the_finish_message(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=_budget_reply()), Step(stdout=_reply())])

    runtime.run(_request(tmp_path))
    first, second = _calls(tmp_path)
    session = _after(first.arguments, "--session-id")
    expected = list(first.arguments)
    expected[expected.index("-p") + 1] = FINISH_MESSAGE
    expected[expected.index("--session-id")] = "--resume"
    expected[expected.index("--max-budget-usd") + 1] = "0.75"

    assert second.arguments == expected
    assert _after(second.arguments, "--resume") == session
    assert "--session-id" not in second.arguments


def test_resumed_call_sees_the_same_run_files_and_none_is_left(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=_budget_reply()), Step(stdout=_reply())])

    runtime.run(_request(tmp_path))
    first, second = _calls(tmp_path)

    assert len(first.files) == 3
    assert second.files == first.files
    assert _left_over(tmp_path / "state") == []


def test_completed_resume_adds_up_the_measures_and_joins_the_denials(tmp_path: Path) -> None:
    push = {"tool_name": "Bash", "tool_input": {"command": "git push"}}
    write = {"tool_name": "Write", "tool_input": {"file_path": "x"}}
    steps = [
        Step(stdout=_budget_reply(permission_denials=[push])),
        Step(stdout=_reply(permission_denials=[write])),
    ]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert result.decision == "doing"
    assert result.entry == "Done."
    assert result.turns == 8
    assert result.cost_usd == Decimal("3.25")
    assert result.tokens == TokenCounts(input=110, output=55, cache_read=77, cache_creation=22)
    assert result.permission_denials == [
        PermissionDenial(tool="Bash", detail='{"command": "git push"}'),
        PermissionDenial(tool="Write", detail='{"file_path": "x"}', path="x"),
    ]


@pytest.mark.parametrize("exit_status", [0, 1], ids=["exit status 0", "exit status 1"])
def test_resume_still_over_budget_ends_as_budget_without_a_third_call(
    tmp_path: Path, exit_status: int
) -> None:
    steps = [
        Step(stdout=_budget_reply()),
        Step(stdout=_budget_reply(), exit_status=exit_status),
        Step(stdout=_reply()),
    ]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "budget"
    assert len(_calls(tmp_path)) == 2


def test_budget_stop_with_exit_status_1_is_resumed(tmp_path: Path) -> None:
    steps = [Step(stdout=_budget_reply(), exit_status=1), Step(stdout=_reply())]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))
    calls = _calls(tmp_path)

    assert result.end_reason == "completed"
    assert len(calls) == 2
    assert _after(calls[1].arguments, "-p") == FINISH_MESSAGE
    assert "--resume" in calls[1].arguments


def test_first_call_ended_by_the_time_limit_is_not_resumed(tmp_path: Path) -> None:
    steps = [Step(stdout=_budget_reply(), wait_seconds=60), Step(stdout=_reply())]
    runtime = _runtime(tmp_path, steps)

    result = runtime.run(_request(tmp_path, time_limit=ROOMY_LIMIT))

    assert result.end_reason == "time_limit"
    assert len(_calls(tmp_path)) == 1


def test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures(
    tmp_path: Path, recorder: Recorder
) -> None:
    steps = [
        Step(stdout=_budget_reply(num_turns=5, total_cost_usd=3.0), wait_seconds=2),
        Step(stdout=_reply(), wait_seconds=60),
    ]
    runtime = _runtime(tmp_path, steps)

    started = time.monotonic()
    result = runtime.run(_request(tmp_path, time_limit=ROOMY_LIMIT))
    elapsed = time.monotonic() - started

    assert elapsed < ROOMY_BOUND_SECONDS
    assert len(_calls(tmp_path)) == 2
    assert result.end_reason == "time_limit"
    assert result.turns is None
    assert result.cost_usd is None
    assert result.tokens is None
    assert result.duration >= timedelta(seconds=2)
    # The resume is handed what the first call left, not the whole limit again.
    resume_limit = recorder.requests[1].time_limit
    assert resume_limit is not None
    assert ROOMY_LIMIT - timedelta(seconds=elapsed) <= resume_limit
    assert resume_limit <= ROOMY_LIMIT - timedelta(seconds=2)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (
            _without(_budget_reply(), "num_turns", "total_cost_usd", "usage"),
            _reply(),
            (3, Decimal("0.25"), TokenCounts(input=10, output=5, cache_read=7, cache_creation=2)),
        ),
        (
            _without(_budget_reply(), "num_turns", "total_cost_usd", "usage"),
            _without(_reply(), "num_turns", "total_cost_usd", "usage"),
            (None, None, None),
        ),
    ],
    ids=["only the resumed call reported", "neither call reported"],
)
def test_measures_a_call_did_not_report_add_nothing(
    tmp_path: Path,
    first: str,
    second: str,
    expected: tuple[int | None, Decimal | None, TokenCounts | None],
) -> None:
    steps = [Step(stdout=first), Step(stdout=second)]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert (result.turns, result.cost_usd, result.tokens) == expected


def test_duration_covers_both_calls(tmp_path: Path) -> None:
    steps = [
        Step(stdout=_budget_reply(), wait_seconds=0.3),
        Step(stdout=_reply(), wait_seconds=0.3),
    ]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert len(_calls(tmp_path)) == 2
    assert result.duration >= timedelta(seconds=0.6)


def test_armed_kill_point_fires_only_after_the_resumed_call(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    written = tmp_path / "work" / "written.txt"
    steps = [
        Step(stdout=_budget_reply()),
        Step(writes={str(written): "written"}, stdout=_reply()),
    ]
    kill_points.arm(KillPoint.AGENT_RUN)
    runtime = _runtime(tmp_path, steps, kill_points)
    request = _request(tmp_path)

    with pytest.raises(InjectedKill):
        runtime.run(request)

    assert len(_calls(tmp_path)) == 2
    assert written.read_text(encoding="utf-8") == "written"


def test_unarmed_kill_point_is_reached_once_for_a_resumed_run(
    tmp_path: Path, kill_points: KillPoints
) -> None:
    steps = [Step(stdout=_budget_reply()), Step(stdout=_reply())]

    result = _runtime(tmp_path, steps, kill_points).run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert kill_points.reached(KillPoint.AGENT_RUN) == 1


@pytest.mark.parametrize(
    "stdout",
    [VERSION_LINE, "\n  \n" + VERSION_LINE],
    ids=["first line", "after blank lines"],
)
def test_version_is_the_first_word_of_the_first_non_blank_line(tmp_path: Path, stdout: str) -> None:
    runtime = _runtime(tmp_path, [Step(stdout=stdout)])

    assert runtime.version() == "2.1.289"
    assert _calls(tmp_path)[0].arguments == ["--version"]


@pytest.mark.parametrize(
    "step",
    [None, Step(stdout=VERSION_LINE, exit_status=1), Step(stdout="")],
    ids=["missing executable", "exit status 1", "prints nothing"],
)
def test_version_that_cannot_be_read_is_a_runtime_error(tmp_path: Path, step: Step | None) -> None:
    if step is None:
        runtime = ClaudeCodeRuntime("/no/such/claude", tmp_path / "state")
    else:
        runtime = _runtime(tmp_path, [step])

    with pytest.raises(AgentRuntimeError):
        runtime.version()


def test_version_query_over_its_limit_is_a_runtime_error(tmp_path: Path) -> None:
    step = Step(stdout=VERSION_LINE, wait_seconds=60)
    runtime = _runtime(tmp_path, [step], version_time_limit=timedelta(seconds=1))

    started = time.monotonic()
    with pytest.raises(AgentRuntimeError):
        runtime.version()
    elapsed = time.monotonic() - started

    assert timedelta(seconds=30) == VERSION_TIME_LIMIT
    assert elapsed < 6


def test_version_query_sees_the_processes_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_VERSION_PROBE", "seen")
    runtime = _runtime(tmp_path, [Step(stdout=VERSION_LINE)])

    runtime.version()

    assert _calls(tmp_path)[0].environment.get("FACTORY_VERSION_PROBE") == "seen"


def test_claude_runtime_inherits_the_agent_runtime_interface() -> None:
    assert issubclass(ClaudeCodeRuntime, AgentRuntime)


def test_measures_only_the_first_call_reported_are_kept(tmp_path: Path) -> None:
    first = _budget_reply(
        num_turns=5, total_cost_usd=3.0, usage={"input_tokens": 10, "output_tokens": 5}
    )
    second = _without(_reply(), "num_turns", "total_cost_usd", "usage")
    steps = [Step(stdout=first), Step(stdout=second)]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert result.turns == 5
    assert result.cost_usd == Decimal("3.0")
    assert result.tokens == TokenCounts(input=10, output=5, cache_read=0, cache_creation=0)


def test_measures_only_the_resumed_call_reported_are_taken(tmp_path: Path) -> None:
    first = _without(_budget_reply(), "num_turns", "total_cost_usd", "usage")
    second = _reply(num_turns=2, total_cost_usd=0.5, usage={"input_tokens": 4, "output_tokens": 1})
    steps = [Step(stdout=first), Step(stdout=second)]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "completed"
    assert result.turns == 2
    assert result.cost_usd == Decimal("0.5")
    assert result.tokens == TokenCounts(input=4, output=1, cache_read=0, cache_creation=0)


def test_budget_stop_with_a_negative_measure_died_and_is_not_resumed(tmp_path: Path) -> None:
    steps = [Step(stdout=_budget_reply(num_turns=-1)), Step(stdout=_reply())]

    result = _runtime(tmp_path, steps).run(_request(tmp_path))

    assert result.end_reason == "died"
    assert result.turns is None
    assert result.tokens is None
    assert result.cost_usd is None
    assert len(_calls(tmp_path)) == 1


@pytest.mark.parametrize(
    ("reply", "end_reason", "expected"),
    [
        (_reply(duration_api_ms=41500), "completed", timedelta(seconds=41.5)),
        (_reply(duration_api_ms=0), "completed", timedelta(0)),
        (_reply(), "completed", None),
        (_reply(duration_api_ms=-1), "died", None),
    ],
    ids=["reported", "zero", "not reported", "negative"],
)
def test_model_duration_is_the_replys_api_time(
    tmp_path: Path, reply: str, end_reason: str, expected: timedelta | None
) -> None:
    result = _runtime(tmp_path, [Step(stdout=reply)]).run(_request(tmp_path))

    assert result.end_reason == end_reason
    assert result.model_duration == expected


@pytest.mark.parametrize(
    "partial",
    ["", _reply(duration_api_ms=41500)],
    ids=["nothing printed", "a whole reply printed"],
)
def test_call_killed_by_the_time_limit_has_no_model_duration(tmp_path: Path, partial: str) -> None:
    steps = [Step(stdout_before_wait=partial, wait_seconds=60, stdout=_reply())]
    runtime = _runtime(tmp_path, steps)

    result = runtime.run(_request(tmp_path, time_limit=ROOMY_LIMIT))

    assert result.end_reason == "time_limit"
    assert result.model_duration is None


@pytest.mark.parametrize(
    ("first", "second", "limit", "expected"),
    [
        (
            Step(stdout=_budget_reply(duration_api_ms=30000)),
            Step(stdout=_reply(duration_api_ms=5000)),
            LIMIT,
            timedelta(seconds=35),
        ),
        (
            Step(stdout=_budget_reply()),
            Step(stdout=_reply(duration_api_ms=5000)),
            LIMIT,
            timedelta(seconds=5),
        ),
        (
            Step(stdout=_budget_reply(duration_api_ms=30000)),
            Step(stdout=_reply()),
            LIMIT,
            timedelta(seconds=30),
        ),
        (Step(stdout=_budget_reply()), Step(stdout=_reply()), LIMIT, None),
        (
            Step(stdout=_budget_reply(duration_api_ms=30000)),
            Step(stdout=_reply(duration_api_ms=5000), wait_seconds=60),
            ROOMY_LIMIT,
            None,
        ),
    ],
    ids=[
        "both known",
        "only the resume known",
        "only the first known",
        "neither known",
        "resume ended by the time limit",
    ],
)
def test_model_duration_of_a_resumed_run_adds_the_known_calls(
    tmp_path: Path, first: Step, second: Step, limit: timedelta, expected: timedelta | None
) -> None:
    runtime = _runtime(tmp_path, [first, second])

    result = runtime.run(_request(tmp_path, time_limit=limit))

    assert len(_calls(tmp_path)) == 2
    assert result.model_duration == expected
