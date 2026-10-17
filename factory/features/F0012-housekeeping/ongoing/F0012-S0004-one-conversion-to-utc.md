---
stage: tests
pr: 156
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One conversion to UTC for the models' times

## Assignment (as of log entry 1)

Five models of the domain convert an aware time to UTC with a field validator of their own, four lines each, the same body every time (`return value.astimezone(UTC)`): `CostRecord.started_at`, `CommitInfo.committed_at`, `PullRequestComment.created_at`, `RepositoryStop.at` and `Claim.started_at`. F0002 wrote the first copies, and later stories copied them. This story puts the rule into one annotated type, `UtcDatetime`, in a new domain module, and gives the five fields that type in place of their validators. Behaviour does not change: an aware time of any offset is kept as the same instant in UTC, and a time without an offset is refused as before.

## Interface

`src/factory/domain/times.py` (new):

```python
def in_utc(value: datetime) -> datetime:
    """`value`, an aware time, as the same instant in UTC."""

UtcDatetime = Annotated[AwareDatetime, AfterValidator(in_utc)]
```

The fields `CostRecord.started_at` (`factory.domain.cost_records`), `CommitInfo.committed_at` (`factory.domain.git`), `PullRequestComment.created_at` (`factory.domain.hosting`), `RepositoryStop.at` (`factory.domain.stops`) and `Claim.started_at` (`factory.domain.work_item`) are typed `UtcDatetime`, and their validators `_to_utc` and `_in_utc` are removed. No other field changes, and the texts these models are written to do not change: the existing tests of `tests/adapters/test_cost_records_jsonl.py` and `tests/adapters/test_work_item_markdown.py` pin them and still pass.

Tests: `tests/domain/test_times.py`. Each model is built from valid values (as its own test module builds it) with the time field set; no existing test changes.

## Acceptance criteria

1. `in_utc(datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2))))` is `datetime(2026, 10, 12, 12, 0, tzinfo=UTC)`, and its `tzinfo` is `UTC`.
2. For each of the five fields, a model built with the aware time `datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2)))` holds `datetime(2026, 10, 12, 12, 0, tzinfo=UTC)` in that field, with `tzinfo` `UTC`; and a model built with the naive `datetime(2026, 10, 12, 12, 0)` is refused with `pydantic.ValidationError`. Ten rows of one parametrized test (five fields, two sides); each model is built from valid values of its own types, so the test passes `mypy --strict`.
3. No module among `factory.domain.cost_records`, `factory.domain.git`, `factory.domain.hosting`, `factory.domain.stops` and `factory.domain.work_item` calls `astimezone` (an `ast.Attribute` named `astimezone` in the module, read with `modules()` of `tests/source_search.py`), and `factory.domain.times` does.
4. `make check` stays green.
5. docs: the project guide's paragraph on the state's `Claim` (section *The data of a work item*, *The claim*), which says that `started_at` is stored in UTC, names `UtcDatetime` in `factory.domain.times` as the one way a model converts a time, to be used by every new time field; the other places that say a time is stored in UTC stay as they are. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import datetime, timedelta, timezone
from factory.domain.stops import RepositoryStop
stop = RepositoryStop(scope='repository', reason='fetch_failed', detail='x', at=datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2))))
print(stop.at.isoformat())
"
grep -rn --include='*.py' 'astimezone(UTC)' src/factory/domain/cost_records.py src/factory/domain/git.py src/factory/domain/hosting.py src/factory/domain/stops.py src/factory/domain/work_item.py; echo "status $?"
```
Expect: the first command prints `2026-10-12T12:00:00+00:00`; the second prints only `status 1`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: `factory.domain.times` with `in_utc` and `UtcDatetime = Annotated[AwareDatetime, AfterValidator(in_utc)]` is concrete. I checked the source: the five named fields exist with `AwareDatetime` and a validator `_to_utc` (cost_records, hosting, stops, work_item) or `_in_utc` (git), each ending in `value.astimezone(UTC)`. No Interface comment states a behaviour that lacks a criterion.
   - Criteria: each is testable by one function. 1 covers `in_utc` directly. 2 is a 10-row parametrized test with the aware side and the naive side (`ValidationError`), so the failing side is covered. 3 is an AST check through `modules()` in `tests/source_search.py`, which exists. 4 is `make check` and 5 is docs.
   - Demo: both commands are runnable. Each `Expect:` line is checkable: `2026-10-12T12:00:00+00:00`, and `status 1` only.
   - Architecture: a new pure domain module that imports only Pydantic and the standard library, so the layers are respected. The existing `astimezone` in `domain/board.py` is outside the five modules of criterion 3 and is not touched.
   - Scope: this is F0012 item 1.2 (decision 18). It is within scope and not in "Out of scope". The docs criterion points at the existing section *The claim* in `docs/project-guide.md`, line 413, whose `started_at` sentence is the one to change.
