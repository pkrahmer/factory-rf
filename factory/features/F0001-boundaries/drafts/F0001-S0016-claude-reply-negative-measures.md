# The claude runtime: a reply with impossible measures is a dead run, and the resumed sums are pinned

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

FEATURE.md decision 12 says a dead, timed-out or over-budget run is a result with an end reason, never an exception. `AgentRuntimeError` is only for a run that cannot be started. The feature acceptance found that `ClaudeCodeRuntime.run` breaks this for one reply. A JSON reply with a valid `subtype` and `is_error` but a negative `num_turns` or token count parses, and then building the `AgentRunResult` fails, so `run` raises a raw `pydantic_core.ValidationError`. The S0009 reviewer noted it, and the acceptance reproduced it.

This story makes such a reply count as a reply that does not parse. The run is `died`, every measure is `None` (R24: nothing invented), and the run files are removed and the kill point reached as for every other `died`. A negative `total_cost_usd` gets the same treatment, because a total that subtracts is no measure either. `AgentRunResult` itself does not bound `cost_usd`, so this rule is the runtime's. The human should confirm the cost part when refining.

It also pins one rule of S0010 that branch coverage shows untested: in a resumed run, a measure that only the first call reported is kept as the first call's.

Not covered here, on purpose, because neither can be tested without sleeps or permission tricks that fail as root:

- the resume skipped when no time is left;
- a run file that cannot be written into an existing state directory.

Covers R12 and R24; restores decision 12.

## Interface

No new public names. `src/factory/adapters/claude_runtime.py`, the reading of one call's reply:

- A reply whose `num_turns`, `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens` or `total_cost_usd` is negative is a reply that does not parse. The call's end reason is `died` unless the `time_limit` ended it, and its turns, tokens and cost are `None`. Zero is a valid value for each.
- For a resumed run, a measure is the sum over both calls, and a call that reported none adds nothing. This is unchanged and is now tested in both directions.

Tests: `tests/adapters/test_claude_runtime.py` and `tests/adapters/test_claude_runtime_resume.py`, with the stand-in of `tests/adapters/claude_stand_in.py`.

## Acceptance criteria

1. A reply with `num_turns` -1 gives a result with `end_reason` `died` and `turns`, `tokens` and `cost_usd` `None`; `run` raises nothing.
2. A reply whose `usage.input_tokens` is -1 gives `died` with every measure `None`; so does one whose `usage.cache_read_input_tokens` is -1.
3. A reply with `total_cost_usd` -0.01 gives `died` with every measure `None`.
4. A completed reply with `num_turns` 0, all four token counts 0 and `total_cost_usd` 0 gives `completed` with turns 0, tokens of 0 and cost 0.
5. After a reply with negative measures, no run file is left under the state directory, and `KillPoint.AGENT_RUN` was reached once.
6. A run whose first call stops on its budget reporting `num_turns` 5, `total_cost_usd` 3.0 and tokens 10 and 5, and whose resumed call completes reporting no measures, has turns 5, cost 3.0 and tokens 10 and 5.
7. make check stays green.
8. docs: the `claude -p` runtime section of `docs/project-guide.md` says that a reply with a negative measure counts as `died` with unknown measures, beside the existing sentence on a reply with a wrong-typed field.

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
c = root / 'claude'
c.write_text(f'#!{sys.executable}\nprint(\'{{\"subtype\": \"success\", \"is_error\": false, \"num_turns\": -1}}\')\n')
c.chmod(0o755)
a = AgentDefinition(name='coder', model='m', tools=[], budget_usd=Decimal(1), instructions='i')
r = AgentRunRequest(agent=a, prompt='p', allowed_decisions=['question'], time_limit=timedelta(seconds=10), working_directory=root)
res = ClaudeCodeRuntime(str(c), root / 'state').run(r)
print(res.end_reason, res.turns, res.tokens, res.cost_usd, list((root / 'state').iterdir()))
"
```
Expect: one line, `died None None None []`, and no traceback.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
