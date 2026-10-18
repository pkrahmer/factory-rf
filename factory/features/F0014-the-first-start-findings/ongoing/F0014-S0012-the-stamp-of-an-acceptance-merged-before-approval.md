---
stage: accept
pr: 203
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The stamp of an acceptance merged before approval

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014-S0007 gave every new journal record `at` and `stage` (decision 25: "set for every new record"). Its criterion 6 says that `book_merge` and `book_refusal`, given `at`, record the `done` entry with it and with `stage` = `done`. The tests check this only on `book_merge`'s plain branch. On the `before_approval` branch the call passes `at` on too, but F0014's feature acceptance found that `at` → `None` there survives every test. An acceptance the human merges before its approval stage could thus lose its stamp unnoticed, and the status map would show its `done` entry with no time. This story pins the stamp on that branch, in the domain and through the merge handler. No behaviour is meant to change.

## Interface

No new names. The rule pinned here is today's:
- `factory.domain.acceptance.book_merge(document, bill, *, before_approval=False, at=None) -> WorkItemDocument`. With `at` given, the `done` entry it appends carries `at` and `stage="done"` on both branches. The entry's text is `done (pull request merged before approval); cost: ...` when `before_approval` is true, and the plain done text when it is false. Without `at`, the entry has neither field on either branch.
- `AcceptanceMerged` (`src/factory/application/acceptance.py`) calls it with `at=boundaries.clock.now()` and with `before_approval` from `is_before_approval`.

## Acceptance criteria

1. `book_merge(document, bill, before_approval=True, at=<a UTC time>)` appends a `done` entry of the factory with `at` equal to that time, `stage == "done"` and `run` `None`. The test is a third `booking` row, `merge-before-approval` (`book_merge(_report(), bill([]), before_approval=True, at=at)`), of `tests/domain/test_journal_stamps.py::test_booking_records_the_done_entry_with_the_time_and_the_done_stage`, beside its rows `merge` and `refusal` (FEATURE decision 35). Its `with-at` row checks this criterion. The test's name and body stay.
2. The same call without `at` appends a `done` entry whose `at`, `stage` and `run` are all `None`. This is the `without-at` row of the same `booking` row.
3. An acceptance merged at its stage `acceptance`, before the first approval, through `AcceptanceMerged`, is booked in `done/` on `main` with a last journal record of kind `done`. That record has `at` equal to `boundaries.clock.now()` and `stage == "done"`, and its text starts with `done (pull request merged before approval); cost: `. This is a new test function in `tests/application/test_acceptance_merged_before_approval.py`, using its fixtures `publish` and `merge` and its helper `_booked`.
4. `make check` stays green.
5. docs: none. The project guide already says that every entry the factory appends carries `at` and `stage`, and that the acceptance's `done` entry carries `done`. The merge before approval does not change.

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
uv run pytest --no-header -p no:cacheprovider tests/domain/test_journal_stamps.py tests/domain/test_acceptance_before_approval.py tests/domain/test_acceptance_booking.py tests/application/test_acceptance_merged_before_approval.py tests/application/test_acceptance_merged.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted.
   - Interface: no new names. It pins the existing `book_merge(document, bill, *, before_approval=False, at=None)` in `src/factory/domain/acceptance.py` (signature read and matches) and the `AcceptanceMerged` call in `src/factory/application/acceptance.py`. Its one behaviour comment, the `done` text with `before_approval`, is covered by criterion 3. The stamp (`at`, `stage="done"`) on both branches is covered by criteria 1 and 2. The rule has no limit or rejected input, so no failing side is missing. The `without at` side is criterion 2.
   - Criteria: each is testable by one function or one row. Criteria 1 and 2 are the `merge-before-approval` `booking` row of `test_booking_records_the_done_entry_with_the_time_and_the_done_stage`. The test exists in `tests/domain/test_journal_stamps.py` with `with-at` and `without-at` rows, and the new `booking` function is `book_merge(_report(), bill([]), before_approval=True, at=at)`. FEATURE decision 35 gives the leave for that row. Criterion 3 is a new function in `tests/application/test_acceptance_merged_before_approval.py`. Its fixtures `publish` and `merge` and its helper `_booked` exist there.
   - Demo: both commands are runnable, and each Expect line is checkable (two named output lines; a pytest summary with `<n> passed` and no `failed`, `error` or `skipped`).
   - Architecture: tests only, with a domain test and an application test, in the layer folders the tests mirror. No source change is needed or asked for.
   - Scope: within F0014. FEATURE.md lists S0012 and the leave of decisions 35 and 36 (4). Nothing in "Out of scope" is touched.
3. tester: Tests written for the before-approval branch of `book_merge`. This story pins behaviour that already exists, so the new tests pass now rather than fail. `make test` is green (33.6 s) and `make lint` is green.
   - criterion 1: tests/domain/test_journal_stamps.py::test_booking_records_the_done_entry_with_the_time_and_the_done_stage[with-at-merge-before-approval]. It is a new `booking` row, `merge-before-approval`, through the new helper `_merge_before_approval`, which calls `book_merge(_report(), bill([]), before_approval=True, at=at)`. It sits beside the rows `merge` and `refusal`, and the test's name and body did not change.
   - criterion 2: tests/domain/test_journal_stamps.py::test_booking_records_the_done_entry_with_the_time_and_the_done_stage[without-at-merge-before-approval]
   - criterion 3: tests/application/test_acceptance_merged_before_approval.py::test_an_acceptance_merged_before_approval_stamps_its_done_entry_with_the_time_and_stage. It uses the fixtures `publish("acceptance")` and `merge` and the helper `_booked`. It checks that the last record has `(at, stage) == (boundaries.clock.now(), "done")` and that its text starts with `done (pull request merged before approval); cost: `.
   - criteria 4 and 5: no test (make check / docs: none).
   Files changed: tests/domain/test_journal_stamps.py and tests/application/test_acceptance_merged_before_approval.py. No new files. The test runner imported every module. Nothing is red for the coder to fix: the story says no behaviour changes, so the coder only needs to confirm `make check` stays green.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (32.1 s)
4. coder: no source change. The story pins behaviour that already exists, and the tester's new tests pass against the current `book_merge` in `src/factory/domain/acceptance.py` and the `AcceptanceMerged` call in `src/factory/application/acceptance.py`: tests/domain/test_journal_stamps.py (the `merge-before-approval` rows `with-at` and `without-at`) and tests/application/test_acceptance_merged_before_approval.py (the new stamp test). I ran `make check` on the branch as it stands, and it ends with `check: green` (test: green, 33.1 s; coverage 99.47 %). I made no commit, because there was no code to write and nothing in this ticket's source diff to refactor. I saw nothing in the code that needed changing.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Scope: tests only. `tests/domain/test_journal_stamps.py` gains `_merge_before_approval` and a third `booking` row, `merge-before-approval`. `tests/application/test_acceptance_merged_before_approval.py` gains `test_an_acceptance_merged_before_approval_stamps_its_done_entry_with_the_time_and_stage`. No source change, which matches "No behaviour is meant to change".
      - Criterion 1: the `with-at` × `merge-before-approval` row calls `book_merge(_report(), bill([]), before_approval=True, at=at)`. It checks number 4, speaker `FACTORY`, kind `done` and `(at, stage, run) == (AT, "done", None)`. The test's name and body did not change, as the criterion requires.
      - Criterion 2: the `without-at` row of the same `booking` checks `(None, None, None)`.
      - Criterion 3: the new function pushes the report at stage `acceptance`, merges it and runs `AcceptanceMerged.handle`. `_booked` reads `done/` on `origin/main` and asserts the last record is `(FACTORY, "done")`. The test then checks that `(at, stage)` equals `(boundaries.clock.now(), "done")`, which is the fixed `ManualClock`, and that the text starts with `BEFORE_APPROVAL`. If `at` became `None` on this branch, both the domain row and this test would fail. That is the surviving mutant the story is meant to kill.
      - The rule has no rejected input and no limit, so there is no failing side to test. The side without `at` is criterion 2.
      - Criterion 4: the coder reports `make check` as `check: green` and `make duplicates` as 0 new.
      - Criterion 5: docs: none, which still holds because the project guide already describes the stamp.
      - Architecture, security and quality: there is no source diff. The test helper follows the existing `_merge`/`_refuse` pattern, and the sides of the rule are rows of one parametrized test.
6. documenter: none, so I wrote nothing new and changed no files. The diff is two test files and no source change.

   Cross-read: `docs/project-guide.md` (line 449) already says that every entry the factory appends carries `at` and `stage`, and that the acceptance's `done` entry carries `done`. That matches `book_merge` on both branches, so the guide is current. I did not read the README, the operator guide or the decision log, because this story changes nothing they describe.

   I found no stale text and no code that contradicts the Interface. I ran no `make check`, since I changed nothing outside the README and `docs/`.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands ran from the repository root and both met their Expect lines. No findings.

   Command 1 (`book_merge` with `at`, with and without `before_approval`):
   ```
   True done 2026-10-18 09:00:00+00:00 done
   False done 2026-10-18 09:00:00+00:00 done
   ```
   Met: these are exactly the two expected lines, and the process exited with 0.

   Command 2 (pytest over the five journal-stamp and acceptance test modules), trimmed:
   ```
   …
   .venv/lib/python3.12/site-packages/_pytest/pathlib.py:95
     PytestWarning: (rm_rf) error removing /tmp/pytest-of-factory/garbage-…/test_seal_takes_the_group_and_0
     <class 'OSError'>: [Errno 39] Directory not empty: …
   …
   -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
   67 passed, 6 warnings in 5.25s
   ```
   Met: the last line reports `67 passed` with no `failed`, `error` or `skipped` count. The 6 warnings come from pytest's cleanup of old temporary directories under /tmp (rm_rf on `garbage-*`), not from these tests. The Expect line does not mention warnings.

   Criteria check: criterion 1 holds. Command 1 shows that `before_approval=True` with `at` gives a `done` entry with that `at` and `stage` `done`. Criteria 2 and 3 are covered by the tests in command 2, all of which pass. The demo contradicts nothing in criteria 4 and 5: the coder and the documenter report `make check` green, and this story needs no docs. The plain branch (`False`) still stamps too, so no behaviour changed, as the assignment says.
