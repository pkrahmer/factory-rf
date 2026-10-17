---
stage: review
pr: 166
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The model's time in an agent run's record and in the cost table

## Assignment (as of log entry 1)

Coder runs took 20 to 30 minutes in three turns, and nobody could tell how much of it was the model thinking and how much the tools running (`make check` above all). `claude -p --output-format json` already reports both in its reply: `duration_ms`, the whole call, and `duration_api_ms`, the time spent waiting for the model. This story reads `duration_api_ms` into the run's result as the model's time, adds it over a resumed call, and writes it into the run's cost record as `model_seconds`, next to the duration and the cost; the rest of a run's time is the tools' and the factory's (FEATURE decision 22). A reply without the field, a call killed by its time limit and an older record all leave it unknown (`None`, never 0, R24). The pinned lines of the cost record file's test gain the new key, by the human's leave (FEATURE decision 37).

With each run's model time in its cost record, the human's word "the board and the cost table show the split per stage" becomes a column of the cost table: `model min`, the minutes of model time of the stage's runs, beside `min`, their whole duration. The difference is the time of the tools and the factory. A run whose model time is unknown adds nothing to the column, as an unknown turn count adds nothing to `turns`. The board shows no cost today and stays as it is (FEATURE decision 22). The cost line under the table does not change. The cost table's pinned text in the bills' test changes by the human's leave (FEATURE decision 38).

## Interface

`src/factory/domain/agent_runs.py`: `AgentRunResult` gains `model_duration: timedelta | None = None`, after `duration`: the time the model took, `None` when unknown.

`src/factory/adapters/claude_runtime.py`:

- `_Reply` gains `duration_api_ms: NonNegativeInt | None = None`; a negative value makes the reply unparsable, so the call is `died`, as for the other measures.
- A result with measures (the reply parsed, the call not killed) has `model_duration = timedelta(milliseconds=reply.duration_api_ms)`, or `None` when the reply has no such field. A call killed by its time limit has `None`.
- A resumed run (a budget stop, then the resume) has the sum of both calls' model durations when both are known, the known one when only one is, `None` when neither; a resume that the time limit ended keeps the second call's `None`, as for the other measures.

`src/factory/domain/cost_records.py`: `CostRecord` gains `model_seconds: Duration | None = None`, after `duration_seconds`. A started record has none (the rule of `_measures_only_when_completed` names it with the other measures); a completed record may have it or not.

`src/factory/application/costs.py`: the completed record copies `result.model_duration` in seconds, or `None`.

`src/factory/adapters/cost_records_jsonl.py` writes the key in field order like every other key; a line without the key (an older file) still reads, with `model_seconds` `None`.

Tests: new test functions in `tests/adapters/test_claude_runtime_resume.py` (criteria 1 to 3), with that module's `_reply`, `_budget_reply`, `_without`, `_request` and `_runtime` and the `claude` stand-in of `tests/adapters/claude_stand_in.py`, so that no reply builder is copied; `tests/domain/test_cost_record_model_seconds.py` (criterion 4); `tests/application/test_costs_model_seconds.py` (criterion 5). By the human's leave (FEATURE decision 37), and no other change to an earlier story's test: in `tests/adapters/test_cost_records_jsonl.py`, `COMPLETED_LINE` gains `"model_seconds":41.5` and `STARTED_LINE` `"model_seconds":null`, each right after `duration_seconds`, and the record `_completed()` builds gains `model_seconds=41.5`.

`src/factory/domain/bills.py`:

- `Bill` gains `model_duration: timedelta = timedelta(0)`, the last field: the sum of the known `model_seconds` of its records. A record whose `model_seconds` is `None` adds nothing.
- `cost_table`: the header is `| stage | runs | min | model min | turns | in | cached | out | USD |`, the alignment row `| :-- | --: | --: | --: | --: | --: | --: | --: | --: |`, and each row and the total row carry, after `min`, the model minutes with one decimal, rounded half up like `min`.
- `cost_line` does not change.

Tests: `tests/domain/test_bills_model_time.py`. By the human's leave (FEATURE decision 38), and no other change to an earlier story's test: the expected table of `test_the_cost_table_of_the_demo_stage_bills` in `tests/domain/test_bills.py` gains the column, `0.0` in each of its rows (its records have no model time).

## Acceptance criteria

1. A reply with `"duration_api_ms": 41500` gives a completed result with `model_duration == timedelta(seconds=41.5)`; a reply without the field gives `None`; a reply with `-1` gives the end reason `died`. Rows of one parametrized test.
2. A call killed by its time limit gives `model_duration is None`, whatever its partial output held.
3. A budget stop with `duration_api_ms` 30000 resumed by a call with 5000 gives `timedelta(seconds=35)`; with the first unknown and the second 5000, `timedelta(seconds=5)`; with the first 30000 and the second unknown, `timedelta(seconds=30)`; with both unknown, `None`; a resume ended by the time limit gives `None`. Rows of one parametrized test.
4. A `CostRecord` with `status="started"` and `model_seconds=1.0` is refused with `pydantic.ValidationError`; a completed one with `model_seconds=None`, `0` or `41.5` is accepted; `-1` and `float("nan")` are refused. Rows of one parametrized test.
5. The cost record that `CostRecorder.complete` writes for a result with `model_duration=timedelta(seconds=41.5)` has `model_seconds == 41.5`, and for a result without it, `None`.
6. The writer renders `model_seconds` after `duration_seconds`; the reader reads a line without the key with `model_seconds is None` (the pinned lines and a line written before this story).
7. The bill of records with `model_seconds` 30.0, `None` and 45.0 has `model_duration == timedelta(seconds=75)`; of records that all have `None`, `timedelta(0)`; of no records, `timedelta(0)`.
8. `bills_by_stage` sums the model time per stage: a `tests` record with `model_seconds` 90 followed by two `doing` records with 60 and 30 give the `tests` bill 90 seconds and the `doing` bill 90 seconds, in that order.
9. The cost table of those three records, with `duration_seconds` 120 for the `tests` record and 60 and 30 for the `doing` records and no turns, tokens or cost, is exactly the header and alignment rows of the Interface, then `| tests | 1 | 2.0 | 1.5 | 0 | 0 | 0 | 0 | 0.00 + 1 unknown |`, `| doing | 2 | 1.5 | 1.5 | 0 | 0 | 0 | 0 | 0.00 + 2 unknown |` and `| **total** | 3 | 3.5 | 3.0 | 0 | 0 | 0 | 0 | 0.00 + 3 unknown |`.
10. 0.25 minutes (15 seconds) of model time is written `0.3` and 0.24 minutes `0.2` (rounded half up). Rows of one parametrized test.
11. The cost line of a bill with model time is the same text as without it.
12. `make check` stays green.
13. docs: the project guide's section *The agent runtime*, in its paragraph on the measures, says that `model_duration` is the reply's `duration_api_ms` (unknown when the reply lacks it or the time limit killed the call, summed over a resume) and that `duration` stays what the factory measured, in place of "the JSON's own durations are ignored"; its section *Cost records* names `model_seconds` (the run's `model_duration` in seconds; `null` in a started record and absent from a line written before it existed), says that the rest of a run's duration is the tools' and the factory's, and its two example lines carry the key; the operator guide's section *What a work item cost: `factory-bill`* says that each record also holds the model's time; the decision log records why the time per tool command inside a run is not recorded (the single JSON reply does not carry it; it needs `claude`'s streamed events); the operator guide's section *The cost table* shows the new table and gets the row `model min` in its table of columns (the minutes the model took, from each run's `model_seconds`; the rest of `min` is the tools' and the factory's; a run without it adds nothing); the project guide's section *Bills* names `model_duration`. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import timedelta
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import CostRecord
result = AgentRunResult(end_reason='completed', decision='doing', entry='Done.', duration=timedelta(seconds=60), model_duration=timedelta(seconds=41.5))
print(result.model_duration.total_seconds(), list(CostRecord.model_fields).index('model_seconds') == list(CostRecord.model_fields).index('duration_seconds') + 1)
"
```
Expect: `41.5 True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_resume.py tests/adapters/test_cost_records_jsonl.py tests/application/test_costs_model_seconds.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.bills import bills_by_stage, cost_table
from factory.domain.cost_records import CostRecord
def record(run, stage, seconds, model):
    return CostRecord(run=run * 32, work_item='F0001-S0001', stage=stage, role='coder', attempt=0, status='completed', started_at=datetime(2026, 10, 17, tzinfo=UTC), duration_seconds=seconds, model_seconds=model, end_reason='completed')
print(cost_table(bills_by_stage([record('a', 'doing', 120.0, 60.0), record('b', 'doing', 60.0, None)])))
"
```
Expect: four lines: the header `| stage | runs | min | model min | turns | in | cached | out | USD |`, the alignment row, `| doing | 2 | 3.0 | 1.0 | 0 | 0 | 0 | 0 | 0.00 + 2 unknown |` and `| **total** | 2 | 3.0 | 1.0 | 0 | 0 | 0 | 0 | 0.00 + 2 unknown |`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules, fields and signatures (`AgentRunResult.model_duration`, `_Reply.duration_api_ms`, `CostRecord.model_seconds`, `Bill.model_duration`, `cost_table` header and alignment row), the field order, and the exact test files and the pinned lines the tester may change. The Interface adds no behaviour that has no criterion.
   - Criteria: each is testable by one test function. Rules have both sides. A missing field gives `None` and `-1` gives `died` (1). A time-limit kill gives `None` (2). Resume sums, the one-known cases, both unknown, and the time-limit resume (3). A started record is refused, and a completed one accepts `None`, 0 and 41.5 while -1 and nan are refused (4). The writer and an older line without the key (6). Known and `None` sums and an empty bill (7). Half-up rounding at 0.25 and 0.24 (10). `cost_line` unchanged (11). I recomputed the numbers of criteria 8 and 9 (minutes, model minutes, totals) and they agree.
   - Demo: the three commands are runnable. Each `Expect:` line is checkable text, and I checked the third's arithmetic (3.0 min, 1.0 model min, 2 unknown).
   - Architecture: the changes sit in the layer each belongs to. The reply is parsed in the adapter, the DTO fields are in the domain, and the copy into the record is in application `costs.py`. No new dependency or package.
   - Scope: this is F0012's item 1.4, "the model's time of every agent run". FEATURE decisions 22, 37 and 38 cover the story, including the leave to change the two earlier tests. Nothing in "Out of scope" is touched.
3. tester: Wrote the red tests for criteria 1 to 11. They are the coder's specification.

   - criterion 1: tests/adapters/test_claude_runtime_resume.py::test_model_duration_is_the_replys_api_time (rows: 41500 gives 41.5 s, no field gives None, -1 gives `died`)
   - criterion 2: tests/adapters/test_claude_runtime_resume.py::test_call_killed_by_the_time_limit_has_no_model_duration (partial output is either nothing or a whole reply with `duration_api_ms`; 2 s limit)
   - criterion 3: tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls (rows: 30000+5000, unknown+5000, 30000+unknown, both unknown, and a resume killed by a 5 s limit)
   - criterion 4: tests/domain/test_cost_record_model_seconds.py::test_model_seconds_only_in_a_completed_record_and_never_negative_or_nan
   - criterion 5: tests/application/test_costs_model_seconds.py::test_completed_record_copies_the_model_duration_in_seconds (rows: 41.5 s and None). It builds a `CostRun` with a started record directly and calls `CostRecorder(boundaries).complete`. It checks both the returned record and the sidecar it wrote.
   - criterion 6, writer: the pinned `COMPLETED_LINE`, `STARTED_LINE` and `_completed()` in tests/adapters/test_cost_records_jsonl.py, changed exactly as FEATURE decision 37 allows; test_render_writes_the_lines_of_the_format pins the key order.
   - criterion 6, reader of an older line: tests/adapters/test_cost_records_jsonl_model_seconds.py::test_lines_without_model_seconds_read_with_it_unknown. I put it in a new file rather than adding a function to the earlier story's module, to stay within "no other change to an earlier story's test".
   - criterion 7: tests/domain/test_bills_model_time.py::test_the_bill_sums_the_known_model_time
   - criterion 8: tests/domain/test_bills_model_time.py::test_bills_by_stage_sums_the_model_time_per_stage
   - criterion 9: tests/domain/test_bills_model_time.py::test_the_cost_table_has_a_model_minutes_column
   - criterion 10: tests/domain/test_bills_model_time.py::test_model_minutes_are_rounded_half_up (15 s gives 0.3; 14.4 s, which is 0.24 min, gives 0.2)
   - criterion 11: tests/domain/test_bills_model_time.py::test_the_cost_line_does_not_show_the_model_time
   - FEATURE decision 38: in tests/domain/test_bills.py::test_the_cost_table_of_the_demo_stage_bills, the expected header and alignment rows gain the `model min` column, and each row gains `0.0` after `min`.

   New files: tests/domain/test_cost_record_model_seconds.py, tests/domain/test_bills_model_time.py, tests/application/test_costs_model_seconds.py, tests/adapters/test_cost_records_jsonl_model_seconds.py. Changed files: tests/adapters/test_claude_runtime_resume.py (new functions only), tests/adapters/test_cost_records_jsonl.py and tests/domain/test_bills.py (the changes the leave allows).

   `make test` is red for the right reasons. Every module imports, because the new fields do not exist yet rather than whole modules being missing. The failures:
   - `CostRecord` and `AgentRunResult` refuse the unknown `model_seconds` / `model_duration` keyword (`extra="forbid"`), so the fixture in test_bills_model_time.py errors.
   - `AgentRunResult` has no `model_duration` attribute.
   - The cost table has no `model min` column.

   `make lint` is green. The type check was skipped as the stage says; it will pass once the fields exist.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/domain/test_bills_model_time.py::test_the_cost_table_has_a_model_minutes_column
4. coder: Each run's model time now goes into its result and its cost record, and the cost table has a new `model min` column. I did not edit any test. `make check` is green and the work is one commit, `ticket F0012-S0014: feat(costs): …`.

   - `src/factory/domain/agent_runs.py`: `AgentRunResult` has a new field `model_duration: timedelta | None = None`, placed after `duration`.
   - `src/factory/adapters/claude_runtime.py`:
     - `_Reply` reads `duration_api_ms: NonNegativeInt | None`. A negative value makes the reply unparsable, so the run ends as `died`.
     - `_result` turns the value into a timedelta. A killed call still returns early with no measures, so its model time stays `None`.
     - `_resumed_result` adds both calls' times with the existing `_add`, which now also accepts `timedelta`. That gives the sum, or the one known value, or `None`. A resume that the time limit ended still keeps the second call's result unchanged, so it is `None`.
   - `src/factory/domain/cost_records.py`: `CostRecord` has a new field `model_seconds: Duration | None`, placed after `duration_seconds`. `_measures_only_when_completed` refuses it in a started record.
   - `src/factory/application/costs.py`: `_completed` copies the run's model time in seconds, or `None`, through a small `_seconds` helper.
   - `src/factory/adapters/cost_records_jsonl.py`: no change. `model_dump` already writes the keys in field order, and the field's default `None` lets an older line without the key still read.
   - `src/factory/domain/bills.py`:
     - `Bill` has a new last field, `model_duration` (default `timedelta(0)`). `_record_bill` and `_add` sum it.
     - A new `_known_duration` treats an unknown value as zero and now serves both `duration` and `model_duration`.
     - `_minutes` now takes a timedelta rather than a `Bill`, so the `min` and `model min` columns share the same half-up rounding.
     - The header and alignment rows gain the column. `cost_line` prints the same text as before.

   Main decision: I reused `_add` by adding `timedelta` to its allowed types instead of writing a separate adder for durations. The rejected alternative would have been a second copy of the same "known one or sum" rule.

   Refactor: I read the diff as a reviewer would and found nothing to change. The two small cleanups (`_minutes` taking a timedelta, `_known_duration` replacing an inline conditional) were already in the feature commit.

   Noticed, not touched: `make duplicates` reports `2 new, 39 known, 0 gone`. Both new findings are vulture dead-code hits for `used_bytes`, in `src/factory/adapters/disk_space.py:19` and `src/factory/application/machine.py:48`. Neither file is part of this ticket, and nothing new comes from this ticket's code. The docs criterion is the documenter's.

   `make check`: check: green
   `make duplicates`: duplicates: 2 new, 39 known, 0 gone
5. reviewer: one finding in group 1 (acceptance criteria). I stopped there, as the checklist says.

   1. `tests/adapters/test_claude_runtime_resume.py::test_model_duration_is_the_replys_api_time`: the Interface types `_Reply.duration_api_ms` as `NonNegativeInt`, so its limit has two sides. The test covers -1 (refused, `died`) but not 0 (accepted). CLAUDE.md *Tests* says a `NonNegativeInt` field gets a test with -1 and one with 0, and the reviewer counts an untested side as a finding. Fix: add a row `(_reply(duration_api_ms=0), "completed", timedelta(0))` to that parametrized test. The tester has to make this change, because the coder does not edit tests (R9). So the coder should end with `tests` and name this row.

   Not reviewed because of the stop rule: groups 2 to 5. One thing for the next round: `_seconds` in `src/factory/application/costs.py:88` repeats `_seconds` in `src/factory/adapters/process.py:43` word for word. The application layer cannot import the adapter's copy, so check this under group 4 (CLAUDE.md: a second copy of an existing helper is a finding).

   Everything else in group 1 holds. Criteria 1 to 11 each have a test named after them that tests what the criterion says. The changes to the pinned tests stay within FEATURE decisions 37 and 38. `CostRecord.model_seconds` is tested on both sides (0 and -1, plus nan). The coder's entry says `make check` was green.
6. coder: The reviewer's only finding (entry 5) is a missing test row, which the coder may not add (R9), so this goes back to the tester. I changed no code this round.

   - Test change for the tester: in `tests/adapters/test_claude_runtime_resume.py::test_model_duration_is_the_replys_api_time`, add the row `(_reply(duration_api_ms=0), "completed", timedelta(0))`. It tests the accepted side of the `NonNegativeInt` limit on `_Reply.duration_api_ms`; the refused side, -1, is already a row.
   - I expect the row to pass against the current code, because `_Reply.duration_api_ms` is `NonNegativeInt | None` and `_result` turns 0 into `timedelta(milliseconds=0)`. If it fails, it comes back to doing.
   - Left as it is: the reviewer's note on `_seconds` in `src/factory/application/costs.py`, which repeats the one in `src/factory/adapters/process.py`. The reviewer marked it for group 4 next round, not as a finding of this round, so I did not change it. If it becomes a finding, the fix stays inside the layer rules: application cannot import adapters. One option is a shared helper in `factory.domain` that both places use. The other is to inline `timedelta.total_seconds()` in `costs.py`.
7. tester: tester (a test change the human approved): I made the one change that coder entry 6 names, which comes from reviewer finding 1 in entry 5.

   - `tests/adapters/test_claude_runtime_resume.py::test_model_duration_is_the_replys_api_time`: added the row `(_reply(duration_api_ms=0), "completed", timedelta(0))` with id `zero`. It sits between `reported` and `not reported`. The row tests the accepted side of the `NonNegativeInt` limit on `_Reply.duration_api_ms`; the refused side, -1, was already a row. I changed nothing else.

   `make test`: test: green (30.6 s). The new row passes against the current code, as the coder expected.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (27.2 s)
8. coder: coder (round 1): This round's only finding is closed, and I removed the duplicate helper the reviewer flagged. `make check` is green.

   - Finding 1 (entry 5), the missing `0` row for `_Reply.duration_api_ms`: the tester added it in entry 7 (`tests/adapters/test_claude_runtime_resume.py::test_model_duration_is_the_replys_api_time`, id `zero`). It passes against the code from commit 13f070d without any code change.
   - The reviewer's note for group 4, `_seconds` in `src/factory/application/costs.py` repeating `_seconds` in `src/factory/adapters/process.py`: fixed in commit 15382be (`refactor(costs)`). I removed the private helper from `costs.py` and moved its one use, a None-or-`total_seconds()` conversion, into `_completed`. I also dropped the `timedelta` import that only the helper needed. Behaviour is unchanged.
   - Alternative I rejected: a shared helper in `factory.domain` that both `costs.py` and `process.py` would use. It would have meant editing `process.py`, which is outside this ticket, and a helper is not worth it for a single use.
   - Noticed, not touched: `make duplicates` still reports the two vulture hits on `used_bytes` (`src/factory/adapters/disk_space.py:19`, `src/factory/application/machine.py:48`) from entry 4. Neither file is part of this ticket. The docs criterion is the documenter's.

   `make check`: check: green

   `make check`: check: green
   `make duplicates`: duplicates: 2 new, 39 known, 0 gone
