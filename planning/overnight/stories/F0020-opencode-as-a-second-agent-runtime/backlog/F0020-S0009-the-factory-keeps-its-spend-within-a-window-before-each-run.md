# The factory keeps its spend within a window before each run

## Description

S0007 waits out a provider's spend limit after a run has met it. Behind a gateway that limits the spend per rolling window (about $3 per 10 minutes at the human's work), most of those limits can be avoided: before a run starts or resumes, the factory can look at what it spent in the window just past and wait until the next run fits. This story adds that throttle as an operator setting, `FACTORY_SPEND_WINDOW` (`<dollars>/<minutes>`, such as `3/10`), unset by default, so that nothing changes without it. `PatientRuns` (S0007) records the cost of every call of a stage's run, with its time, in a log of its own in the state directory, and before every call (the first and every resume) waits, on the same `Waiter`, until the spend of the window just past is below the window's dollars. It cannot prevent a limit inside a long run, so it adds to S0007's wait and replaces nothing; a throttle wait counts toward neither the ceiling nor the stage's `time_limit`. Built only when the human confirms the feature's decision 15.

## Interface

`factory.domain.spend` (`domain`, new):

```python
class SpendWindow(BaseModel):
    usd: Annotated[Decimal, Field(gt=0)]
    minutes: PositiveInt

class SpendRecord(BaseModel):
    at: UtcDatetime
    cost_usd: Cost          # the cost records' type: a Decimal of at least 0

def wait_to_fit(records: Sequence[SpendRecord], window: SpendWindow, now: datetime) -> timedelta: ...
```

- `wait_to_fit`: the records in the window are those with `now - minutes < at <= now`. When their sum is below `usd`, the wait is zero. Otherwise, taking them oldest first, the wait is the time until the first one whose leaving the window brings the sum below `usd` leaves it: `at + minutes - now`. Records outside the window, and the order the records come in, change nothing.

`factory.domain.settings` (`domain`):

```python
SPEND_WINDOW_VARIABLE = "FACTORY_SPEND_WINDOW"

class InstanceSettings(BaseModel):
    ...
    spend_window: SpendWindow | None = None   # new, last
```

- `read_settings`: unset or blank gives `None`; `<dollars>/<minutes>`, the dollars a positive decimal number with at most two decimals and the minutes a whole number of at least 1, both ASCII, gives the window (`3/10`, `2.50/10`); any other raises `SettingsInvalid` naming the variable with `is not <dollars>/<minutes>, such as 3/10`.

`factory.application.boundaries` (`application`):

- `Boundaries` gains `spend_records: RecordLog[SpendRecord] | None = None`, last.

`factory.application.provider_limits` (`application`):

- With a spend window in the settings, the spend records and a waiter, `PatientRuns.run` waits `wait_to_fit(<the records>, <the window>, clock.now())` before every call of the runtime (the first and each resume), when it is above zero, and writes `spend window: <agent> waits <s> s for the spend of the last <m> min (<sum> USD) to fall below <usd> USD` to the factory log before it; `<sum>` is the window's sum at that moment.
- After every call whose result has a cost, it appends `SpendRecord(at=clock.now(), cost_usd=<the call's cost>)`; a call without a cost appends nothing.
- Without any of the three, it neither waits nor records, as in S0007.
- A throttle wait counts toward neither the provider limit's ceiling nor the time left (S0007).

`factory.entry.wiring` (`entry`):

- `build_boundaries` gives the boundaries `JsonLinesRecordLog(<state>/spend-records.jsonl, SpendRecord)`.

Tests (the tester writes them): `tests/domain/test_spend.py`, `tests/domain/test_settings_spend_window.py`, `tests/application/test_patient_runs_spend.py` (with `FakeAgentRuntime`, `ManualClock`, `ManualWaiter` and a `JsonLinesRecordLog` in `tmp_path`; the boundaries and helpers of S0007's `tests/application/test_patient_runs.py` imported, not copied), `tests/entry/test_wiring_spend_records.py`. No earlier test changes.

## Acceptance criteria

1. `wait_to_fit` under a window of 3 USD per 10 minutes at 12:10 (rows of one parametrized test): no records give zero; records of 1.00 at 12:02 and 1.50 at 12:05 (2.50) give zero; records of 1.00 at 12:02, 1.50 at 12:05 and 0.50 at 12:09 (3.00) give 2 minutes (12:02 leaves at 12:12); records of 0.20 at 12:02, 2.90 at 12:05 and 0.10 at 12:09 (3.20) give 5 minutes (the first leaving leaves 3.00, only the second brings it below); a record of 5.00 at 12:00, exactly ten minutes before, is outside the window and gives zero; the same records in another order give the same wait.
2. `SpendWindow` refuses `usd` 0 and `minutes` 0 and accepts 0.01 and 1 (rows).
3. `read_settings` gives `None` without `FACTORY_SPEND_WINDOW` or with a blank one, 3 USD per 10 minutes for `3/10` and 2.50 per 10 for `2.50/10`; it raises `SettingsInvalid` naming the variable for `3`, `3/0`, `0/10`, `-1/10`, `3/10.5`, `2.505/10`, `abc/10` and `3 / 10 / 5` (rows).
4. With a window of 3 per 10 minutes and spend records summing 3.00 whose oldest leaves in 120 seconds, a stage's run waits 120 seconds before its first call and writes the log line `spend window: coder waits 120 s for the spend of the last 10 min (3.00 USD) to fall below 3 USD`; with records summing 2.00 it calls at once.
5. A run of two calls, a `provider_limit` of cost 0.20 and a completed one of 0.30, appends two spend records with those costs and the clock's times after each call; a call without a cost appends none.
6. Before the resume after a limit, the throttle waits as before the first call, and its wait is not counted toward the ceiling: under a ceiling of 10 minutes, a limit's cool-down of 10 minutes and a throttle wait of 5 minutes, the resume is still made (rows of the waits recorded).
7. Without a window, without spend records or without a waiter, no spend record is written and no throttle wait is made (rows).
8. `build_boundaries` gives spend records at `<state>/spend-records.jsonl`, which a patient run with a window writes.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`, the section *A provider's spend limit*: `FACTORY_SPEND_WINDOW` (unset by default), what it does before each run and resume, the log line, the file `/state/spend-records.jsonl`, and that it avoids most limits behind a gateway but not one inside a long run; the configuration table gets the variable. `docs/project-guide.md`: `factory.domain.spend` and the spend records in the boundaries. `docs/decisions.md`: an entry *The factory can keep its spend within a window*, dated with the story, with the reasons of the feature's decision 15.

## Smoke test

```bash
uv run -q python - <<'EOF'
from datetime import UTC, datetime
from decimal import Decimal
from factory.domain.settings import read_settings
from factory.domain.spend import SpendRecord, wait_to_fit

window = read_settings({"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "smoke", "FACTORY_SPEND_WINDOW": "3/10"}).spend_window
def at(minute: int) -> datetime:
    return datetime(2026, 10, 18, 12, minute, tzinfo=UTC)
records = [SpendRecord(at=at(2), cost_usd=Decimal("1.00")), SpendRecord(at=at(5), cost_usd=Decimal("1.50")), SpendRecord(at=at(9), cost_usd=Decimal("0.50"))]
print(window.usd, window.minutes)
print(wait_to_fit(records, window, at(10)), wait_to_fit(records[:2], window, at(10)))
EOF
```
Expect: two lines, `3 10` and `0:02:00 0:00:00`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
