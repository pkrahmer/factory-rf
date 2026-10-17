---
stage: accept
pr: 177
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A standing main_branch_failing cleared when main moves

## Assignment (as of log entry 1)

The preflight probes `main` with `lint` only after the machine's items have passed. When they fail (a new image without `make`, say), the preflight stops with `preflight_failed` and returns before the probe, so a `main_branch_failing` raised earlier stays in the health status even after the human has pushed the fix to `main` (F0010's acceptance, open point 5; `docs/decisions.md`, the S0009 entry's "Open:"). The human's answer of 2026-10-17 (item 1.10): a standing `main_branch_failing` is cleared when `main` is green again. Whether the new `main` is green cannot be known while the machine cannot run `lint`; what is known is that the stop names a commit that is no longer `main`. This story clears the stop then, and the new `main` is probed as soon as the machine's items pass again, which raises the stop anew if it is red (FEATURE decision 30). A stop whose commit is still `main` stays.

## Interface

`src/factory/application/preflight.py`, `Preflight.run`: when the machine's items fail, before it returns `preflight_failed`, it reads the stamp it started with. When that stamp has a `main_failed` commit and `git.resolve("origin/main")` gives another commit (or `None`), it calls `clear_stop("main_branch_failing")`; when it gives the same commit, or the stamp has no `main_failed`, the stop is left as it is. A `GitError` of the `resolve` leaves the stop as it is and does not change the result. The result is still `preflight_failed`, and the stamp is not rewritten. Nothing else in the preflight changes.

Tests: `tests/application/test_preflight_stale_main_stop.py`, with the `rig` and `red_main` fixtures of `tests/application/test_preflight_run.py` (imported or rebuilt the same way): a red `main` probed once (so the stamp holds `main_failed`), then the machine's items made to fail by removing `make` from the rig's `which` and running the preflight with another image. No existing test changes.

## Acceptance criteria

1. After `main` has moved on from the failing commit (the human's fix pushed) or is gone (the preflight's git a clone of an empty remote, as `test_without_an_origin_main_no_lint_runs_and_the_preflight_passes` builds it), a preflight whose machine's items fail returns `preflight_failed`, the health status holds `preflight_failed` and no `main_branch_failing`, the factory log gains `stop cleared main_branch_failing`, and the stamp is as it was. Two rows of one parametrized test.
2. When `main` has not moved, the same preflight returns `preflight_failed`, the health status holds both stops, `main_branch_failing` with its earlier detail, and the stamp is as it was.
3. When the stamp has no `main_failed` (a green `main` probed before) and a `main_branch_failing` stands (written into the health status as `Rig.raise_standing` does), the machine's failure returns `preflight_failed` and leaves both stops in force.
4. When git cannot resolve `origin/main` (the checkout removed, as `test_a_git_error_while_probing_is_a_machine_stop_and_leaves_the_stamp` removes it), the machine's failure leaves `main_branch_failing` in force and the result `preflight_failed`.
5. When the machine's items pass again on the fixed `main`, the preflight probes it once: green clears nothing more and returns `None`; red raises `main_branch_failing` for the new commit. Two rows of one parametrized test.
6. Every test of `tests/application/test_preflight_run.py` and `tests/application/test_tick_preflight.py` still passes.
7. `make check` stays green.
8. docs: the operator guide's section *The stamp and the probe of the main branch* says that while the machine's items fail, a `main_branch_failing` of a commit that is no longer `main` is cleared, and that the new `main` is probed when the machine passes again; the decision log answers the S0009 entry's open point (the human's answer of 2026-10-17). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_preflight_stale_main_stop.py tests/application/test_preflight_run.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names `src/factory/application/preflight.py`, `Preflight.run`, `git.resolve("origin/main")` and `clear_stop("main_branch_failing")`. It states each case: the same commit, a different commit, `None`, no `main_failed` in the stamp, a `GitError`. The result stays `preflight_failed` and the stamp is not rewritten. The `rig`, `red_main` and `Rig.raise_standing` names it cites exist in `tests/application/test_preflight_run.py`, and `preflight.py` already compares `stamp.main_failed` with `main`.
   - Criteria: each one is a single test, or two parametrized rows (1 and 5). Every behaviour the Interface states has a criterion on the passing side and the failing side: moved or gone is 1, unmoved is 2, no `main_failed` is 3, a git error is 4, and the later probe, green or red, is 5. The pass-through of existing tests is 6, and `make check` and `docs:` come last.
   - Demo: one runnable pytest command over two named test files. Its `Expect:` line names the last line's form (`<n> passed in <t>s`, with no failed, error or skipped count), which can be checked against the output.
   - Architecture: the change sits in the application layer and uses only the existing git and stop-clearing interfaces. It adds no dependency and no new module, and the only test file is the new one in `tests/application/`.
   - Scope: this is item 1.10 of FEATURE.md. It matches FEATURE decision 30, which the human confirmed in decision 47, and nothing in "Out of scope" applies.
3. tester: Wrote the tests for the acceptance criteria in a new file, `tests/application/test_preflight_stale_main_stop.py`. It reuses the `rig` and `red_main` fixtures of `tests/application/test_preflight_run.py`, assigned as module attributes so that ruff raises no F811, and imports `IMAGE`, `OTHER_IMAGE`, `TOOLS` and `Rig` from that file. A shared fixture `failed_once` probes the red main once and asserts that the stamp holds `main_failed`. To make the machine's items fail, each test removes `make` from the rig's `which` and runs the preflight with `OTHER_IMAGE`.

   - criterion 1: tests/application/test_preflight_stale_main_stop.py::test_a_failed_machine_clears_the_stop_of_a_main_that_moved_on, rows `moved` (BROKEN removed from main) and `gone` (git swapped for a clone of an empty bare remote). Each row checks the result, that the health status reasons are exactly `["preflight_failed"]`, that the log has a line ending `stop cleared main_branch_failing`, and that the stamp is unchanged.
   - criterion 2: tests/application/test_preflight_stale_main_stop.py::test_a_failed_machine_keeps_the_stop_of_a_main_that_has_not_moved (both stops stand, `main_branch_failing` keeps its earlier detail, the stamp is unchanged).
   - criterion 3: tests/application/test_preflight_stale_main_stop.py::test_a_failed_machine_keeps_a_standing_stop_when_the_stamp_names_no_failed_main (a green main probed first, then a `main_branch_failing` written with `Rig.raise_standing`).
   - criterion 4: tests/application/test_preflight_stale_main_stop.py::test_a_failed_machine_keeps_the_stop_when_git_cannot_resolve_main (the checkout removed with `shutil.rmtree`).
   - criterion 5: tests/application/test_preflight_stale_main_stop.py::test_the_moved_main_is_probed_once_when_the_machine_passes_again, rows `green` (BROKEN removed, the run returns `None` and no `main_branch_failing` stands) and `red` (an unrelated commit pushed: `main_branch_failing` is raised with a detail naming the new commit). Both rows check that `lint` ran exactly twice in total and that no `preflight_failed` remains.
   - criterion 6: no new test. The existing files `tests/application/test_preflight_run.py` and `tests/application/test_tick_preflight.py` are left unchanged.

   Result of the one `make test` run: only the two rows of criterion 1 fail, on assertions, not on import or collection errors. Every module imported fine, because the change goes into the existing `Preflight.run`. The tests for criteria 2–5 already pass on the current code: they pin behaviour the coder must keep. Criterion 5 passes because the later run with a new image probes the moved main whether or not the stop was cleared before. `make lint` is green. I skipped the type check, as this stage's instructions say.

   No criterion needed interpreting. I decided not to add, to criteria 2–4, a check that no "stop cleared" line was logged, because the criteria do not ask for it.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/application/test_preflight_stale_main_stop.py::test_a_failed_machine_clears_the_stop_of_a_main_that_moved_on[gone]
4. coder: Implemented the change in `src/factory/application/preflight.py` (commit ebb5d7d1). `Preflight.run` now keeps the stamp it read at the start (`started_with`). When the machine's items fail, it calls a new private method, `_clear_stale_failing_stop`, before it returns `preflight_failed`. That method does nothing if there is no stamp or the stamp has no `main_failed`. Otherwise it resolves `origin/main`; a `GitError` leaves the stop in place. If the result differs from `main_failed`, which includes `None`, it calls `clear_stop("main_branch_failing")`. The stamp is never rewritten on this path, and the rest of the preflight is unchanged.

   Main design decision: I passed in the stamp read before the machine's items run. The alternative was to read the store again after they fail. I rejected it because the Interface asks for "the stamp it started with", and one read keeps the path free of a second I/O call. I also kept the check separate from `_probe`, because `_probe` assumes the machine has passed: it checks out main and runs `lint`.

   Refactor: I read the diff as a reviewer would and found nothing to change. It is one small method and a two-line change in `run`.

   `make check`: green. The new test file, `tests/application/test_preflight_run.py` and `tests/application/test_tick_preflight.py` all pass. Nothing else noticed. The docs criterion is left to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–5 has a test in `tests/application/test_preflight_stale_main_stop.py`, and criteria 1 and 5 are two parametrized rows each. Every behaviour the Interface states is tested from both sides:
        - a moved or gone `main` clears the stop (criterion 1);
        - the same commit keeps the stop (criterion 2);
        - no `main_failed` in the stamp keeps the stop (criterion 3);
        - a `GitError` keeps the stop, and the error would propagate without the `except` (criterion 4);
        - the stamp is left as it was (checked in 1 and 2).
        A wrong implementation would fail at least one of these: one that always clears fails 2 and 3, one that never clears fails 1. Criterion 6 holds: neither existing test file is in the diff. The coder's entry records `check: green`.
      - Architecture: the change stays inside `factory.application.preflight`. It reaches git only through `Boundaries.git` and clears the stop only through `StopService`. It adds no new import, dependency or module.
      - Security: nothing applies. The diff adds no markers, no string-built commands and no new input boundary.
      - Quality: `_clear_stale_failing_stop` (`src/factory/application/preflight.py:323`) does one thing and reuses `_MAIN_REF` and `_MAIN_FAILING`. Its comment says why, and it has no docstring because it is private. Keeping it separate from `_probe` is right, because `_probe` checks out `main` and runs `lint`. `make duplicates` reports 0 new findings.
      - Ticket hygiene: the coder's entry explains the main decision (pass in the stamp read at the start) and what it rejected (reading the store again). `Assignment` matches the code. The docs criterion still describes what the documenter must write.
6. documenter: - `docs/operator-guide.md`, "The stamp and the probe of the main branch": new bullet saying that while the machine's items fail, a `main_branch_failing` whose commit is no longer `origin/main` (moved or gone) is cleared, the result stays `preflight_failed`, the stamp is not rewritten, the new `main` is probed when the machine passes again, and a stop whose commit is still `main` (or when git cannot resolve it) stays.
   - `docs/decisions.md`: new entry at the end answering the S0009 entry's open point (the human's answer of 2026-10-17), with what was rejected.
   - Cross-read the diff of `src/factory/application/preflight.py` against the operator guide's stop table and the tick section; both are still true. `python -m factory.entry.check_documents` prints `documents ok`. No `make check` run: only documents changed. No findings; the code matches the Interface.
   - Stale but untouched: the S0009 entry in the decision log still carries its "Open:" text; the log is a history, so the new entry answers it instead.

   `make check`: check: green
   `make documents`: documents ok
7. demo: no findings.

   Command 1: `uv run pytest --no-header -p no:cacheprovider tests/application/test_preflight_stale_main_stop.py tests/application/test_preflight_run.py`
   ```
   ...........................                                              [100%]
   27 passed in 2.07s
   ```
   This met its `Expect:` line. The last line reads `<n> passed in <t>s`, with no failed, error or skipped count.

   Checked against the acceptance criteria:
   - Criteria 1–5: the new test file passes in full.
   - Criterion 6: `test_preflight_run.py` passes in this run. Neither existing test file appears in the diff against `origin/main`. `test_tick_preflight.py` was not run in this demo.
   - Criterion 8: `docs/decisions.md` and `docs/operator-guide.md` are the only documents changed against `origin/main`, and `python -m factory.entry.check_documents` prints `documents ok`.
   - Criterion 7: I did not run `make check` again. The coder's entry records `check: green`, and the factory runs the check itself after this stage.

   Nothing in the demo contradicts a criterion.
