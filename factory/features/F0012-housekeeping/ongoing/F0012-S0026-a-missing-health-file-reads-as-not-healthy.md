---
stage: docs
pr: 176
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A missing health file reads as not healthy

## Assignment (as of log entry 1)

`factory-health` prints `healthy` and exits 0 when the state directory holds no health file. The factory writes the file only when it raises or clears a stop, so a container whose instance never got as far as its first write, or whose state directory is not the one the check reads, looks healthy (F0010's acceptance, open point 6: `factory-run` ended with status 2 while `factory-health` said `healthy`). The human's answer of 2026-10-17 (item 1.10): a missing health file after the start period reads as not healthy. The start period is Docker's (`start_period: 60s` in the compose file: a failed check in it does not count). This story makes `factory-run` write an empty health status when there is none, at the start of the instance, and `factory-health` report a missing file as not healthy (FEATURE decision 29). A damaged file still reads as healthy: every stop is raised again while its fault lasts. Two tests of F0010 change by the human's leave (FEATURE decision 43).

## Interface

`src/factory/entry/wiring.py`: `health_file(state_directory: Path) -> Path`, the path of the health file in `state_directory` (`<state_directory>/health.json`), used by `health_store` and by the two commands below.

`src/factory/entry/run.py`: `run_instance` first writes `HealthStatus()` through `health_store(settings.state_directory)` when `health_file(settings.state_directory)` does not exist, before it reads the token file; an existing file is left as it is, its stops in force. An `OSError` of that write propagates.

`src/factory/entry/health.py`, `main`: without a given `store`, when `health_file(<state directory>)` does not exist, it prints `no health status: <path> is missing` and returns 1. With a given `store`, it reads the store as today. Everything else is unchanged.

Tests: `tests/entry/test_health_missing.py` and `tests/entry/test_run_health_file.py` (with the settings and fakes `tests/entry/test_run.py` uses). By the human's leave (FEATURE decision 43), and no other change to an earlier story's test: `test_a_state_directory_without_a_health_file_is_healthy` in `tests/entry/test_health.py` becomes `test_a_state_directory_without_a_health_file_is_not_healthy`, with the line and status of criterion 1, and the row without stops of `test_the_module_run_as_a_process_exits_with_the_health_status` writes an empty health status first.

## Acceptance criteria

1. `main(["--state-directory", <a folder without health.json>])` prints `no health status: <folder>/health.json is missing` and returns 1; with a file holding no stop it prints `healthy` and returns 0; with a damaged file (`not json`) it prints `healthy` and returns 0. Rows of one parametrized test.
2. `main` with a given store and no file in the state directory reads the store: an empty store prints `healthy` and returns 0.
3. The module run as a process (`python -m factory.entry.health --state-directory <folder without the file>`) exits with status 1.
4. `run_instance` on a state directory without a health file leaves one that reads `HealthStatus()` (when no stop was raised meanwhile); on a state directory whose health file holds a stop, the stop is still in force after the instance has started (before any tick clears it).
5. `run_instance` writes the file before it reads the token file: with a missing token file it raises `SettingsInvalid` and the health file exists.
6. `run_instance` on a state directory whose path is a regular file raises `OSError` (the health file cannot be written, for a root user too) and does not clone the checkout.
7. `make check` stays green.
8. docs: the operator guide's sections *The health status file* and *The health check and the restart policy* say that `factory-run` writes an empty status when it starts and that a missing file is not healthy (`no health status: ... is missing`), which Docker counts only after the start period; the README's commands outside the image say what `factory-health` prints there now; the decision log records the answer to F0010's open point 6. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
import tempfile
from factory.entry.health import main
with tempfile.TemporaryDirectory() as folder:
    print(main(['--state-directory', folder]))
" | sed "s|/tmp/[^/]*|<tmp>|"
```
Expect: two lines: `no health status: <tmp>/health.json is missing` and `1`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures: `wiring.health_file(state_directory) -> Path` (`<dir>/health.json`; `_HEALTH_FILE_NAME` and `health_store` exist in wiring.py), `run.run_instance` (exists, run.py:88), `health.main` with its `store` keyword (exists, health.py:22). The messages, exit status and the order of the write before the token read are stated exactly.
   - Criteria: each is testable by one function or one parametrized test. Rules with both sides: missing file → not healthy against an empty file and a damaged file → healthy (1); a given store read against the missing file (2); an existing health file kept with its stop against a missing one written (4); the write before the token read (5); the unwritable state directory raises `OSError` and no clone (6). The process exit status is criterion 3.
   - Demo: runnable as written; its `Expect:` line (two lines, the path with the temporary folder masked, then `1`) can be checked against the output.
   - Architecture: the change stays in `factory.entry`, which wires, and uses the existing store behind its interface. No new dependency or layer change.
   - Scope: within F0012 scope item 1.10 and decisions 29 and 43. The two earlier tests that change are named, with the human's leave.
3. tester: red tests for the missing health file, one test per criterion.
   - criterion 1: tests/entry/test_health_missing.py::test_only_a_missing_health_file_is_not_healthy (rows missing → `no health status: <folder>/health.json is missing`, 1; empty status → `healthy`, 0; `not json` → `healthy`, 0)
   - criterion 2: tests/entry/test_health_missing.py::test_a_given_store_is_read_when_the_state_directory_has_no_health_file
   - criterion 3: tests/entry/test_health_missing.py::test_the_module_run_as_a_process_exits_one_without_a_health_file
   - criterion 4: tests/entry/test_run_health_file.py::test_run_instance_writes_an_empty_health_status_only_when_there_is_none (rows missing → the file exists and reads `HealthStatus()`; a `fetch_failed` stop already written → still there after the start, with `should_stop` true so no tick runs)
   - criterion 5: tests/entry/test_run_health_file.py::test_run_instance_writes_the_health_file_before_it_reads_the_token_file
   - criterion 6: tests/entry/test_run_health_file.py::test_run_instance_on_a_state_directory_that_is_a_file_raises_and_clones_nothing
   - Interface `health_file`: tests/entry/test_health_missing.py::test_the_health_file_lies_in_the_state_directory (`<dir>/health.json`)
   - Two earlier tests changed by the human's leave (FEATURE decision 43), as the Interface describes, and nothing else in that file: in tests/entry/test_health.py, `test_a_state_directory_without_a_health_file_is_healthy` is renamed to `..._is_not_healthy` and now expects the criterion 1 line and status 1. In `test_the_module_run_as_a_process_exits_with_the_health_status`, the row without stops now writes an empty status first (`_write` always runs).
   - Files created: tests/entry/test_health_missing.py and tests/entry/test_run_health_file.py. test_run_health_file.py has its own `settings` fixture with the same shape as test_run.py's, because that fixture lives in test_run.py and I may not change that file. The fakes (`hosting`, `remote`, `agent_home`) come from conftest.
   - One `make test` run: both new modules fail at import, because the test runner could not import `health_file` from `factory.entry.wiring`. `test_a_state_directory_without_a_health_file_is_not_healthy` fails on the wrong result. `make lint` is green. I did not run the type check, as this stage says.
   - Criterion 6 may already raise `OSError` before the change, from the later writes in the state directory. Its test pins the outcome, not the order. Criterion 5 is the test that pins the order.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/entry/test_run_health_file.py - ImportError while importing test ...
4. coder: a missing health file now reads as not healthy, and `factory-run` writes an empty health status when it starts. Commit 66c8189e.
      - `src/factory/entry/wiring.py`: new `health_file(state_directory) -> Path` returns `<dir>/health.json`. `health_store` now builds its path with it.
      - `src/factory/entry/run.py`: `run_instance` first calls `_write_an_empty_health_status_when_there_is_none`, before `read_hosting_token`. It writes `HealthStatus()` through `health_store` only when `health_file` does not exist, so an existing file keeps its stops. An `OSError` from the write propagates; when the state directory is a regular file the error comes from the write, so nothing is cloned. The docstring now names the `OSError`.
      - `src/factory/entry/health.py`, `main`: when no `store` is given and the file is missing, it prints `no health status: <path> is missing` and returns `_STOPPED` (1). With a given store it reads the store as before. A damaged file still reads as healthy, because the store's reader is unchanged.
      - Main decision: the check for a missing file sits in `main`, which knows whether a store was given. I rejected making the store's `read` report a missing file, for two reasons. The given-store path has to stay as it is (criterion 2). And `_stop_the_machine` in run.py relies on `read()` of a missing file returning an empty status.
      - Refactor: I read the diff once afterwards and found nothing to change, so there is no refactor commit.
      - Demo: its output is `no health status: <tmp>/health.json is missing`, then `1`, as the ticket expects.
      - Not touched: the docs (criterion 8) are the documenter's work.
      - Open point for review: no test drives `factory-run` to a status-2 exit and checks the health file. When the settings are invalid, `main` never reaches `run_instance`, so the file is written only by `_stop_the_machine`, as before.

      `make check`: check: green

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Criteria 1–6: each has a test in `tests/entry/test_health_missing.py` or `tests/entry/test_run_health_file.py`, and each test checks what its criterion says. Criterion 1 is one parametrized test with three rows: missing, empty and damaged. Criterion 4 covers both sides: a missing file gets written, and an existing stop is kept (`should_stop` is true, so no tick runs). Criterion 5 tests the order: with no token file, `SettingsInvalid` is raised and the health file still exists. Criterion 6 checks for `OSError` and that nothing is cloned. The Interface's `health_file` has its own test. The two F0010 tests changed exactly as the Interface describes (FEATURE decision 43), and no other earlier test changed. The coder's entry has `make check` green and `make duplicates` at 0 new.
      - Architecture: the change stays in `factory.entry`. `run.py` and `health.py` reach the file only through `wiring.health_file` and `health_store`, and `health_store` now builds its path with `health_file`, so the path is defined once. `replace_text` creates the state directory when it is missing, so the first write also works on a fresh volume.
      - Security: no suppression markers, no strings built into commands, and the missing-file message prints only the path the operator gave.
      - Quality: the docstrings of `main` and `run_instance` describe the new behaviour, including the `OSError`. The comment on `_write_an_empty_health_status_when_there_is_none` says why the write is there. No dead code.
      - Ticket: the log gives the main decision: the missing-file check is in `main`, not in the store's `read`, because criterion 2 and `_stop_the_machine` both rely on how `read` works today. `Assignment` matches what was built, and the docs criterion (8) is still accurate.
      - Coder's open point: when `factory-run` exits with status 2 on invalid settings, it never writes the file. That is not a gap: with no file, `factory-health` now reports not healthy, which is the fix for F0010 open point 6.
