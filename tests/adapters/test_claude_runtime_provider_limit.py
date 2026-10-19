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


@pytest.mark.parametrize(
    ("limit", "step", "end_reason", "limit_wait", "measured"),
    [
        pytest.param(
            None,
            Step(stdout=_error_reply(LIMIT_RESULT)),
            "provider_limit",
            SEVEN_MINUTES,
            True,
            id="error-reply-428",
        ),
        pytest.param(
            None, Step(stdout=_error_reply("API Error: 500")), "died", None, True, id="error-500"
        ),
        pytest.param(
            None,
            Step(stderr="API Error: 428, try again in 7 minutes\n", exit_status=1),
            "provider_limit",
            SEVEN_MINUTES,
            False,
            id="stderr-428-with-wait",
        ),
        pytest.param(
            None,
            Step(stderr="API Error: 428\n", exit_status=1),
            "provider_limit",
            None,
            False,
            id="stderr-428-without-wait",
        ),
        pytest.param(
            ProviderLimit(status=429),
            Step(stderr="API Error: 428, try again in 7 minutes\n", exit_status=1),
            "died",
            None,
            False,
            id="other-status-configured",
        ),
        pytest.param(
            ProviderLimit(message="spend limit"),
            Step(stdout=_error_reply("the spend limit is reached")),
            "provider_limit",
            None,
            True,
            id="message-configured",
        ),
    ],
)
def test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session(
    tmp_path: Path,
    limit: ProviderLimit | None,
    step: Step,
    end_reason: str,
    limit_wait: timedelta | None,
    *,
    measured: bool,
) -> None:
    runtime = _runtime(tmp_path, [step], limit)

    result = runtime.run(_request(tmp_path, None))

    [call] = read_calls(tmp_path / "bin")
    assert result.end_reason == end_reason
    assert result.limit_wait == limit_wait
    assert result.session == _after(call.arguments, "--session-id")
    if measured:
        assert (result.cost_usd, result.turns) == (Decimal("0.01"), 1)
    else:
        assert (result.cost_usd, result.turns, result.tokens) == (None, None, None)


# Prints the limit's status on standard error at once, then outlasts any time limit.
SLOW_LIMIT_SCRIPT = """
import sys
import time

sys.stderr.write("API Error: 428\\n")
sys.stderr.flush()
time.sleep(60)
"""


def test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "bin" / "claude"
    executable.parent.mkdir()
    executable.write_text(f"#!{sys.executable}\n{SLOW_LIMIT_SCRIPT}", encoding="utf-8")
    executable.chmod(0o755)
    runtime = ClaudeCodeRuntime(str(executable), tmp_path / "state")
    request = _request(tmp_path, None).model_copy(update={"time_limit": timedelta(seconds=3)})

    started = time.monotonic()
    result = runtime.run(request)
    elapsed = time.monotonic() - started

    assert result.end_reason == "time_limit"
    assert result.limit_wait is None
    assert elapsed < 20


def test_a_budget_stop_that_names_the_status_ends_budget_and_is_resumed(tmp_path: Path) -> None:
    steps = [Step(stdout=_budget_reply(result="API Error: 428")), Step(stdout=_budget_reply())]
    runtime = _runtime(tmp_path, steps)

    result = runtime.run(_request(tmp_path, None))

    first, second = read_calls(tmp_path / "bin")
    assert result.end_reason == "budget"
    assert _after(second.arguments, "--resume") == _after(first.arguments, "--session-id")


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
