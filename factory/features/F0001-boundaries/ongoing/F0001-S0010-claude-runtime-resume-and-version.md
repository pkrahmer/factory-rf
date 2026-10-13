---
stage: doing
pr: 10
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The claude agent runtime: the budget resume and the version

## Assignment (as of log entry 1)

Finish the `claude -p` implementation of the agent-runtime interface (R12) that S0009 began. When the call ends because the budget is spent (the reply's `subtype` is `error_max_budget_usd`), the runtime resumes the same session once, with a quarter of the budget (at least 0.50) and the message to finish, so that an agent that ran out of money still gives its decision and its entry; whether the process exit status is 0 does not matter, because the `subtype` decides first. One `time_limit` counts across both calls, the measures of both calls are added up (a call that reported none adds nothing, and unknown stays unknown when neither reported) unless the resumed call is ended by the `time_limit`, when the whole run's cost, tokens and turns are unknown (R24: no partial or estimated figures), and a run that is still over budget after the resume ends as `budget`; a third call is never made. The `agent-run` kill point is reached once, after the last call. The runtime also answers the version query that the preflight uses later (F0010, ST5.3), which completes the `AgentRuntime` protocol: from this story on, `ClaudeCodeRuntime` satisfies it structurally. This story was split from the runtime to keep each story within 26 criteria. Covers R12 and R24 (a timed-out or killed run's cost and tokens are unknown, never invented); keeps kept thing 20 (duration, turns, tokens and cost of every agent run are reported). The resume message differs from v1's: it asks for `question` where v1 asked for `stuck` (decision 13 of the feature). Tests use the stand-in executable of S0009, never the real `claude`; whether the pinned `claude` exits non-zero on a budget stop is a morning observation, and the criterion for exit status 1 makes the code right in either case.

## Interface

`src/factory/adapters/claude_runtime.py` (adds to the module from S0009)

```python
FINISH_MESSAGE = "Finish now: give your decision (question if the work is not done) and your entry."
MINIMUM_RESUME_BUDGET = Decimal("0.50")
VERSION_TIME_LIMIT = timedelta(seconds=30)

def resume_budget(budget: Decimal) -> Decimal: ...

class ClaudeCodeRuntime:      # satisfies AgentRuntime structurally, no inheritance
    def __init__(
        self,
        executable: str,
        state_directory: Path,
        kill_points: KillPoints | None = None,
        *,
        version_time_limit: timedelta = VERSION_TIME_LIMIT,
    ) -> None: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    def version(self) -> str: ...
```

The rules, each with a criterion below:

- Resume. When the first call's output is a JSON object whose `subtype` is `error_max_budget_usd`, whatever the exit status, the same session is resumed once: the same arguments, except `-p` is `FINISH_MESSAGE`, `--session-id <session>` becomes `--resume <session>`, and `--max-budget-usd` is `format(resume_budget(agent.budget_usd), "f")`. The files under `state_directory` are the same ones as for the first call; they are removed when the run ends. The resumed call's reply is read by the rules of S0009. When it also ends with `error_max_budget_usd`, the end reason is `budget`; a third call is never made.
- `resume_budget(budget)` is a quarter of the budget, at least `MINIMUM_RESUME_BUDGET`, rounded half up to cents.
- The measures of both calls are added up: `turns`, `cost_usd` and each of the four token counts; a call that reported none adds nothing; a measure is unknown (`None`) when neither call reported it. When the resumed call is ended by the `time_limit`, `turns`, `cost_usd` and `tokens` of the run are `None` (R24; S0009 takes no measures from a call the time limit ended, and a figure for the first call alone would be a partial one); `duration` is still the factory's own. The permission denials are joined, the first call's first.
- One `time_limit` counts across the whole run: the first call may take `request.time_limit`, the resume what is left of it (the factory's own measure from the start of `run`). A first call that ended by the time limit is never resumed; its end reason is `time_limit`. A call that reaches the limit is killed with its children.
- `duration` is the time the factory measured from the start of `run` to its end, both calls included.
- After the last call has ended and the result is made, `run` reaches `KillPoint.AGENT_RUN` once (when it has kill points), whatever the end reason.
- `version()` runs `<executable> --version` through `run_process` with the limit `version_time_limit` and the current environment of the process, and returns the first whitespace-separated word of the first non-blank line of its output, for example `2.1.289` for `2.1.289 (Claude Code)`. It raises `AgentRuntimeError` when the call cannot be started, exits non-zero, reaches the limit or prints nothing.

Tests: `tests/adapters/test_claude_runtime_resume.py`, which uses `tests/adapters/claude_stand_in.py` from S0009 (extended with new helpers only, no existing helper or test is changed). A test module assigns `ClaudeCodeRuntime` to a variable annotated `AgentRuntime`, so that mypy checks the fit. The only waiting in the tests is for a stand-in that the `time_limit` or the `version_time_limit` kills, a first call that takes 1 second, and a stand-in that waits a fraction of a second.

## Acceptance criteria

1. `resume_budget` gives `1.00` for `Decimal("4")`, `0.75` for `Decimal("3")`, `0.50` for `Decimal("2")`, `0.50` for `Decimal("1")`, `0.50` for `Decimal("0.40")`, `0.51` for `Decimal("2.04")`, `0.51` for `Decimal("2.02")` and `0.53` for `Decimal("2.10")` (a half cent rounds up).
2. When the first reply has `subtype` `error_max_budget_usd`, a second call is made whose arguments are those of the first except `-p` is `FINISH_MESSAGE`, `--resume` and the same session id replace `--session-id`, and `--max-budget-usd` is the resume budget.
3. The second call finds the same three files, with the same content, in `state_directory`, and none is left after `run` returns.
4. When the resumed call completes, `end_reason` is `completed` and `turns`, `cost_usd` and the four token counts are the sums of both calls' values, and the permission denials of both are joined, first call's first.
5. When the resumed call also ends with `error_max_budget_usd`, `end_reason` is `budget` and exactly two calls were made; the same when the resumed call exits with status 1 (the `subtype` decides before the exit status for the resumed call too).
6. A first reply with `subtype` `error_max_budget_usd` and an exit status of 1 is resumed in the same way, and the run completes when the resumed call does.
7. A first call ended by the `time_limit` (a stand-in that waits 60 seconds, a limit of 1 second) is not resumed: `end_reason` is `time_limit` and exactly one call was made.
8. With `time_limit=timedelta(seconds=2)`, a first call that takes 1 second and ends with `error_max_budget_usd`, and a resumed call that would wait 60 seconds, `run` returns within 5 seconds with `end_reason` `time_limit`; the resumed call's limit was what was left of the 2 seconds; the first call reported `num_turns` 5 and `total_cost_usd` 3.0, and `turns`, `cost_usd` and `tokens` of the result are `None` all the same, while `duration` is at least 1 second.
9. A first reply without measures and a resumed reply with them give the resumed call's values; when neither reply has `num_turns`, `total_cost_usd` or `usage`, `turns`, `cost_usd` and `tokens` are `None`.
10. `duration` covers both calls: with a stand-in that waits 0.3 seconds in each call, it is at least 0.6 seconds.
11. With `KillPoint.AGENT_RUN` armed, a run with two calls raises `InjectedKill` only after the second call, with its writes on disk; without arming, `reached(AGENT_RUN)` is 1 after such a run.
12. `version()` returns `2.1.289` for a stand-in that prints `2.1.289 (Claude Code)`, also when blank lines come first.
13. `version()` raises `AgentRuntimeError` for a missing executable, for exit status 1, and for a stand-in that prints nothing.
14. `VERSION_TIME_LIMIT` is `timedelta(seconds=30)`; with `version_time_limit=timedelta(seconds=1)` and a stand-in that waits 60 seconds, `version()` raises `AgentRuntimeError` within 6 seconds.
15. The stand-in that `version()` starts sees a variable that was set in the test process.
16. `ClaudeCodeRuntime` is not a subclass of `AgentRuntime`, and a test module assigns a `ClaudeCodeRuntime` to a variable annotated `AgentRuntime`, so that `make check` (mypy) proves the structural fit.
17. make check stays green.
18. docs: `docs/project-guide.md` describes the budget resume, the shared `time_limit`, the added-up measures and the version query of the `claude -p` runtime; `docs/operator-guide.md` says which `claude` version is expected (the preflight checks it from F0010) and what a budget stop or a `time_limit` costs (WE6.3).

## Demo

```bash
uv run python -c "
import sys, tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
root = Path(tempfile.mkdtemp())
body = '''import json, sys
if sys.argv[1:] == ['--version']:
    print('2.1.289 (Claude Code)')
elif '--resume' in sys.argv:
    print(json.dumps({'subtype': 'success', 'is_error': False, 'num_turns': 3, 'total_cost_usd': 0.25, 'usage': {'input_tokens': 10, 'output_tokens': 5}, 'structured_output': {'decision': 'doing', 'entry': 'Done.'}}))
else:
    print(json.dumps({'subtype': 'error_max_budget_usd', 'is_error': True, 'num_turns': 5, 'total_cost_usd': 3.0}))
'''
script = root / 'claude'
script.write_text('#!' + sys.executable + chr(10) + body)
script.chmod(0o755)
agent = AgentDefinition(name='coder', model='sonnet', tools=['Read'], budget_usd=Decimal('3'), instructions='Code.')
request = AgentRunRequest(agent=agent, prompt='Stage: doing', allowed_decisions=['review', 'doing', 'question'], time_limit=timedelta(minutes=5), working_directory=root, environment={})
runtime = ClaudeCodeRuntime(str(script), root / 'state')
print(runtime.version())
result = runtime.run(request)
print(result.end_reason, result.decision, result.turns, result.cost_usd, result.tokens.input, result.tokens.output)
"
```
Expect: two lines: `2.1.289`, then `completed doing 8 3.25 10 5`: the first call stopped on its budget, the session was resumed once, and the measures of both calls were added up (the first reported no tokens, so they are the resumed call's).

```bash
uv run python -c "
from decimal import Decimal
from factory.adapters.claude_runtime import resume_budget
print([str(resume_budget(Decimal(value))) for value in ('4', '3', '2', '1', '2.04', '2.02')])
"
```
Expect: one line, `['1.00', '0.75', '0.50', '0.50', '0.51', '0.51']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete module `src/factory/adapters/claude_runtime.py`, constants, `resume_budget`, the `ClaudeCodeRuntime` constructor, `run` and `version`, with the rules listed one by one.
   - Criteria: 18 criteria, each testable by one test function. Each rule has its failing side. Budget: the resumed call also over budget gives `budget` and no third call (5), with exit status 1 on the resumed call too. Time limit: a first call ended by `time_limit` is not resumed (7), and a resumed call ended by `time_limit` gives unknown measures (8). Version: a missing executable, exit 1, empty output (13) and the limit (14). Unknown measures are covered by 9. The kill point is covered by 11, rounding by 1, and the shared environment by 15. Gap noted, not a blocker: killing the call's children is stated in the rules but not tested here; S0004 covers process-group kill.
   - Demo: both commands are runnable with the stand-in script. The Expect lines are checkable: `2.1.289`, then `completed doing 8 3.25 10 5`, then the list of budgets.
   - Architecture: the module sits in `factory.adapters`, reached through the `AgentRuntime` protocol and `run_process`. Fit is by structural typing, so no layer is crossed.
   - Scope: within the feature's scope ("claude -p implementation with the budget resume, the time_limit and the version query"). Nothing falls under "Out of scope". The stand-in is used and the real `claude` is not.
3. tester: Wrote the red tests for the budget resume, the shared time_limit, the added-up measures and the version query of the `claude -p` runtime. All of them are in one new file, `tests/adapters/test_claude_runtime_resume.py`. It uses the S0009 stand-in from `tests/adapters/claude_stand_in.py` without changes, since no new helper was needed.

   Criterion → test (all in tests/adapters/test_claude_runtime_resume.py):
   - criterion 1: test_resume_budget_is_a_quarter_at_least_fifty_cents_rounded_half_up (parametrized over all 8 values; checks the Decimal value and its string, e.g. `1.00`)
   - criterion 2: test_budget_stop_resumes_the_same_session_with_the_finish_message
   - criterion 3: test_resumed_call_sees_the_same_run_files_and_none_is_left
   - criterion 4: test_completed_resume_adds_up_the_measures_and_joins_the_denials
   - criterion 5: test_resume_still_over_budget_ends_as_budget_without_a_third_call (parametrized: the resumed call exits 0 or 1; a third step is scripted to show it is never played)
   - criterion 6: test_budget_stop_with_exit_status_1_is_resumed
   - criterion 7: test_first_call_ended_by_the_time_limit_is_not_resumed
   - criterion 8: test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures
   - criterion 9: test_measures_a_call_did_not_report_add_nothing (parametrized: only the resumed call reported / neither did)
   - criterion 10: test_duration_covers_both_calls
   - criterion 11: test_armed_kill_point_fires_only_after_the_resumed_call, test_unarmed_kill_point_is_reached_once_for_a_resumed_run
   - criterion 12: test_version_is_the_first_word_of_the_first_non_blank_line (parametrized: first line / after blank lines; also checks that the argv is exactly `--version`)
   - criterion 13: test_version_that_cannot_be_read_is_a_runtime_error (parametrized: missing executable, exit status 1, prints nothing)
   - criterion 14: test_version_query_over_its_limit_is_a_runtime_error (also checks that VERSION_TIME_LIMIT is 30 s)
   - criterion 15: test_version_query_sees_the_processes_environment
   - criterion 16: test_claude_runtime_fits_the_agent_runtime_protocol_structurally. It assigns the runtime to a variable annotated `AgentRuntime`, which mypy checks, and it asserts that `AgentRuntime` is not in the MRO. It does not use `issubclass`, because that raises TypeError on a protocol that is not runtime_checkable.
   - criteria 17 and 18 are not tests: `make check` is the gate, and the docs criterion is for the docs stage.

   Note for the coder on criterion 8: the test also asserts that the whole run takes under 2.9 s. That is the observable form of "the resumed call's limit was what was left": a resume given the whole 2 s again would end near 3 s.

   `make test`: collection error in the new module. The test runner could not import `FINISH_MESSAGE` from `factory.adapters.claude_runtime`; `resume_budget`, `VERSION_TIME_LIMIT`, the `version_time_limit` keyword and `version()` are missing too. `make lint` is green. I did not run the type check, as the stage skill says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
