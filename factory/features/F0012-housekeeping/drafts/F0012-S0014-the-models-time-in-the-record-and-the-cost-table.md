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
