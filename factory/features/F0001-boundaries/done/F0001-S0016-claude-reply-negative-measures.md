---
stage: done
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

- A reply whose `num_turns`, `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens`, `usage.cache_creation_input_tokens` or `total_cost_usd` is negative is a reply that does not parse. The call's end reason is `died`, and its turns, tokens and cost are `None`. Zero is a valid value for each.
- A budget-stop reply (`subtype` `error_max_budget_usd`) with a negative measure is such a reply too: the run is `died`, every measure `None`, and it is not resumed.
- For a resumed run, a measure is the sum over both calls, and a call that reported none adds nothing. This is unchanged and is now tested in both directions.

Tests: `tests/adapters/test_claude_runtime.py` and `tests/adapters/test_claude_runtime_resume.py`, with the stand-in of `tests/adapters/claude_stand_in.py`.

## Acceptance criteria

1. A reply with `num_turns` -1 gives a result with `end_reason` `died` and `turns`, `tokens` and `cost_usd` `None`; `run` raises nothing.
2. A reply in which one of `usage.input_tokens`, `usage.output_tokens`, `usage.cache_read_input_tokens` or `usage.cache_creation_input_tokens` is -1, the others valid, gives `died` with every measure `None` (one parametrized test).
3. A reply with `total_cost_usd` -0.01 gives `died` with every measure `None`.
4. A completed reply with `num_turns` 0, all four token counts 0 and `total_cost_usd` 0 gives `completed` with turns 0, tokens of 0 and cost 0.
5. After a reply with negative measures, no run file is left under the state directory, and `KillPoint.AGENT_RUN` was reached once.
6. A run whose first call stops on its budget reporting `num_turns` 5, `total_cost_usd` 3.0 and tokens 10 and 5, and whose resumed call completes reporting no measures, has turns 5, cost 3.0 and tokens 10 and 5.
7. A first call that stops on its budget (`subtype` `error_max_budget_usd`) reporting `num_turns` -1 gives `died` with every measure `None`, and the stand-in was called once (no resume).
8. A run whose first call stops on its budget reporting no measures, and whose resumed call completes reporting `num_turns` 2, `total_cost_usd` 0.5 and tokens 4 and 1, has turns 2, cost 0.5 and tokens 4 and 1.
9. make check stays green.
10. docs: the `claude -p` runtime section of `docs/project-guide.md` says that a reply with a negative measure counts as `died` with unknown measures, beside the existing sentence on a reply with a wrong-typed field.

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
4. intake: accepted. I carried in the human's answer (log entry 3) and wrote exactly it into the story: (1) an Interface line for the budget-stop reply with a negative measure (`died`, every measure `None`, not resumed) and a new criterion 7; (2) removed "unless the `time_limit` ended it" from the Interface; (3) a new criterion 8 for the first call reporting no measures and the resumed call reporting some. The closing criteria are now 9 (`make check`) and 10 (`docs:`). The Assignment is unchanged, because its meaning did not change.
   - Interface: names `src/factory/adapters/claude_runtime.py`, no new public names. Each rule is stated for both sides: negative is `died` with `None` measures, zero is valid. The resumed sums are stated, and "tested in both directions" is now backed by criteria 6 and 8.
   - Criteria: each is testable by one test function. The failing sides are covered by criteria 1, 2, 3 and 7, the passing zero side by 4, the cleanup and kill point by 5, and the resumed sums by 6 and 8.
   - Demo: the command is runnable and its Expect line (`died None None None []`, no traceback) can be checked against the output.
   - Architecture: the change stays inside `factory.adapters`, with no new layer or dependency.
   - Scope: within F0001 and not in its "Out of scope". It matches FEATURE.md decisions 12, 13 and 21.
5. tester: I wrote the tests for criteria 1 to 8, adding them to the two existing claude runtime test files. No new files were needed.

   - criterion 1: tests/adapters/test_claude_runtime.py::test_negative_turns_died_with_unknown_measures
   - criterion 2: tests/adapters/test_claude_runtime.py::test_negative_token_count_died_with_unknown_measures (parametrized over the four `usage` fields, each set to -1 while the others stay valid)
   - criterion 3: tests/adapters/test_claude_runtime.py::test_negative_cost_died_with_unknown_measures
   - criterion 4: tests/adapters/test_claude_runtime.py::test_zero_measures_are_valid
   - criterion 5: tests/adapters/test_claude_runtime.py::test_reply_with_negative_measures_removes_run_files_and_reaches_the_kill_point
   - criterion 6: tests/adapters/test_claude_runtime_resume.py::test_measures_only_the_first_call_reported_are_kept
   - criterion 7: tests/adapters/test_claude_runtime_resume.py::test_budget_stop_with_a_negative_measure_died_and_is_not_resumed
   - criterion 8: tests/adapters/test_claude_runtime_resume.py::test_measures_only_the_resumed_call_reported_are_taken

   How I read the criteria: in criteria 6 and 8, "tokens 10 and 5" and "tokens 4 and 1" mean `input_tokens` and `output_tokens`. The cache counts are left out of the reply and are expected to be 0. An existing test, `test_cache_counts_default_to_zero`, already pins that default, so this is not a new rule.

   `make test` result: the new tests for criteria 1, 2, 3, 5 and 7 fail for the right reason. They get the wrong end reason, or a `ValidationError` from the current runtime; no import or collection errors. The tests for criteria 4, 6 and 8 pin behaviour that already exists, so they are expected to pass now (the story says these rules are "unchanged and now tested"). There are no modules the test runner could not import. `make lint` is green.

   Left for the next stages: criterion 9 (`make check`) is for the coder, and criterion 10 (the docs sentence) is for the documenter.

   `make lint`: lint: green
   `make test`: FAILED tests/adapters/test_claude_runtime_resume.py::test_budget_stop_with_a_negative_measure_died_and_is_not_resumed
6. coder: I changed `src/factory/adapters/claude_runtime.py` (commit 16acc2a). The private reply models are now bounded at zero. `_Reply.num_turns` is `NonNegativeInt | None`. `_Reply.total_cost_usd` is `NonNegativeFloat | None`. The four `_Usage` token counts are `NonNegativeInt`. A reply with a negative measure therefore fails validation in `_parse_reply`, which returns `None`. That is the existing path for a reply that does not parse: the run is `died` with every measure `None`, the run files are removed in `finally`, and `KillPoint.AGENT_RUN` is reached. A budget-stop reply with a negative measure fails to parse too, so its end reason is never `budget` and it is not resumed. Zero is still valid. I did not need to change the resumed sums; the tests for criteria 6 and 8 already passed. `make check` is green.

   Main decision: I put the rule in the reply's parse model. I rejected a separate check after parsing. It would duplicate the "does not parse" path, and it would have to run before the budget subtype is read so that it does not trigger a resume. Bounding the fields keeps "a negative measure is a reply that does not parse" literally true. I added one comment above `_Usage` giving the reason.

   Refactor: I read the diff and found nothing to change; it is three type annotations, an import and a comment.

   Not touched: two lines of `claude_runtime.py` remain uncovered (360, 381-382): the resume skipped when no time is left, and the state-directory write error. The story leaves both out on purpose. Criterion 10, the docs sentence, is for the documenter.

   `make check`: check: green
7. reviewer: no findings.

   I read the ticket and `git diff main...HEAD -- . ':!factory'`: `src/factory/adapters/claude_runtime.py` and the two test files.

   - Acceptance criteria: each of criteria 1 to 8 has a test, and each test checks what its criterion says. Criteria 1, 2 and 3 change one measure to -1 (or the cost to -0.01) and keep the other `_reply` values valid. Criterion 2 is one test parametrized over the four `usage` fields. Criterion 4 is the zero side of the same limit; `Decimal("0.0") == Decimal(0)` holds. Criterion 5 asserts that the call ran with its files, that no run file is left and that `KillPoint.AGENT_RUN` was reached once. Criterion 6 tests the first-call-only sum and criterion 8 the resumed-call-only sum. Criterion 7 uses `_budget_reply(num_turns=-1)`, asserts `died` with every measure `None`, and checks that the stand-in was called once. Every rule the Interface states is tested on its rejected side (negative) and its accepted side (zero). The coder's entry says the factory's `make check` was green.
   - Architecture: the change stays inside `factory.adapters`. The bounds sit on the private parse models (`NonNegativeInt` and `NonNegativeFloat` from pydantic, which is already a dependency). It adds no new interface, DTO or wrapper.
   - Security: nothing silences a check, nothing builds a shell command or SQL from strings, and there are no secrets. A reply with a negative measure fails validation at the boundary, `_parse_reply` catches that, and the run ends as `died` without leaking the error.
   - Quality: the rule reuses the existing "reply does not parse" path, so there is no duplicated check. The comment above `_Usage` gives the reason.
   - Ticket hygiene: log entry 6 states the main decision (bounding the parse model) and the alternative rejected (a separate check after parsing). The Assignment matches what was built. Criterion 10 still tells the documenter what to add to `docs/project-guide.md`.
8. documenter: changed `docs/project-guide.md` (measures paragraph of the `claude -p` runtime section): after the sentence on a wrong-typed field, it now says a reply with a negative `num_turns`, token count or `total_cost_usd` counts as `died` with every measure `None`, that zero is valid, and that a budget-stop reply with a negative measure is `died` and not resumed (criterion 10).
   Cross-read and found current against the diff: the resume paragraphs of the same section (sums over both calls, a call that reported none adds nothing; this matches criteria 6 and 8), the `AgentRunResult` paragraph, `README.md`, `docs/operator-guide.md`. The code matches the Interface and no finding for the coder. No examples were written; `make check` is green after the edit. Nothing stale seen that is unrelated to this story.

   `make check`: check: green
9. demo: no findings.

   I ran the one command under `## Demo` from the repository root, exactly as written. It used a stand-in `claude` that replies `{"subtype": "success", "is_error": false, "num_turns": -1}` and called `ClaudeCodeRuntime.run`. Exit status 0.

   ```
   died None None None []
   ```

   Expect: one line, `died None None None []`, and no traceback. Met: the output is exactly that line, with nothing on stderr.

   Checked against the acceptance criteria:
   - Criterion 1: the end reason is `died`, turns, tokens and cost are `None`, and `run` raised nothing.
   - Criterion 5, the part this demo shows: the state directory is empty, so no run file is left.

   The demo contradicts no criterion. Criteria 2 to 4 and 6 to 8 are not exercised by the demo; the tests named in log entry 5 cover them. Criteria 9 and 10 are the factory's `make check` and the documenter's change (log entry 8).
10. done (pull request merged); cost: 7 runs, 3.9 min, 35 turns, 109k tokens in (360k more from cache), 12k out, $0.97
