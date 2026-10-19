---
stage: docs
blocked: null
round: 2
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
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-19T10:07:38.706890Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-19T10:09:44.493948Z'
  stage: review
  run: 5ed053eb29224475b599c3219e1ab966
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-19T10:10:04.942715Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-19T10:10:23.126590Z'
  stage: doing
  run: b228dd04a7354b5cac1301aa424e38bd
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-19T10:10:43.305863Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-19T10:15:06.472475Z'
  stage: tests
  run: 08601e91f4654aa494395ff5a1642714
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-19T10:15:26.712569Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-19T10:17:19.478784Z'
  stage: doing
  run: 315429a1dff044458a200e7d896c904a
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-19T10:17:39.749850Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-19T10:18:41.393486Z'
  stage: review
  run: 324a5e848bf04cfda35256b16576470e
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-19T10:19:02.118672Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-19T10:19:22.319085Z'
  stage: doing
  run: f60af536e3f74677874fbc092fe37358
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-19T10:19:42.677829Z'
  stage: tests
- number: 24
  speaker: tester
  kind: result
  at: '2026-10-19T10:21:38.624649Z'
  stage: tests
  run: b8662ff8c9b848b99a51e4a8c5db14f1
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-19T10:21:59.124344Z'
  stage: doing
- number: 26
  speaker: coder
  kind: result
  at: '2026-10-19T10:24:00.842993Z'
  stage: doing
  run: 97298a7489c2426292aa5da2c19de331
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-19T10:24:20.996399Z'
  stage: review
- number: 28
  speaker: reviewer
  kind: result
  at: '2026-10-19T10:25:21.910518Z'
  stage: review
  run: 1fd5867f3c2449118407b8ef0b5ba8e7
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
14. A line on standard error that does not hold the limit (`HTTP 500 Internal Server Error`, and `error 1428`) stops nothing: a stand-in that prints it and then a valid block ends the run `completed`, after one call (rows of the test of criterion 10, beside its limit line).
15. The resume after a budget stop runs with the same run files as the first call, and they are removed only after it: a run that was resumed leaves the state directory empty, and the resume still sees its configuration file (`OPENCODE_CONFIG` names a file that exists while it runs).
16. `make check` stays green.
17. docs: `docs/project-guide/agents.md`, the section *The opencode runtime*: the budget is summed while the run streams and the run is stopped when the sum passes it, then resumed once by session with the finish message and a quarter of the budget (at least $0.50); a provider limit is recognized in an `error` event or a line of standard error, never in the agent's own text or tools' output, and stops the run at once with its session kept. `docs/operator-guide.md`, the agent runtime: an opencode run's budget is kept by the factory, and a run may pass its budget by the cost of one step. `docs/decisions.md`: an entry *opencode's budget is kept by the factory while the run streams*, dated with the story, with the reasons of the feature's decision 11.

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
11. factory: started review as self.
12. reviewer: Findings:
    1. `tests/adapters/test_opencode_provider_limit.py:37` `_runtime`, and the inline build at lines 159-164: a second and a third copy of `_runtime` in `tests/adapters/test_opencode_runtime.py:44`, with only `provider_limit` (and the executable) added. Fix: give the one shared builder a `provider_limit` keyword (and an executable override for the stderr wrapper), and use it in both places.
    2. `tests/adapters/test_opencode_budget.py:20` imports the private `_runtime` from the test module `test_opencode_runtime.py`, and `tests/adapters/test_opencode_provider_limit.py:26` imports the private `_over_budget` and `RESUME_REPLY` from `test_opencode_budget.py`. `WAIT_SECONDS` and `BOUND_SECONDS` are also copied in both new files (`test_opencode_budget.py:25-26`, `test_opencode_provider_limit.py:30-31`). Fix: the tester moves these helpers and constants to one shared place, `tests/adapters/opencode_stand_in.py`, under the standing leave, and both files import them from there.
    3. `tests/adapters/test_opencode_budget.py:144` `test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` does not check that a resume happened. It also passes when the budget stop never fires, because the first call is then killed at the 5-second limit. Fix: also assert `len(read_calls(tmp_path / "bin")) == 2`.
    4. criterion 14 added: it needs its test. The Interface's stderr rule ("on a line of standard error the limit is in") has no test for its failing side, a stderr line that does not hold the limit (`HTTP 500 Internal Server Error`, `error 1428`), which must stop nothing. Pinning it needs no change under `src/`. The test becomes rows of criterion 10's test. The closing criteria are now 15 and 16.

    Checked and sound:
    - `src/factory/adapters/opencode_runtime.py`: the per-call `_Watch` stops the call when the sum is strictly greater than the budget, and reads a limit only from `error` events and stderr lines.
    - `_resume` mirrors `ClaudeCodeRuntime._resume`. It uses `resume_budget` and `resumed_result`, the run files are removed in `finally` after both calls, and `finished_run` reaches `AGENT_RUN` once.
    - The layers hold, and the diff adds no new markers.
    - Criteria 1, 2, 4 and 6 to 13 have tests that pin them.
    - `make duplicates` lists 5 new findings. All of them are blocks that S0004/S0005 shared with `claude_runtime` and that this diff did not add; `_resume` is not reported.

    Earlier tests: the diff adds `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_provider_limit.py` and changes, renames or deletes no test file that `main` holds.
13. factory: started doing as self.
14. coder: All of the reviewer's findings in entry 12 are test changes, so I changed no code. The code the review checked is `src/factory/adapters/opencode_runtime.py`, and it stays as entries 7 and 10 describe. These are the changes for the tester:

    1. **One shared runtime builder.** Give the shared runtime builder a `provider_limit` keyword and an executable override. Use it in place of the copy of `_runtime` at `tests/adapters/test_opencode_provider_limit.py:37` and the inline build at lines 159-164. The copied builder is `_runtime` in `tests/adapters/test_opencode_runtime.py:44`.
    2. **Move the shared helpers and constants.** Under the standing leave, move `_runtime`, `_over_budget`, `RESUME_REPLY`, `WAIT_SECONDS` and `BOUND_SECONDS` to `tests/adapters/opencode_stand_in.py`. Then:
       - `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_provider_limit.py` import them from there and keep no copies.
       - `tests/adapters/test_opencode_runtime.py` uses the moved `_runtime` too. Every test there keeps its name and checks the same thing.
    3. **Check that the resume happened.** In `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, also assert `len(read_calls(tmp_path / "bin")) == 2`.
    4. **Criterion 14 needs only its test.** Add rows to `test_a_limit_line_on_standard_error_ends_the_run_at_once_without_a_wait`, beside its limit line:
       - `HTTP 500 Internal Server Error` on standard error, then a valid block, ends `completed` after one call.
       - The same holds for `error 1428`.

       The current code should already pass these rows, because the limit check on standard error uses `limit_in_text` on whole numbers.

    Main choice: I send the work item back with `tests` instead of `question`. Findings 1 and 2 fall under the standing leave to move a shared test helper. Findings 3 and 4 are this story's own tests, as the review asked.

    The journal did not change the meaning of the task, and the reviewer already renumbered the closing criteria.

    Noticed, not touched:
    - `_Watch.stopped_by` in `src/factory/adapters/opencode_runtime.py` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
    - The row `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]`, which failed once in entry 8, may be flaky under the parallel test workers. If it fails again, it is worth a story of its own.
15. factory: started tests as self.
16. tester: I made the test changes the coder's entry 14 names, which come from the reviewer's findings in entry 12. I changed no code under `src/`. `make lint` is green and `make test` is green (`test: green (39.0 s)`).

    **1 and 2. The shared helpers are in one place.** These moves fall under the standing leave to move a shared test helper. `tests/adapters/opencode_stand_in.py` now holds:
    - `stand_in_runtime(tmp_path, steps, *, settings_file, kill_points, provider_limit, stderr_first)`. This is the old `_runtime` of `test_opencode_runtime.py`, with a `provider_limit` keyword added. `stderr_first` is the executable override: it puts the wrapper that writes a line to standard error and then execs the stand-in in front of the stand-in.
    - `budget_steps` (formerly `_steps`), `over_budget` (formerly `_over_budget`), `RESUME_REPLY`, `RESUME_ENTRY`, `WAIT_SECONDS` and `BOUND_SECONDS`.

    `test_opencode_budget.py` and `test_opencode_provider_limit.py` import these and keep no copies. That removes the copied `_runtime`, the inline build, `_stderr_first` and the imports from other test modules.

    Earlier test files I changed under the standing leave:
    - `tests/adapters/test_opencode_runtime.py`: its `_runtime` was removed, and it uses `stand_in_runtime`.
    - `tests/adapters/test_opencode_resume_session.py`: it imported `_runtime` from `test_opencode_runtime.py` and now imports `stand_in_runtime`.

    Every test in both files keeps its name and checks the same thing.

    **3.** `test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` now also asserts `len(read_calls(tmp_path / "bin")) == 2`.

    **4. Criterion 14 is new rows of criterion 10's test.** The test now has three rows: `limit-line`, `500` (`HTTP 500 Internal Server Error`) and `1428` (`error 1428`). The two new rows play a valid block and must end `completed`.
    - My first `make test` failed on the `limit-line` row. The new call-count check found 0 calls, because the runtime stops on the standard-error line before the stand-in records its call. How many calls get recorded there depends on timing.
    - Every row now asserts `len(read_calls(...)) <= 1`. A `completed` run must have run the stand-in, so for criterion 14's rows that check still means exactly one call.
    - The earlier version of the criterion-10 test checked no call count, so the limit row checks nothing less than before. The second `make test` was green.

    Mapping:
    - criterion 1: tests/adapters/test_opencode_budget.py::test_a_call_is_stopped_once_its_summed_cost_passes_the_budget
    - criterion 2: tests/adapters/test_opencode_budget.py::test_the_resume_continues_the_session_with_the_finish_message_and_sums_both_calls
    - criterion 3: tests/adapters/test_opencode_budget.py::test_a_resume_past_its_own_budget_ends_the_run_by_budget_without_a_third_call
    - criterion 4: tests/adapters/test_opencode_budget.py::test_a_budget_stop_without_a_known_session_is_not_resumed
    - criterion 5: tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit
    - criterion 6: tests/adapters/test_opencode_provider_limit.py::test_a_limit_error_after_a_step_ends_the_run_at_once_with_its_wait_and_session
    - criterion 7: tests/adapters/test_opencode_provider_limit.py::test_a_limit_error_before_any_step_ends_the_run_without_measures
    - criterion 8: tests/adapters/test_opencode_provider_limit.py::test_an_error_that_is_no_limit_does_not_stop_the_call
    - criterion 9: tests/adapters/test_opencode_provider_limit.py::test_an_error_without_a_status_is_a_limit_when_its_message_holds_the_pattern
    - criterion 10: tests/adapters/test_opencode_provider_limit.py::test_a_limit_line_on_standard_error_ends_the_run_at_once_without_a_wait (row limit-line)
    - criterion 11: tests/adapters/test_opencode_provider_limit.py::test_a_limit_in_the_agent_s_text_or_a_tool_s_output_stops_nothing
    - criterion 12: tests/adapters/test_opencode_provider_limit.py::test_a_limit_in_the_resume_ends_the_run_by_the_limit_with_both_calls_costs
    - criterion 13: tests/adapters/test_opencode_budget.py::test_the_kill_point_is_reached_once_for_a_resumed_run
    - criterion 14: tests/adapters/test_opencode_provider_limit.py::test_a_limit_line_on_standard_error_ends_the_run_at_once_without_a_wait (rows 500, 1428)
    - criteria 15 and 16: no test (`make check` and the docs).

    Files: no new files. Changed: `tests/adapters/opencode_stand_in.py`, `tests/adapters/test_opencode_budget.py`, `tests/adapters/test_opencode_provider_limit.py`, `tests/adapters/test_opencode_runtime.py` and `tests/adapters/test_opencode_resume_session.py`. Every module imported; nothing was left that the test run could not import.

    `lint`: lint: green (0.0 s)
    `test`: test: green (38.5 s)
17. factory: started doing as self.
18. coder: Round 1: every finding in the reviewer's entry 12 was a test change, and the tester made them in entry 16. So I changed no code: `src/factory/adapters/opencode_runtime.py` is the same as in entries 7 and 10. With the tester's moved helpers in `tests/adapters/opencode_stand_in.py`, the reworked tests in `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_provider_limit.py` (including criterion 14's rows `500` and `1428`, and criterion 5's two-call check), and the changed `tests/adapters/test_opencode_runtime.py` and `tests/adapters/test_opencode_resume_session.py`, a fresh `make check` is green (`test: green (39.6 s)`, `check: green`).

    What I built (unchanged since entry 7): in `src/factory/adapters/opencode_runtime.py`, a `_Watch` object for each call is the `run_streaming` callback. It adds up the cost of each `step_finish` and stops the call when the total is greater than the budget. It stops the call on a limit found only in `error` events and in lines of standard error. A budget stop with a known session is resumed once through `_resume`, using `resume_budget` and `resumed_result`. The run files are removed after both calls, and `AGENT_RUN` is reached once. The new keyword is `provider_limit`, and `None` means `ProviderLimit()`.

    Main choice (unchanged): `_Watch` keeps a record of why it stopped the call, and the result reads that record. I rejected working the reason out again from the collected output after the kill: that would repeat the budget and limit rules, and it could disagree with what actually stopped the call.

    Refactor: I read the diff against `main` again and nothing needed changing; only the one source file differs.

    Noticed, not touched:
    - `_Watch.stopped_by` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
    - `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]` failed once in entry 8 and passed in this run; it may be flaky under the parallel workers.

    The journal did not change the meaning of the task. The reviewer added criterion 14, which is already in the Description.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 35 known, 1 gone
19. factory: started review as self.
20. reviewer: Findings:
    1. `tests/adapters/test_opencode_runtime.py:245`: the earlier test `test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agent_runtime` was renamed to `..._is_an_agentstand_in_runtime`. This is a slip in replacing `_runtime` with `stand_in_runtime`. The standing leave allows the helper move only if every earlier test keeps its name, so this change goes beyond the leave. Fix: the tester restores the name as it is on `main`.
    2. Criterion 15 added: it needs its test. The Interface says the resume runs "with the same run files, which are removed only after it". The diff builds this in `OpencodeRuntime.run` (`files.remove()` in `finally`, after `_resume`), but no test pins it. `test_the_state_directory_holds_no_file_after_a_run` covers only single calls. Fix: a test in `tests/adapters/test_opencode_budget.py` that runs `[over_budget(), RESUME_REPLY]` and checks two things: the state directory is empty afterwards, and the resume's recorded call saw its `OPENCODE_CONFIG` file's text. Pinning this needs no change under `src/`. The closing criteria are renumbered to 16 and 17.

    Checked and sound:
    - `src/factory/adapters/opencode_runtime.py`:
      - `_Watch` stops a call only when the sum is strictly greater than the budget.
      - It reads a limit only from `error` events (by `statusCode` or `limit_in_text` on the message) and from stderr lines.
      - The stop reason comes after `time_limit` in `_end_reason`.
      - `_resume` uses `resume_budget`, `resumed_result` and what is left of the time limit.
      - `finished_run` reaches `AGENT_RUN` once.
    - The round-0 findings are resolved:
      - The shared `stand_in_runtime`, `over_budget`, `RESUME_REPLY` and the constants are now in `tests/adapters/opencode_stand_in.py`.
      - Criterion 5 now asserts two calls.
      - Criterion 14's rows `500` and `1428` were added.
    - Criteria 1 to 14 have tests that pin them. The journal (entry 18) shows `make check` green after the coder.

    Earlier tests:
    - `tests/adapters/test_opencode_runtime.py`: changed under the standing leave to move a shared test helper (`_runtime` moved to `stand_in_runtime`). The rename in finding 1 goes beyond that leave.
    - `tests/adapters/test_opencode_resume_session.py`: changed under the standing leave to move a shared test helper (it now imports `stand_in_runtime` instead of `_runtime`).

    Notes:
    - `tests/adapters/test_opencode_provider_limit.py:695`: `len(read_calls(...)) <= 1` is weaker than "after one call" for the `500` and `1428` rows. It holds only because a `completed` end implies the stand-in ran. Splitting the expected call count per row would state it directly.
21. factory: started doing as self.
22. coder: Round 2. Both findings in the reviewer's entry 20 are test changes, so I changed no code. `src/factory/adapters/opencode_runtime.py` stays as entries 7 and 10 describe. The tester needs to make these two changes:

    1. **Restore the renamed test.** In `tests/adapters/test_opencode_runtime.py:245`, rename `test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agentstand_in_runtime` back to `test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agent_runtime`, the name `main` has at line 259. The standing leave allows the helper move only if every test keeps its name.
    2. **Criterion 15 needs only its test.** Add a test to `tests/adapters/test_opencode_budget.py` that runs `[over_budget(), RESUME_REPLY]` and asserts two things:
       - the state directory is empty after the run;
       - the resume's recorded call saw the text of its `OPENCODE_CONFIG` file.

       The code already does this: `OpencodeRuntime.run` calls `files.remove()` in its `finally`, after `_resume` (`src/factory/adapters/opencode_runtime.py:586-589`). The new test should pass without any change under `src/`.

    **Main choice:** I end with `tests`, not `question`. Finding 1 undoes a slip in the tester's own move made under the standing leave. Finding 2 adds a criterion that needs only its test.

    **Not touched:** the reviewer's note that the `500` and `1428` rows in `tests/adapters/test_opencode_provider_limit.py` assert `len(read_calls(...)) <= 1`, where they could assert exactly one call per row. That one is up to the tester. Still open from earlier entries:
    - `_Watch.stopped_by` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
    - `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]` may be flaky.

    The journal did not change the meaning of the task. The reviewer already added criterion 15 and renumbered the closing criteria.
23. factory: started tests as self.
24. tester: Round 2, the test change the reviewer asked for in entry 20 and the coder named in entry 22. I made these two changes:

    1. I restored the name of an earlier test in `tests/adapters/test_opencode_runtime.py`. It is `test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agent_runtime` again, as on `main`. It had become `..._agentstand_in_runtime` by mistake when I moved the helper. Compared with `main`, every test in that file now keeps its name. The only difference left is the move of `_runtime` to `stand_in_runtime` in `tests/adapters/opencode_stand_in.py`, which the standing leave to move a shared test helper allows.
    2. I added the test for criterion 15 to `tests/adapters/test_opencode_budget.py`. It runs `[over_budget(), RESUME_REPLY]` and checks three things:
       - the resume's `OPENCODE_CONFIG` names the same file as the first call's;
       - the resume read that file's text, the same text the first call read;
       - the state directory is empty after the run.

       The new import is `CONFIG_VARIABLE` from `factory.adapters.opencode_runtime`. I compare with the first call's file because the criterion says "the same run files as the first call".

    Mapping:
    - criterion 15: `tests/adapters/test_opencode_budget.py::test_the_resume_runs_with_the_first_call_s_run_files_which_are_removed_after_it`
    - criteria 1 to 14: unchanged from entry 16.
    - criteria 16 and 17: no test (`make check` and the docs).

    Files: I created no new files. I changed `tests/adapters/test_opencode_budget.py` and `tests/adapters/test_opencode_runtime.py`. The change to `tests/adapters/test_opencode_runtime.py`, a file an earlier story wrote, only undoes the rename; the helper move stays under the standing leave to move a shared test helper.

    Every module imported. As expected, the new test passes against the existing code: `make test` is green (test: green (39.3 s)), and `make lint` is green.

    Not taken up: the reviewer's note that the `500` and `1428` rows in `tests/adapters/test_opencode_provider_limit.py` check `<= 1` call. This round's change asked only for the two fixes above, so I left that test as it is.

    `lint`: lint: green (0.0 s)
    `test`: test: green (38.6 s)
25. factory: started doing as self.
26. coder: Round 2. The reviewer's two findings in entry 20 were both test changes, and the tester made them in entry 24: the earlier test name in `tests/adapters/test_opencode_runtime.py` is back, and `tests/adapters/test_opencode_budget.py::test_the_resume_runs_with_the_first_call_s_run_files_which_are_removed_after_it` now covers criterion 15. I changed no code. `src/factory/adapters/opencode_runtime.py` is the same as entries 7 and 10 describe. As expected, the new criterion-15 test passes against it, because `OpencodeRuntime.run` removes the run files in its `finally` after `_resume`. A fresh `make check` is green (`test: green (37.2 s)`, `check: green`).

    What I built (unchanged): everything is in `src/factory/adapters/opencode_runtime.py`.
    - Each call gets a `_Watch`, which is the `run_streaming` callback. It adds up the cost of each `step_finish` and stops the call when the total is strictly greater than the call's budget.
    - It also stops the call on a provider limit, which it reads only from `error` events (by `statusCode`, or `limit_in_text` on the message) and from lines of standard error.
    - A budget stop with a known session is resumed once through `_resume`, which uses `resume_budget`, `resumed_result` and what is left of the time limit. The run files are removed after both calls, and `AGENT_RUN` is reached once.
    - The new keyword `provider_limit` defaults to `ProviderLimit()`.

    Main choice (unchanged): `_Watch` records why it stopped the call, and the result reads that record. I rejected working the reason out again from the collected output after the kill: that would repeat the budget and limit rules, and it could disagree with what actually stopped the call.

    Refactor: no code changed this round, so there was nothing to refactor.

    The journal did not change what the task means. The reviewer already added criterion 15 to the Description.

    Noticed, not touched:
    - `_Watch.stopped_by` is typed `EndReason | None`, although it only ever holds `budget` or `provider_limit`.
    - The reviewer's note still stands: the `500` and `1428` rows in `tests/adapters/test_opencode_provider_limit.py` assert `<= 1` call instead of exactly one.
    - `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]` may be flaky under the parallel workers; it passed this run.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 35 known, 1 gone
27. factory: started review as self.
28. reviewer: no findings

    Checked and sound:
    - `src/factory/adapters/opencode_runtime.py`:
      - `_Watch.on_line` adds up the `step_finish` costs as `Decimal` and stops only when the sum is strictly greater than the call's budget.
      - It reads a limit only from `error` events (`_limit_message`: `statusCode` equals the limit's status, or `limit_in_text` on the message) and from lines of standard error.
      - `_end_reason` puts `time_limit` first, then the stop the watch recorded.
      - `_limit_wait` is `named_wait` of the recorded text, and only for `provider_limit`.
      - `run` resumes once, and only on `budget` with a known session.
      - `_resume` matches `ClaudeCodeRuntime._resume`: what is left of the time limit, `FINISH_MESSAGE` and `resume_session` through `model_copy`, `resume_budget` and `resumed_result`.
      - `files.remove()` runs in `finally` after the resume, and `finished_run` reaches `AGENT_RUN` once.
      - The new keyword `provider_limit` comes last and defaults to `ProviderLimit()`.
    - Criteria 1 to 15 each have a test in `tests/adapters/test_opencode_budget.py` or `tests/adapters/test_opencode_provider_limit.py` that pins them, both sides of each rule as rows of one parametrized test:
      - at the budget and past it (1);
      - a status that is no limit and a limit's status (8);
      - a message limit and the default limit (9);
      - a stderr limit line and the lines `500` and `1428` (10 and 14);
      - `text` and `tool_use` (11).
    - The round-1 findings are resolved:
      - The earlier test name in `tests/adapters/test_opencode_runtime.py` is restored. That file now differs from `main` only by the helper move.
      - Criterion 15 is pinned by `test_the_resume_runs_with_the_first_call_s_run_files_which_are_removed_after_it`. It checks the same `OPENCODE_CONFIG` file, that the resume saw that file's text, and that the state directory is empty afterwards.
    - Layers hold. The diff adds no security marker. The journal (entry 26) has `make check` green after the coder. `make duplicates` reports the same 5 new findings as before, none of them added by this diff.
    - The Description and the docs criterion (17) match what was built.

    Earlier tests:
    - `tests/adapters/test_opencode_runtime.py`: changed under the standing leave to move a shared test helper. Its `_runtime` moved to `stand_in_runtime` in `tests/adapters/opencode_stand_in.py`, and every test keeps its name and what it checks.
    - `tests/adapters/test_opencode_resume_session.py`: changed under the standing leave to move a shared test helper. It imports `stand_in_runtime` instead of `_runtime` from `test_opencode_runtime.py`.
    - `tests/adapters/opencode_stand_in.py`: the shared helper module. No leave was needed: it only adds the moved helpers and constants and leaves what it held as it was.

    Notes:
    - `tests/adapters/test_opencode_provider_limit.py:310`: the rows `500` and `1428` check `len(read_calls(...)) <= 1`, which is weaker than "after one call". It holds only because a `completed` end implies the stand-in ran. An expected call count per row would state it directly.
