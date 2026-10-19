---
stage: review
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 258
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T09:52:14.306671Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T09:52:14.312636Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T09:52:36.619506Z'
  stage: intake
  run: 972e65115689495ab8c4eb281fa6d063
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T09:52:56.964322Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T10:00:51.424988Z'
  stage: tests
  run: 3241096e02644d168513d42fdf220417
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T10:01:12.394716Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T10:04:40.080092Z'
  stage: doing
  run: 573612d9d583433bb80918dbb882986d
- number: 8
  speaker: factory
  kind: stall
  at: '2026-10-19T10:04:40.102412Z'
  stage: doing
  run: 573612d9d583433bb80918dbb882986d
  reason: check_red
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T10:05:02.271823Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-19T10:07:18.361173Z'
  stage: doing
  run: 8645df2a9d354815849bb271b4988a02
---

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
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names `OpencodeRuntime.__init__` with the new last keyword `provider_limit: ProviderLimit | None`, the `run_streaming` callback, `resume_budget`, `resumed_result`, `FINISH_MESSAGE` from `agent_launch`, `limit_in_text`, `named_wait` and the kill point `AGENT_RUN`. Each one is a concrete module or name, and the wiring is correctly left to S0008.
   Criteria: each is testable by one parametrized test function. Every Interface behaviour has a criterion:
   - The budget sum, with the exact-budget case on both sides, is criterion 1.
   - The resume's arguments and sums are 2, and the resume budget stop without a third call is 3.
   - No resume without a session is 4, and the resume time limit is 5.
   - A limit by `statusCode` is 6 and 7, and the non-limit error on both limit settings is 8.
   - A limit by message, with the default limit refusing it, is 9, and a limit on stderr is 10.
   - A limit never read from `text` or `tool_use` is 11.
   - A limit in the resume is 12, and the kill point after a resume is 13.
   Both sides of every rule are covered (stops/passes, limit/no limit).
   Smoke test: runnable. It uses a stand-in `opencode` and the public API, with the 30-second waits bounded by the 20-second checks. The `Expect:` line is checkable: 0.6+0.6 stops at the budget, the resume adds 0.1 for a cost of 1.3, and the third call gives `provider_limit 420.0 None ses_smoke`.
   Architecture: the work lies in the adapters layer (`opencode_runtime`), reuses `agent_launch`, the process module's `run_streaming` and the domain's `resumed_result` and provider-limit helpers, and calls no tool outside the one wrapper. Wiring stays in `entry` (S0008).
   Scope: within F0020's S0006 scope line (budget stop and resume, provider limit while streaming). The waiting and continuing after a limit is left to S0007, and nothing in the feature's Out of scope is touched.
4. factory: started tests as self.
5. tester: I wrote the tests for criteria 1 to 13 in two files. Both use the stand-in and the event builders of `tests/adapters/opencode_stand_in.py` by import. Each stopped stand-in plays its events in `stdout_before_wait` and then waits 30 seconds. Every elapsed time is checked against 20 seconds.

   - criterion 1: tests/adapters/test_opencode_budget.py::test_a_call_is_stopped_once_its_summed_cost_passes_the_budget (rows at-the-budget, past-the-budget)
   - criterion 2: tests/adapters/test_opencode_budget.py::test_the_resume_continues_the_session_with_the_finish_message_and_sums_both_calls
   - criterion 3: tests/adapters/test_opencode_budget.py::test_a_resume_past_its_own_budget_ends_the_run_by_budget_without_a_third_call
   - criterion 4: tests/adapters/test_opencode_budget.py::test_a_budget_stop_without_a_known_session_is_not_resumed
   - criterion 5: tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit
   - criterion 6: tests/adapters/test_opencode_provider_limit.py::test_a_limit_error_after_a_step_ends_the_run_at_once_with_its_wait_and_session
   - criterion 7: tests/adapters/test_opencode_provider_limit.py::test_a_limit_error_before_any_step_ends_the_run_without_measures
   - criterion 8: tests/adapters/test_opencode_provider_limit.py::test_an_error_that_is_no_limit_does_not_stop_the_call (rows 500-default-limit, 428-limit-429)
   - criterion 9: tests/adapters/test_opencode_provider_limit.py::test_an_error_without_a_status_is_a_limit_when_its_message_holds_the_pattern (rows pattern, default-limit)
   - criterion 10: tests/adapters/test_opencode_provider_limit.py::test_a_limit_line_on_standard_error_ends_the_run_at_once_without_a_wait
   - criterion 11: tests/adapters/test_opencode_provider_limit.py::test_a_limit_in_the_agent_s_text_or_a_tool_s_output_stops_nothing (rows text, tool-use)
   - criterion 12: tests/adapters/test_opencode_provider_limit.py::test_a_limit_in_the_resume_ends_the_run_by_the_limit_with_both_calls_costs
   - criterion 13: tests/adapters/test_opencode_budget.py::test_the_kill_point_is_reached_once_for_a_resumed_run
   - criteria 14 and 15: no test (`make check` and the docs).

   **Files created:**
   - `tests/adapters/test_opencode_budget.py`
   - `tests/adapters/test_opencode_provider_limit.py`

   I changed no earlier test file. The budget file imports the runtime builder `_runtime` from `tests/adapters/test_opencode_runtime.py`. The provider-limit file imports `RESUME_REPLY` and `_over_budget` from the budget file. It has its own builder, which passes `provider_limit=`.

   **Choices that stay within the criteria:**
   - The stand-in prints standard error only after its wait. So for criterion 10, a small wrapper executable in `tmp_path` writes the line to standard error and then execs the stand-in.
   - The stand-in's `error` builder always sets `statusCode`. So for criterion 9, the test drops that key from the built event's JSON instead of copying the builder.
   - The token sums in criterion 2 are what the runtime already counts for one step of the stand-in's builders (input 10, output 5 + 2 reasoning, cache read 100, cache write 20), times 4.

   **Test run:** one `make test`; I saw only its last lines. They list failures in the budget file, and `make test` ended with an error, which is the expected red. Every module imports: `factory.adapters.agent_launch.FINISH_MESSAGE`, `factory.domain.provider_limits.ProviderLimit`, `factory.adapters.opencode_runtime.OpencodeRuntime` and `factory.domain.kill_points`.
   - The budget tests fail on the result: the run is never stopped, so the call count or end reason is wrong.
   - The provider-limit tests should fail because `OpencodeRuntime` does not yet take the `provider_limit` keyword. The output I saw did not show those lines, so this is my expectation, not a confirmed result.

   `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/adapters/test_opencode_budget.py::test_the_kill_point_is_reached_once_for_a_resumed_run
6. factory: started doing as self.
7. coder: I built the budget stop, the resume and the provider-limit stop in `src/factory/adapters/opencode_runtime.py`. No other source file changed. The tester's tests in `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_provider_limit.py` pass unchanged, and `make check` is green.

   **How it works**
   - A small per-call class, `_Watch`, is the callback of `run_streaming`.
     - On standard output it parses each line as an event. It adds `Decimal(str(cost))` of each `step_finish` and stops when the sum is greater than the call's budget.
     - It stops at once on an `error` event whose `statusCode` is the limit's status or whose message the limit is in (`limit_in_text`). That check, `_limit_message`, reads only `error` events, so `text` and `tool_use` events never count as a limit.
     - On standard error it stops on any line the limit is in.
     - It records why it stopped and the text of the limit.
   - `_result` reads that record:
     - A stop ends `budget` or `provider_limit` with the measures of the events read.
     - `limit_wait` is `named_wait` of the limit text.
     - A time limit still comes first.
   - `_call` now builds the `_Watch` and returns the call's `AgentRunResult` instead of the `ProcessResult`.
   - `run` resumes once when the first call ended `budget` and its session is known. `_resume` follows `ClaudeCodeRuntime._resume`:
     - It uses what is left of the time limit, or returns `time_limit` when nothing is left.
     - The resume request is a `model_copy` of the request, with `prompt=FINISH_MESSAGE`, `resume_session=<session>` and `time_limit=left`. The existing `_opencode_argv` therefore puts `--session` before the prompt.
     - The budget is `resume_budget(budget_usd)`, and the result is `resumed_result(first, second)`.
   - The run files are removed in the `finally` after both calls. `finished_run` reaches `AGENT_RUN` once.
   - The new keyword `provider_limit` comes last; `None` means `ProviderLimit()`.
   - `_start` takes an optional `on_line` in place of the `streaming` flag. The no-op `_never_stop` is gone.
   - `_events` now uses a new `_event(line)` parser, which the watch shares.

   **Main choice and the alternative I rejected**
   - I chose a stateful watch object per call: it keeps the running sum and the reason it stopped, and the result reads both afterwards.
   - I rejected reading the reason for the stop again from the collected output after the kill. That would repeat the limit and budget logic and could disagree with what actually stopped the call (for example, a budget passed and a later limit line both in the buffer).

   **Refactor:** after `make check` was green I reshaped the limit check into `_limit_message`, which returns the message or `None`, and ran `make check` again; it was green. Reading the diff as a reviewer, nothing else needed changing.

   **Noticed, not touched**
   - `_resume`'s structure matches `ClaudeCodeRuntime._resume` (time left, then a result of `time_limit` or a second call, then `resumed_result`). `make duplicates` may report the two as similar code. The arguments differ, so sharing a helper would mean a callback; I left it as it is.
   - `_Watch.stopped_by` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
   - Every line on standard error is checked against the limit. With the default limit, any stderr line holding the whole number 428 stops the call, as the interface says.
   - The journal did not change the meaning of the task.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/entry/check_story.py                   92      1     18      1    98%   161
   src/factory/entry/confine.py                       70      1      8      1    97%   110
   src/factory/entry/contract.py                      28      1      6      1    94%   41
   src/factory/entry/guard.py                         37      1     10      1    96%   56
   src/factory/entry/health.py                        33      1     10      1    95%   48
   src/factory/entry/run.py                           71      1      4      1    97%   170
   src/factory/entry/watch.py                         52      3      6      2    91%   82-83, 87
   -------------------------------------------------------------------------------------------
   TOTAL                                            8522     61   1748     32    99%

   103 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.04%
   =========================== short test summary info ============================
   FAILED tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]
   make: *** [Makefile:75: test] Error 1
9. factory: started doing as self.
10. coder: The previous run's implementation in `src/factory/adapters/opencode_runtime.py` is unchanged and still the work: a per-call `_Watch` is the `run_streaming` callback, a budget stop resumes once by session through `_resume`, and a limit stop ends `provider_limit`. Entry 7 describes it. The tester's `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_provider_limit.py` pass unchanged.

    **Why it stalled, and what I did**
    - The stall in entry 8 was `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]`. That test belongs to another story, and this story touched neither it nor `make_commands`.
    - It passes when its module runs alone. A fresh `make check` is green (`test: green (37.1 s)`, `check: green`).
    - I take the failure to be a one-off under the parallel workers, not a fault of this work. I changed no code for it.

    **Main choice and the alternative I rejected** (unchanged from entry 7)
    - Chosen: a stateful watch object per call, which records why it stopped. The result reads that record afterwards.
    - Rejected: working out the stop reason again from the collected output after the kill. That would repeat the budget and limit rules and could disagree with what actually stopped the call.

    **Refactor:** I read the diff against `main` as a reviewer would. Nothing needed changing.

    **Noticed, not touched**
    - The flaky row above, in `tests/adapters/test_make_commands.py`. If it fails again, it is worth a story of its own.
    - `_Watch.stopped_by` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
    - `_resume` has the same shape as `ClaudeCodeRuntime._resume`, so `make duplicates` may report the two as similar code.
    - The private `_limit_message` and `_Watch` keep short docstrings, which CLAUDE.md leaves out for private names. I kept them because they state the return contract.

    The journal did not change the meaning of the task.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 35 known, 1 gone
