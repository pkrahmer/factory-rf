# The opencode run stops at its budget and at a provider limit while it streams

## Description

opencode has no budget flag, and behind the gateway at the human's work a call past the spend limit returns HTTP 428 and plain opencode then waits for someone to type "continue"; a run would spend past its budget, or hang until the stage's `time_limit`. This story makes the opencode runtime act on its events as they stream (S0003): it sums the cost of every `step_finish` and stops the run as soon as the sum passes the agent's budget, then resumes the session once with the finish message and the share the Claude Code runtime gives a resume, as that runtime does with its own budget flag; and it recognizes the provider limit in an `error` event or a line of standard error and stops the run at once with the end reason `provider_limit` (S0005), the session kept and the wait the message names. Everything else the run prints, the agent's text and its tools' output above all, is never taken for a limit. The waiting and the continuing after a limit are the application layer's, in S0007.

## Interface

`factory.adapters.opencode_runtime` (`adapters`):

```python
class OpencodeRuntime(AgentRuntime):
    def __init__(self, ..., provider_limit: ProviderLimit | None = None) -> None: ...   # new keyword, last
```

- `provider_limit` `None` is `ProviderLimit()` (status 428, no message).
- The callback of `run_streaming` sums the cost of each `step_finish` event of the call as it arrives and stops the call when the sum is greater than the call's budget: the agent's `budget_usd` for the first call, `resume_budget(budget_usd)` for a resume. At the budget exactly, the call goes on.
- It stops the call at once, as a provider limit, on an `error` event whose `error.data.statusCode` is the limit's status, or whose `error.data.message` the limit is in (`limit_in_text`); and on a line of standard error the limit is in. It never reads a limit from a `text` or a `tool_use` event or from any other event's fields.
- A call stopped by its budget ends `budget`, with the measures of the events read; a call stopped by a limit ends `provider_limit`, with those measures, `limit_wait` `named_wait` of the message or the line, and the session.
- A run whose first call ends `budget` and whose session is known is resumed once: the words of S0004 and S0005 with `--session <session>` before the prompt and `FINISH_MESSAGE` (of `agent_launch`) as the prompt, within what is left of the request's time limit, as the Claude Code runtime's resume does, with the same run files, which are removed only after it. The run's result is `resumed_result` of the two calls (S0002): a resume stopped by its budget ends the run `budget` without a third call, one stopped by a limit ends it `provider_limit`. Without a known session, a budget stop is the run's result.
- An `error` event that is no limit does not stop the call; the call ends as S0004 says.
- The kill point `AGENT_RUN` is reached once after the whole run, also after a resume.

`factory.entry.wiring` (`entry`): nothing yet; S0008 builds this runtime.

Tests (the tester writes them): `tests/adapters/test_opencode_budget.py`, `tests/adapters/test_opencode_provider_limit.py`, both with the stand-in and the event builders of `tests/adapters/opencode_stand_in.py` (S0004), imported, not copied; a stand-in that is to be stopped plays its events in `stdout_before_wait` and then waits 30 seconds, and every elapsed time is checked against a bound of 20 seconds.

## Acceptance criteria

1. With a budget of 1, steps costing 0.4, 0.4 and 0.2 (a sum of exactly 1.00) followed by a valid block: the call is not stopped and the run is `completed`; with steps of 0.4, 0.4 and 0.21 followed by a 30-second wait, the call is stopped right after the third `step_finish` and the stand-in is called a second time, within 20 seconds (rows of one parametrized test).
2. The resume after a budget stop calls the stand-in with `--session ses_a` before the prompt and the finish message as the prompt; a resume that prints a step of 0.1 and a valid block ends the run `completed` with the decision and entry of the resume, `cost_usd` 1.11, `turns` 4 and both calls' tokens.
3. A resume whose steps sum to more than `resume_budget(1)` (0.30 and 0.25) is stopped and the run ends `budget` with both calls' costs, and the stand-in is called exactly twice.
4. A first call stopped by its budget whose events carry no `sessionID` is not resumed: the run ends `budget` with the call's cost, after one call.
5. A resume that waits 30 seconds after its first step, under a request time limit of 5 seconds, ends the run `time_limit` within 20 seconds.
6. An `error` event with `statusCode` 428 and the message `spend limit reached, try again in 7 minutes` after one step of 0.2, followed by a 30-second wait: the run ends `provider_limit` within 20 seconds, with `cost_usd` 0.2, `limit_wait` 420 seconds and `session` `ses_a`, after one call (no resume).
7. The same `error` event before any step ends the run `provider_limit` without measures and with the event's session.
8. An `error` event with `statusCode` 500 does not stop the call: a stand-in that then exits 1 ends `died`, after its own end (rows: 500 with the default limit; 428 with a runtime built with `ProviderLimit(status=429)`).
9. A runtime built with `ProviderLimit(message="spend limit")` stops on an `error` event without `statusCode` whose message is `the spend limit is reached`; the default limit does not (rows).
10. A line `HTTP 428 Precondition Required` on standard error, followed by a 30-second wait, ends the run `provider_limit` within 20 seconds, its `limit_wait` `None`.
11. A `text` event whose text holds `HTTP 428` and a `tool_use` event whose input and error hold `428` stop nothing, and the run ends as its block says (rows).
12. A limit in the resume after a budget stop ends the run `provider_limit` with both calls' costs and the session.
13. The kill point `AGENT_RUN` is reached once for a run that was resumed.
14. `make check` stays green.
15. docs: `docs/project-guide/agents.md`, the section *The opencode runtime*: the budget is summed while the run streams and the run is stopped when the sum passes it, then resumed once by session with the finish message and a quarter of the budget (at least $0.50); a provider limit is recognized in an `error` event or a line of standard error, never in the agent's own text or tools' output, and stops the run at once with its session kept. `docs/operator-guide.md`, the agent runtime: an opencode run's budget is kept by the factory, and a run may pass its budget by the cost of one step. `docs/decisions.md`: an entry *opencode's budget is kept by the factory while the run streams*, dated with the story, with the reasons of the feature's decision 11.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work" "$d/state"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
here=$(dirname "$0")
n=$(cat "$here/count" 2>/dev/null || echo 0)
n=$((n + 1))
echo "$n" > "$here/count"
printf '%s\n' "$*" >> "$here/arguments"
case "$n" in
1)
  printf '%s\n' '{"type":"step_start","timestamp":1000,"sessionID":"ses_smoke","part":{"type":"step-start"}}' '{"type":"step_finish","timestamp":1100,"sessionID":"ses_smoke","part":{"type":"step-finish","cost":0.6,"tokens":{"input":1,"output":1}}}' '{"type":"step_start","timestamp":1200,"sessionID":"ses_smoke","part":{"type":"step-start"}}' '{"type":"step_finish","timestamp":1300,"sessionID":"ses_smoke","part":{"type":"step-finish","cost":0.6,"tokens":{"input":1,"output":1}}}'
  sleep 30 ;;
2)
  printf '%s\n' '{"type":"step_start","timestamp":2000,"sessionID":"ses_smoke","part":{"type":"step-start"}}' '{"type":"text","timestamp":2050,"sessionID":"ses_smoke","part":{"type":"text","text":"<factory-result>\ndecision: question\nentry:\nStopped at the budget.\n</factory-result>"}}' '{"type":"step_finish","timestamp":2100,"sessionID":"ses_smoke","part":{"type":"step-finish","cost":0.1,"tokens":{"input":1,"output":1}}}' ;;
*)
  printf '%s\n' '{"type":"error","timestamp":3000,"sessionID":"ses_smoke","error":{"name":"APIError","data":{"message":"spend limit reached, try again in 7 minutes","statusCode":428}}}'
  sleep 30 ;;
esac
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.agent_launch import FINISH_MESSAGE
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="anthropic/claude-sonnet-5-5", tools=["Read"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=120), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
runtime = OpencodeRuntime(str(d / "opencode"), d / "state")
started = time.monotonic()
result = runtime.run(request)
print(result.end_reason, result.cost_usd, result.entry, time.monotonic() - started < 20)
calls = (d / "arguments").read_text(encoding="utf-8").splitlines()
print(calls[1].endswith(f"--session ses_smoke {FINISH_MESSAGE}"))
started = time.monotonic()
limited = runtime.run(request)
print(limited.end_reason, limited.limit_wait.total_seconds(), limited.cost_usd, limited.session, time.monotonic() - started < 20)
EOF
```
Expect: three lines, `completed 1.3 Stopped at the budget. True`, `True`, `provider_limit 420.0 None ses_smoke True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
