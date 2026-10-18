# The stamp of an acceptance merged before approval

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014-S0007 gave every new journal record `at` and `stage` (decision 25: "set for every new record"). Its criterion 6 says that `book_merge` and `book_refusal`, given `at`, record the `done` entry with it and with `stage` = `done`. The tests check this only on `book_merge`'s plain branch. On the `before_approval` branch the call passes `at` on too, but F0014's feature acceptance found that `at` → `None` there survives every test. An acceptance the human merges before its approval stage could thus lose its stamp unnoticed, and the status map would show its `done` entry with no time. This story pins the stamp on that branch, in the domain and through the merge handler. No behaviour is meant to change.

## Interface

No new names. The rule pinned here is today's:
- `factory.domain.acceptance.book_merge(document, bill, *, before_approval=False, at=None) -> WorkItemDocument`. With `at` given, the `done` entry it appends carries `at` and `stage="done"` on both branches. The entry's text is `done (pull request merged before approval); cost: ...` when `before_approval` is true, and the plain done text when it is false. Without `at`, the entry has neither field on either branch.
- `AcceptanceMerged` (`src/factory/application/acceptance.py`) calls it with `at=boundaries.clock.now()` and with `before_approval` from `is_before_approval`.

## Acceptance criteria

1. These are rows of one parametrized test, `before_approval` true and false. `book_merge(document, bill, before_approval=<row>, at=<a UTC time>)` appends a `done` entry of the factory with `at` equal to that time and `stage == "done"`, and its text starts with the row's prefix.
2. The same two rows without `at` append a `done` entry whose `at`, `stage` and `run` are all `None`.
3. An acceptance merged at a stage before the first approval, through the merge handler, is booked in `done/` on `main` with a last journal record of kind `done`. That record has `at` equal to the boundaries' clock at the merge and `stage == "done"`. Its text starts with `done (pull request merged before approval); cost: `.
4. `make check` stays green.
5. docs: none. The decision log's journal entry already says every new record carries the stamp, and the merge before approval does not change.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.acceptance import AcceptanceState, book_merge
from factory.domain.bills import bill
from factory.domain.work_item import WorkItemDocument
state = AcceptanceState(stage='acceptance', stories=['F0002-S0001'])
document = WorkItemDocument(state=state, body='# A\n\n## Journal\n')
at = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
for before in (True, False):
    done = book_merge(document, bill([]), before_approval=before, at=at).state.journal[-1]
    print(before, done.kind, done.at, done.stage)
"
```
Expect: two lines, `True done 2026-10-18 09:00:00+00:00 done` and `False done 2026-10-18 09:00:00+00:00 done`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_acceptance_before_approval.py tests/domain/test_acceptance_booking.py tests/application/test_acceptance_merged_before_approval.py tests/application/test_acceptance_merged.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
