# The claude agent runtime: the budget resume and the version

## Assignment (as of log entry 1)

Finish the `claude -p` implementation of the agent-runtime interface (R12) that S0009 began. When the call ends because the budget is spent (the reply's `subtype` is `error_max_budget_usd`), the runtime resumes the same session once, with a quarter of the budget (at least 0.50) and the message to finish, so that an agent that ran out of money still gives its decision and its entry; whether the process exit status is 0 does not matter, because the `subtype` decides first. One `time_limit` counts across both calls, the measures of both calls are added up (a call that reported none adds nothing, and unknown stays unknown when neither reported), and a run that is still over budget after the resume ends as `budget`; a third call is never made. The `agent-run` kill point is reached once, after the last call. The runtime also answers the version query that the preflight uses later (F0010, ST5.3), which completes the `AgentRuntime` protocol: from this story on, `ClaudeCodeRuntime` satisfies it structurally. This story was split from the runtime to keep each story within 26 criteria. Covers R12 and R24 (a timed-out or killed run's cost and tokens are unknown, never invented); keeps kept thing 20 (duration, turns, tokens and cost of every agent run are reported). The resume message differs from v1's: it asks for `question` where v1 asked for `stuck` (decision 13 of the feature). Tests use the stand-in executable of S0009, never the real `claude`; whether the pinned `claude` exits non-zero on a budget stop is a morning observation, and the criterion for exit status 1 makes the code right in either case.

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
- The measures of both calls are added up: `turns`, `cost_usd` and each of the four token counts; a call that reported none adds nothing; a measure is unknown (`None`) when neither call reported it. The permission denials are joined, the first call's first.
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
5. When the resumed call also ends with `error_max_budget_usd`, `end_reason` is `budget` and exactly two calls were made.
6. A first reply with `subtype` `error_max_budget_usd` and an exit status of 1 is resumed in the same way, and the run completes when the resumed call does.
7. A first call ended by the `time_limit` (a stand-in that waits 60 seconds, a limit of 1 second) is not resumed: `end_reason` is `time_limit` and exactly one call was made.
8. With `time_limit=timedelta(seconds=2)`, a first call that takes 1 second and ends with `error_max_budget_usd`, and a resumed call that would wait 60 seconds, `run` returns within 5 seconds with `end_reason` `time_limit`; the resumed call's limit was what was left of the 2 seconds.
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
