---
stage: ready
pr: 18
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# The claude runtime: a reply with impossible measures is a dead run, and the resumed sums are pinned

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

FEATURE.md decision 12 says a dead, timed-out or over-budget run is a result with an end reason, never an exception. `AgentRuntimeError` is only for a run that cannot be started. The feature acceptance found that `ClaudeCodeRuntime.run` breaks this for one reply. A JSON reply with a valid `subtype` and `is_error` but a negative `num_turns` or token count parses, and then building the `AgentRunResult` fails, so `run` raises a raw `pydantic_core.ValidationError`. The S0009 reviewer noted it, and the acceptance reproduced it.

This story makes such a reply count as a reply that does not parse. The run is `died`, every measure is `None` (R24: nothing invented), and the run files are removed and the kill point reached as for every other `died`. A negative `total_cost_usd` gets the same treatment, because a total that subtracts is no measure either. `AgentRunResult` itself does not bound `cost_usd`, so this rule is the runtime's.

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
2. A reply in which one of `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens` or `usage.cache_creation_input_tokens` is -1, the others valid, gives `died` with every measure `None` (one parametrized test).
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
2. intake: Format check passed. The story is not ready: two behaviours the story or FEATURE.md state have no criterion.

   1. FEATURE.md decision 21 says "a budget-stop reply with a negative measure is `died` and not resumed". The Interface says nothing about this, and no criterion tests it. The criteria only cover replies that do not hit the budget. Without a criterion, a coder can parse the negative reply as `died` and still start the resume, and every listed test passes. Options: (a) add a criterion: a first call that stops on its budget with a negative measure, e.g. `num_turns` -1, gives `died` with every measure `None`, and the stand-in is called once (no resume). (b) Drop the sentence from the decision. I would choose (a), and add one line to the Interface saying the same.

   2. The Interface says the end reason is `died` "unless the `time_limit` ended it". The side where the `time_limit` ended the call and the reply also has a negative measure has no criterion. Options: (a) add a criterion stating the expected end reason (`timed_out`, as I read it) and measures `None`. (b) Remove "unless the `time_limit` ended it" from the Interface, since a call ended by the `time_limit` has no parsed reply. I would choose (b), because decision 13 already says a `time_limit` call has no measures taken from its JSON.

   3. The Interface says the resumed sum is "tested in both directions", but criterion 6 covers only the first call reporting the measures. The reverse, where the first call reports none and the resumed call reports some, has no criterion. Either add that criterion, or reword the Interface to say that only the first-call-only direction is pinned here. I would add the criterion.

   Everything else I checked is fine: the Interface names the module and the rules, the Demo is runnable and its Expect line is checkable, the architecture matches (the change stays inside `factory.adapters`), and the scope matches FEATURE.md.
3. human (pull request comment, 2026-10-13): 1. (a): add the Interface line "A budget-stop reply (`subtype` `error_max_budget_usd`) with a negative measure is such a reply too: the run is `died`, every measure `None`, and it is not resumed." and the criterion, before the two closing ones: "A first call that stops on its budget (`subtype` `error_max_budget_usd`) reporting `num_turns` -1 gives `died` with every measure `None`, and the stand-in was called once (no resume)." This is FEATURE.md decision 21.
   2. (b): remove "unless the `time_limit` ended it" from the Interface. A call the `time_limit` ended has no measures taken from its output (decision 13), so this rule reads only a call that ended on its own; nothing about time-outs changes.
   3. Add the criterion, before the two closing ones: "A run whose first call stops on its budget reporting no measures, and whose resumed call completes reporting `num_turns` 2, `total_cost_usd` 0.5 and tokens 4 and 1, has turns 2, cost 0.5 and tokens 4 and 1." Keep "tested in both directions" in the Interface.
