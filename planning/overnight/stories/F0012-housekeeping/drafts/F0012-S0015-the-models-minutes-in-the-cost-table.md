# The model's minutes in the cost table

## Assignment (as of log entry 1)

With each run's model time in its cost record (F0012-S0014), the human's word "the board and the cost table show the split per stage" becomes a column of the cost table: `model min`, the minutes of model time of the stage's runs, beside `min`, their whole duration. The difference is the time of the tools and the factory. A run whose model time is unknown adds nothing to the column, as an unknown turn count adds nothing to `turns`. The board shows no cost today and stays as it is (FEATURE decision 22). The cost line under the table does not change. The cost table's pinned text in the bills' test changes by the human's leave (FEATURE decision 38).

## Interface

`src/factory/domain/bills.py`:

- `Bill` gains `model_duration: timedelta = timedelta(0)`, the last field: the sum of the known `model_seconds` of its records. A record whose `model_seconds` is `None` adds nothing.
- `cost_table`: the header is `| stage | runs | min | model min | turns | in | cached | out | USD |`, the alignment row `| :-- | --: | --: | --: | --: | --: | --: | --: | --: |`, and each row and the total row carry, after `min`, the model minutes with one decimal, rounded half up like `min`.
- `cost_line` does not change.

Tests: `tests/domain/test_bills_model_time.py`. By the human's leave (FEATURE decision 38), and no other change to an earlier story's test: the expected table of `test_the_cost_table_of_the_demo_stage_bills` in `tests/domain/test_bills.py` gains the column, `0.0` in each of its rows (its records have no model time).

## Acceptance criteria

1. The bill of records with `model_seconds` 30.0, `None` and 45.0 has `model_duration == timedelta(seconds=75)`; of records that all have `None`, `timedelta(0)`; of no records, `timedelta(0)`.
2. `bills_by_stage` sums the model time per stage: two `doing` records of 60 and 30 seconds and one `tests` record of 90 give `doing` 90 seconds and `tests` 90 seconds.
3. The cost table of the bills of criterion 2 is exactly the header and alignment rows of the Interface, then `| tests | 1 | <min> | 1.5 | ... |`, `| doing | 2 | <min> | 1.5 | ... |` and `| **total** | 3 | <min> | 3.0 | ... |`, the other cells as the other columns give them.
4. 0.25 minutes (15 seconds) of model time is written `0.3` and 0.24 minutes `0.2` (rounded half up). Rows of one parametrized test.
5. The cost line of a bill with model time is the same text as without it.
6. `make check` stays green.
7. docs: the operator guide's section *The cost table* shows the new table and gets the row `model min` in its table of columns (the minutes the model took, from each run's `model_seconds`; the rest of `min` is the tools' and the factory's; a run without it adds nothing); the project guide's section *Bills* names `model_duration`. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

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
