---
stage: tests
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
