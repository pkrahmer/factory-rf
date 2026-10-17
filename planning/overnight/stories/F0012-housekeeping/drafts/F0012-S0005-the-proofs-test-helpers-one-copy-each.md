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

- `rerun_seconds` uses `_claim_commits` and `state_at`; it raises `AssertionError` when the result has no claim commit or no `killed_at`.
- `state_at` is today's `_state_at`, made public; `_claim_commits` uses it.
- `branch_state` replaces `_branch_state` of `tests/test_fault_paths_7_to_13.py` with the same behaviour; that module imports it.
- `_kill_to_rerun_recorded` returns `rerun_seconds(result) == KILL_TO_RERUN.total_seconds()` for a case that charges a crash, `True` otherwise, and `False` when the result has no claim commit or no `killed_at`.
- `_opening_text` is renamed `_opening_document`; `_rerun` calls `rerun(world, empty_disk=empty_disk)` in place of advancing the clock and calling `restart` itself.

`tests/test_kill_points.py`: `_rerun_seconds` is removed; `test_the_rerun_starts_five_seconds_after_the_kill` records `rerun_seconds(result)` as its property, asserts it is 5.0, and also asserts `violations(result, case, ("kill-to-rerun-recorded",)) == []`.

`tests/test_fault_path_names.py` is deleted.

New tests in `tests/test_proof_support.py` (criteria 2 and 3), using `run_case` of `tests/proof_support.py` and `dataclasses.replace` on a `CaseResult`.

## Acceptance criteria

1. For each case of `KILL_POINT_CASES` that charges a crash, `rerun_seconds` of its result is 5.0, and `violations(result, case, ("kill-to-rerun-recorded",))` is `[]` (the existing test over those cases).
2. `violations(..., ("kill-to-rerun-recorded",))` of the `commit-push` case's result is `[]`, and of the same result with `killed_at` one second earlier (`dataclasses.replace`) is `["kill-to-rerun-recorded"]`. Two rows of one parametrized test.
3. `branch_state` of a world with a started and once-ticked story returns the state the branch holds (stage, round and `blocked` as `state_at` reads them at `origin/<branch>`), and of a work item without a branch returns `None`. Two rows of one parametrized test.
4. No module under `tests/` defines a function named `_rerun_seconds`, `_branch_state`, `_state_at` or `_opening_text`, and `tests/test_fault_path_names.py` does not exist.
5. Every test of `tests/test_kill_points.py`, `tests/test_fault_paths.py`, `tests/test_fault_paths_7_to_13.py` and `tests/test_fault_paths_table.py` still passes.
6. `make check` stays green.
7. docs: the project guide's command for the paths (section *Fault-injection paths*) no longer names `tests/test_fault_path_names.py`; it says that `rerun_seconds` and `branch_state` of `tests/proof_support.py` are the proof's helpers for the rerun's time and a branch's state. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
ls tests/test_fault_path_names.py; grep -rn "def _rerun_seconds\|def _branch_state\|def _state_at\|def _opening_text" tests; echo "status $?"
```
Expect: an `ls` error that the file does not exist, then `status 1`.

```bash
uv run pytest --no-header -p no:cacheprovider -q tests/test_kill_points.py tests/test_proof_support.py tests/test_fault_paths_table.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
