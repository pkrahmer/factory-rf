"""The `claude -p` runtime ends a call the provider's spend limit refused as `provider_limit`."""

import json
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_os_user import _request
from adapters.test_claude_runtime_resume import _after, _budget_reply
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.provider_limits import ProviderLimit
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

LIMIT_RESULT = "API Error: 428 spend limit reached, try again in 7 minutes"
SEVEN_MINUTES = timedelta(seconds=420)


def _error_reply(result: str) -> str:
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": True,
            "num_turns": 1,
            "total_cost_usd": 0.01,
            "result": result,
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "permission_denials": [],
        }
    )


def _runtime(
    tmp_path: Path, steps: list[Step], limit: ProviderLimit | None = None
) -> ClaudeCodeRuntime:
    executable = write_stand_in(tmp_path / "bin", steps)
    return ClaudeCodeRuntime(str(executable), tmp_path / "state", provider_limit=limit)


ONE_CALL = (Decimal("0.01"), 1)


@pytest.mark.parametrize(
    ("limit", "steps", "end_reason", "limit_wait", "measures", "resumed"),
    [
        pytest.param(
            None,
            [Step(stdout=_error_reply(LIMIT_RESULT))],
            "provider_limit",
            SEVEN_MINUTES,
            ONE_CALL,
            False,
            id="error-reply-428",
        ),
        pytest.param(
            None,
            [Step(stdout=_error_reply("API Error: 500"))],
            "died",
            None,
            ONE_CALL,
            False,
            id="error-500",
        ),
        pytest.param(
            None,
            [Step(stderr="API Error: 428, try again in 7 minutes\n", exit_status=1)],
            "provider_limit",
            SEVEN_MINUTES,
            None,
            False,
            id="stderr-428-with-wait",
        ),
        pytest.param(
            None,
            [Step(stderr="API Error: 428\n", exit_status=1)],
            "provider_limit",
            None,
            None,
            False,
            id="stderr-428-without-wait",
        ),
        pytest.param(
            ProviderLimit(status=429),
            [Step(stderr="API Error: 428, try again in 7 minutes\n", exit_status=1)],
            "died",
            None,
            None,
            False,
            id="other-status-configured",
        ),
        pytest.param(
            ProviderLimit(message="spend limit"),
            [Step(stdout=_error_reply("the spend limit is reached"))],
            "provider_limit",
            None,
            ONE_CALL,
            False,
            id="message-configured",
        ),
        pytest.param(
            None,
            [Step(stdout=_budget_reply(result="API Error: 428")), Step(stdout=_budget_reply())],
            "budget",
            None,
            (Decimal("6.0"), 10),
            True,
            id="budget-stop-naming-428",
        ),
    ],
)
def test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session(
    tmp_path: Path,
    limit: ProviderLimit | None,
    steps: list[Step],
    end_reason: str,
    limit_wait: timedelta | None,
    *,
    measures: tuple[Decimal, int] | None,
    resumed: bool,
) -> None:
    runtime = _runtime(tmp_path, steps, limit)

    result = runtime.run(_request(tmp_path, None))

    calls = read_calls(tmp_path / "bin")
    session = _after(calls[0].arguments, "--session-id")
    assert result.end_reason == end_reason
    assert result.limit_wait == limit_wait
    assert result.session == session
    assert [_after(call.arguments, "--resume") for call in calls[1:]] == (
        [session] if resumed else []
    )
    if measures is None:
        assert (result.cost_usd, result.turns, result.tokens) == (None, None, None)
    else:
        assert (result.cost_usd, result.turns) == measures


# Records its arguments, prints the limit's status on standard error at once, then outlasts any
# time limit.
SLOW_LIMIT_SCRIPT = """
import json
import sys
import time
from pathlib import Path

(Path(__file__).resolve().parent / "arguments.json").write_text(json.dumps(sys.argv[1:]))
sys.stderr.write("API Error: 428\\n")
sys.stderr.flush()
time.sleep(60)
"""


def test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "bin" / "claude"
    executable.parent.mkdir()
    executable.write_text(f"#!{sys.executable} -B\n{SLOW_LIMIT_SCRIPT}", encoding="utf-8")
    executable.chmod(0o755)
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state")
    request = _request(tmp_path, None).model_copy(update={"time_limit": ROOMY_LIMIT})

    started = time.monotonic()
    result = runtime.run(request)
    elapsed = time.monotonic() - started

    arguments = json.loads((executable.parent / "arguments.json").read_text(encoding="utf-8"))
    assert result.end_reason == "time_limit"
    assert result.limit_wait is None
    assert result.session == _after(arguments, "--session-id")
    assert elapsed < ROOMY_BOUND_SECONDS


def test_a_resume_the_limit_refused_ends_provider_limit_with_both_calls_measures(
    tmp_path: Path,
) -> None:
    steps = [Step(stdout=_budget_reply()), Step(stdout=_error_reply(LIMIT_RESULT))]
    runtime = _runtime(tmp_path, steps)

    result = runtime.run(_request(tmp_path, None))

    first, second = read_calls(tmp_path / "bin")
    session = _after(first.arguments, "--session-id")
    assert result.end_reason == "provider_limit"
    assert result.limit_wait == SEVEN_MINUTES
    assert result.cost_usd == Decimal("3.01")
    assert result.turns == 6
    assert _after(second.arguments, "--resume") == session
    assert result.session == session
