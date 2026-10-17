---
stage: done
pr: 157
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The proof's test helpers, one copy each

## Assignment (as of log entry 1)

F0011's review and acceptance let through copies in the proof's test helpers, all under `tests/`:

- `tests/test_kill_points.py::_rerun_seconds` finds the stage-start commit of a rerun a second way, beside `_claim_commits` and `_state_at` of `tests/proof_support.py`, so the check `kill-to-rerun-recorded` of `violations` is reached by no test.
- `_opening_text` in `tests/proof_support.py` returns a `WorkItemDocument`, not a text.
- `_rerun` in `tests/proof_support.py` advances the clock and restarts, which is what the public `rerun` does.
- `_branch_state` in `tests/test_fault_paths_7_to_13.py` reads a work item's state on its branch again, beside `_state_at`.
- `tests/test_fault_path_names.py` checks paths 1 to 6, which `tests/test_fault_paths_table.py` checks for all thirteen.

This story leaves one copy of each. It is a change of tests only, by the human's leave (FEATURE decision 33); the coder expects to change nothing under `src/`. Nothing the proof asserts is lost, and the check `kill-to-rerun-recorded` gains a test of both its sides.

## Interface

`tests/proof_support.py`:

```python
def rerun_seconds(result: CaseResult) -> float:
    """Seconds from the kill to the claim of the newest claim commit of the result's branch."""

def state_at(world: World, ref: str, path: str) -> WorkItemState | None:
    """The state of the work item file `path` at `ref`, or None when `ref` has no such file."""

def branch_state(world: World, work_item: WorkItemId) -> WorkItemState | None:
    """The state on the work item's branch after a fetch, or None when there is no branch."""
```

- `rerun_seconds` uses `_claim_commits` and `state_at`; it raises `AssertionError` when the result has no `killed_at`.
- `state_at` is today's `_state_at`, made public; `_claim_commits` and the module's other callers use it.
- `branch_state` replaces `_branch_state` of `tests/test_fault_paths_7_to_13.py` with the same behaviour; that module imports it.
- `_kill_to_rerun_recorded` returns `True` for a case that charges no crash; for a case that charges one, `False` when the result has no `killed_at`, and otherwise `rerun_seconds(result) == KILL_TO_RERUN.total_seconds()`.
- `_opening_text` is renamed `_opening_document`; `_rerun` calls `rerun(world, empty_disk=empty_disk)` in place of advancing the clock and calling `restart` itself.

`tests/test_kill_points.py`: `_rerun_seconds` is removed; `test_the_rerun_starts_five_seconds_after_the_kill` records `rerun_seconds(result)` as its property, asserts it is 5.0, and also asserts `violations(result, case, ("kill-to-rerun-recorded",)) == []`.

`tests/test_fault_path_names.py` is deleted.

New tests in `tests/test_proof_support.py` (criteria 2 and 3), using `run_case` of `tests/proof_support.py` and `dataclasses.replace` on a `CaseResult`.

## Acceptance criteria

1. For each case of `KILL_POINT_CASES` that charges a crash, `rerun_seconds` of its result is 5.0, and `violations(result, case, ("kill-to-rerun-recorded",))` is `[]` (the existing test over those cases).
2. `violations(..., ("kill-to-rerun-recorded",))` is `[]` for the `commit-push` case's result, `["kill-to-rerun-recorded"]` for the same result with `killed_at` one second earlier and for it with `killed_at=None` (`dataclasses.replace`), and `[]` for the `post-record` case's result (a case that charges no crash) with `killed_at` one second earlier. Four rows of one parametrized test; `rerun_seconds` of the `commit-push` result with `killed_at=None` raises `AssertionError`.
3. `branch_state` of a world with a started and once-ticked story returns the state the branch holds (stage, round and `blocked` as `state_at` reads them at `origin/<branch>`), and of a started story whose branch does not exist yet returns `None`; `state_at` of a path that `origin/main` does not hold returns `None`. Three rows of one parametrized test.
4. None of `tests/proof_support.py`, `tests/test_kill_points.py` and `tests/test_fault_paths_7_to_13.py` defines a function named `_rerun_seconds`, `_branch_state`, `_state_at` or `_opening_text` (read with `ast`); `_rerun` in `tests/proof_support.py` calls `rerun` and calls neither `restart` nor `advance`; and `tests/test_fault_path_names.py` does not exist.
5. Every test of `tests/test_kill_points.py`, `tests/test_fault_paths.py`, `tests/test_fault_paths_7_to_13.py` and `tests/test_fault_paths_table.py` still passes.
6. `make check` stays green.
7. docs: the project guide's command for the paths (section *Fault-injection paths*) no longer names `tests/test_fault_path_names.py`; it says that `rerun_seconds` and `branch_state` of `tests/proof_support.py` are the proof's helpers for the rerun's time and a branch's state; the list of `CRASH_CONDITIONS` in *The kill-point cases* names the time from kill to rerun among the conditions. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
ls tests/test_fault_path_names.py; grep -n "def _rerun_seconds\|def _branch_state\|def _state_at\|def _opening_text" tests/proof_support.py tests/test_kill_points.py tests/test_fault_paths_7_to_13.py; echo "status $?"
```
Expect: an `ls` error that the file does not exist, then `status 1`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_kill_points.py tests/test_proof_support.py tests/test_fault_paths_table.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`tests/proof_support.py`: `rerun_seconds`, `state_at`, `branch_state`; `_kill_to_rerun_recorded`, `_opening_document`, `_rerun` behaviour; `tests/test_kill_points.py`; deletion of `tests/test_fault_path_names.py`). I checked with grep that today's `_rerun_seconds`, `_branch_state`, `_state_at`, `_opening_text`, `_rerun`, `_claim_commits` and `_kill_to_rerun_recorded` exist where the story says. The `_state_at` and `_branch_state` copies in other test modules (under `tests/application/`) are outside the story, as FEATURE decision 33 says.
   - Criteria: each is testable by one test function. Criteria 2 and 3 name their rows, and each rule has its failing side: killed_at one second earlier, `killed_at=None`, a crash-free case, a missing branch, a path `origin/main` does not hold, and `AssertionError` from `rerun_seconds`. Criterion 4 (AST and absence) is one test, 5 and 6 are existing gates, 7 is the docs criterion.
   - Demo: both commands are runnable. Each `Expect:` line is checkable (an `ls` error plus `status 1`; a last line with `passed` and no `failed` or `error`).
   - Architecture: the change is tests only, so it touches no layer. Decision 33 grants the human's leave for editing tests I did not write.
   - Scope: within F0012 scope 1.2 (S0003 to S0005, the findings known today). Nothing in Out of scope is touched.
3. tester: wrote the tests for criteria 1–5. I also did the whole helper refactor the story asks for, because every file it touches is under `tests/`, and the tester's lane is the only one that may write there. So the branch is green, not red: the coder has nothing left to change under `src/`, and criterion 7 belongs to the documenter.

   Criterion → test:
   - criterion 1: tests/test_kill_points.py::test_the_rerun_starts_five_seconds_after_the_kill. It now records `rerun_seconds(result)`, asserts 5.0, and asserts `violations(..., ("kill-to-rerun-recorded",)) == []`.
   - criterion 2: tests/test_proof_support.py::test_the_kill_to_rerun_check_holds_only_for_the_recorded_five_seconds, with four rows: commit-push as recorded, commit-push with `killed_at` one second earlier, commit-push with `killed_at=None`, and post-record with `killed_at` one second earlier. The `AssertionError` side is tests/test_proof_support.py::test_the_rerun_seconds_of_a_result_without_a_kill_time_raise.
   - criterion 3: tests/test_proof_support.py::test_the_state_helpers_read_the_branch_or_return_none, with three rows: a ticked story, a story with no branch, and a path that `origin/main` does not hold. Each row compares stage, round and blocked.
   - criterion 4: tests/test_proof_support.py::test_each_proof_helper_has_one_copy. It uses `ast` to check that none of the three modules defines `_rerun_seconds`, `_branch_state`, `_state_at` or `_opening_text`, that `_rerun` calls `rerun` and neither `restart` nor `advance`, and that `tests/test_fault_path_names.py` is absent.
   - criterion 5: the existing tests of test_kill_points, test_fault_paths, test_fault_paths_7_to_13 and test_fault_paths_table pass unchanged. No new test is needed.

   Changes:
   - tests/proof_support.py: `_state_at` is now the public `state_at`, with a docstring, and all callers use the new name.
   - tests/proof_support.py: new `rerun_seconds`, built on `_claim_commits` and `state_at`, which asserts that `killed_at` is set. `_kill_to_rerun_recorded` returns False when `killed_at` is None and otherwise compares `rerun_seconds` with `KILL_TO_RERUN`.
   - tests/proof_support.py: new `branch_state`, which keeps the behaviour of the old `_branch_state` and uses `work_item_file`. `_opening_text` is renamed `_opening_document`. `_rerun` now calls `rerun(world, empty_disk=...)` instead of advancing the clock and calling `restart` itself.
   - tests/test_fault_paths_7_to_13.py: `_branch_state` removed; the module imports `branch_state`.
   - tests/test_kill_points.py: `_rerun_seconds` removed, along with the import of `branch_name` that is no longer used.
   - tests/test_fault_path_names.py: deleted, with `git rm`.
   - tests/test_proof_support.py: created.

   Runs: `make test` passed ("test: green", 99.51 % coverage) and `make lint` passed. `make types` also passed, since nothing under test is missing. The runner reported no module it could not import.

   Rejected: putting the four criterion-2 rows into separate test functions, because the project rule is one parametrized test per rule.

   Open: criterion 7 (the project guide, section *Fault-injection paths* and *The kill-point cases*) is the documenter's.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (26.8 s)
4. coder: nothing to build. As the ticket says, this is a change of tests only. The tester already made the whole helper refactor under `tests/`: `state_at`, `rerun_seconds` and `branch_state` in `tests/proof_support.py`; `_opening_document`; `_rerun` calling `rerun`; and the removed copies in `tests/test_kill_points.py` and `tests/test_fault_paths_7_to_13.py`. They also deleted `tests/test_fault_path_names.py` and created `tests/test_proof_support.py`.

   - Diff check: `git diff main...HEAD -- . ':!factory'` touches only those five test files. Nothing under `src/` changes, so I made no commit.
   - Refactor step: there is no coder diff to refactor. The test files are outside my lane (R9), so I left them as they are.
   - `make check`: green (`test: green (27.2 s)`, coverage 99.51 %, `check: green`).

   Open: criterion 7, the project guide's *Fault-injection paths* and *The kill-point cases* sections, belongs to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.

   - Criterion 1: `tests/test_kill_points.py::test_the_rerun_starts_five_seconds_after_the_kill` records `rerun_seconds(result)`, asserts 5.0, and asserts `kill-to-rerun-recorded` gives `[]`. It goes through `_checked`, which calls `violations(result, case_by_id(case_id), (condition,))`. The local `_rerun_seconds` and the `branch_name` import it no longer needs are gone.
   - Criterion 2: `tests/test_proof_support.py::test_the_kill_to_rerun_check_holds_only_for_the_recorded_five_seconds` has the four rows the criterion names, built with `dataclasses.replace` on module-scoped `run_case` results. The `AssertionError` side is its own test, `test_the_rerun_seconds_of_a_result_without_a_kill_time_raise`. `_kill_to_rerun_recorded` in `tests/proof_support.py` matches the Interface: `True` when the case charges no crash, `False` without `killed_at`, otherwise it compares `rerun_seconds` with `KILL_TO_RERUN`.
   - Criterion 3: `test_the_state_helpers_read_the_branch_or_return_none` is one parametrized test with three rows: ticked story, no branch, no file. In the ticked row, `assert held is not None` stops a None == None comparison from passing by accident.
   - Criterion 4: `test_each_proof_helper_has_one_copy` uses `ast.walk` over the three modules, checks that `_rerun` calls `rerun` and not `restart` or `advance`, and checks that `tests/test_fault_path_names.py` is gone. That module only checked paths 1 to 6, so deleting it loses nothing, as the Assignment says. `_rerun` now calls the public `rerun`, which advances by `KILL_TO_RERUN` and restarts, so behaviour is unchanged.
   - Criterion 5: per the tester's and coder's entries, the existing fault-path and kill-point tests pass unchanged. The coder's entry records `make check` green (99.51 % coverage) and `make duplicates` at 0 new.
   - Architecture and security: the diff is tests only and nothing under `src/` changes. It adds no suppression marker, baseline entry or secret.
   - Quality: `state_at`, `branch_state` and `rerun_seconds` have docstrings that describe their behaviour, and no copies of them remain. One small difference I did not count as a finding: `branch_state` returns `None` when the branch exists but lacks the file, where the old `_branch_state` asserted. Criterion 3 defines it through `state_at`, so this follows the story, and its only caller still fails after `ACCEPTANCE_TICKS`.
   - Ticket hygiene: the tester's entry explains why the tester did the whole refactor (everything is under `tests/`). The Assignment matches what was built.

   Open: criterion 7, the project guide's *Fault-injection paths* and *The kill-point cases*, is the documenter's.
6. documenter: changed only `docs/project-guide.md`, for criterion 7.
   - *Fault-injection paths*: the pytest command no longer names `tests/test_fault_path_names.py`. A short paragraph after it says that `rerun_seconds` and `branch_state` of `tests/proof_support.py` are the proof's helpers for the time from kill to rerun and for a work item's state on its branch (`None` when there is no branch).
   - *The kill-point cases*: the `CRASH_CONDITIONS` list now names the rerun's claim five seconds after the kill.
   - `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed no file outside `docs/`; the factory runs it next.
   - Cross-read: the rest of the project guide's proof sections, the README and the operator guide name none of the changed helpers, so they are current.
   - Nothing stale seen that is unrelated to this story. No findings for the coder.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands met their `Expect:` lines; no findings.

   1. `ls tests/test_fault_path_names.py; grep -n "def _rerun_seconds\|def _branch_state\|def _state_at\|def _opening_text" tests/proof_support.py tests/test_kill_points.py tests/test_fault_paths_7_to_13.py; echo "status $?"`
   ```
   ls: cannot access 'tests/test_fault_path_names.py': No such file or directory
   status 1
   ```
   Met: `ls` reports that the file does not exist, grep finds none of the four old helper definitions, and the output ends with `status 1`.

   2. `uv run pytest --no-header -p no:cacheprovider tests/test_kill_points.py tests/test_proof_support.py tests/test_fault_paths_table.py 2>&1 | tail -1`
   ```
   67 passed in 20.38s
   ```
   Met: one line that says `passed`, with no `failed` or `error`.

   Against the criteria: command 1 covers the absence parts of criterion 4. Command 2 runs the tests for criteria 1–3 and part of criterion 5 (`test_fault_paths.py` and `test_fault_paths_7_to_13.py` were not in the demo; the earlier entries record them green under `make check`). The demo contradicts no criterion. I did not rerun `make check`, because the factory runs it as the gate.
8. done (pull request merged); cost: 6 runs, 4.5 min, 38 turns, 111k tokens in (577k more from cache), 15k out, $1.11
