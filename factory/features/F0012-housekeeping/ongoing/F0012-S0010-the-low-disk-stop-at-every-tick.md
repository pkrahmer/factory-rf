---
stage: docs
pr: 162
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The low-disk stop at every tick

## Assignment (as of log entry 1)

With the free space readable (F0012-S0009), the factory stops before a write can hang: at the start of every tick, before the fetch, it reads the free space of the work directory (the checkout's parent) and of the state directory, and when either has less than `FACTORY_MIN_FREE_GB` it raises a machine stop `disk_low`, which the health status and the factory log show, and ends the tick. A free space that cannot be read is the same stop, with the error as its detail (loud over lucky). The stop is cleared by the first tick that finds enough room. One check per tick covers the preflight too, because the preflight runs inside the tick (FEATURE decision 20). The stop is a new row of `STOP_TABLE`, `disk-low`, with v1's limit L64 (the machine's own stops never reached a pull request), so the stop table's tests, the operator guide's table of stops and the document check hold it. The tests of the stop table and of the stops' scopes gain the new reason, by the human's leave (FEATURE decision 34).

## Interface

`src/factory/domain/stops.py`:

- `RepositoryStopReason` gains `"disk_low"`, after `"preflight_failed"`.
- The scope rule of `RepositoryStop`: the scope is `machine` for `preflight_failed` and `disk_low`, `repository` for every other reason (a `ValueError` from the model validator otherwise, as today).

`src/factory/domain/stop_table.py`: `STOP_TABLE` gains, after `preflight-failed`, the row `StopRow(id="disk-low", limits=("L64",), destination="health_status", reason="disk_low", test="test_repository_stop_reaches_the_health_status_and_the_factory_log")`: fifteen rows. The guide's description of the row: the work or the state directory has less free space than the setting asks for, or its free space cannot be read.

`src/factory/application/tick.py`, `Tick.run`: a first step before the fetch. When `boundaries.disk` or `boundaries.settings` is `None`, it does nothing (so every test that builds boundaries without them ticks as before). Otherwise it reads `disk.free_bytes` of `settings.checkout.parent` and of `settings.state_directory`, in that order:

- every path read, `disk_low_detail(free, settings.min_free_gb)` is `None`: `clear_stop("disk_low")`, and the tick goes on;
- a detail: `raise_stop(RepositoryStop(scope="machine", reason="disk_low", detail=<the detail>, at=<now>))`, and the tick ends with `TickOutcome(stopped="disk_low")`, before the fetch;
- an `OSError` for a path: no later path is read, the stop's detail is `cannot read the free space of <path>: <error>` for that path alone, and the tick ends the same way.

Tests: `tests/application/test_tick_disk.py`, on the boundaries of `tests/conftest.py` with `disk` and `settings` replaced (`dataclasses.replace`), the settings' `checkout` and `state_directory` under `tmp_path`, the handlers `{"idle": IdleHandler()}`, and the agents of `PIPELINE_YAML`'s roles installed with `install_agents` of `tests/git_support.py`, as `tests/application/test_tick.py` does (without them the load step stops the tick at `agent_definition_invalid`). The fake disk is `FakeDiskSpace` in a new shared helper module `tests/disk_support.py`, deriving from `DiskSpace`: it is given, per path, a byte count or an `OSError` for `free_bytes` and for `used_bytes`, raises the `OSError` it was given for a path, and keeps the paths it was asked, in order, in `asked`. F0012-S0016 and F0012-S0017 import it.

By the human's leave (FEATURE decision 34), and no other change to an earlier story's test: in `tests/domain/test_stop_table.py` the row `disk-low` joins `ROWS` after `preflight-failed`, and `test_the_table_holds_the_fourteen_stops_in_order` becomes `test_the_table_holds_the_fifteen_stops_in_order`; in `tests/test_stop_table.py`, `test_repository_stop_reaches_the_health_status_and_the_factory_log` gives `disk_low` the scope `machine`; in `tests/domain/test_stops.py`, `SCOPES` gains `("disk_low", "machine")`; in `tests/entry/test_health.py`, `disk_low` joins the reasons of `test_every_stop_reason_makes_the_check_fail_until_it_is_cleared`.

## Acceptance criteria

1. A `RepositoryStop` of reason `disk_low` is accepted with scope `machine` and refused with scope `repository`; `preflight_failed` keeps its scope `machine` and every other reason `repository` (the rows of `SCOPES`).
2. `STOP_TABLE` holds fifteen rows, `disk-low` the eighth, after `preflight-failed`, with the values of the Interface; every value of `RepositoryStopReason` is the reason of exactly one row.
3. A tick whose fake disk gives both paths exactly `min_free_gb * GIGABYTE` bytes runs on: its outcome is not `stopped`, and the health status holds no `disk_low` stop.
4. With the work directory one byte short, the tick ends with `TickOutcome(stopped="disk_low")` before the fetch: a commit the human pushed to `main` after the checkout was cloned is not at the checkout's `origin/main` after the tick.
5. That stop is in the health status with scope `machine` and the detail `disk_low_detail` gives for the paths read, and the factory log gains one line that ends with `stop machine disk_low: ` and that detail.
6. With the state directory short and the work directory not, the detail names the state directory only; with both short, both, the work directory first. Rows of one parametrized test.
7. A fake disk that raises `OSError("no such device")` for the state directory stops the tick with the detail `cannot read the free space of <state directory>: no such device`; one that raises it for the work directory stops the tick with `cannot read the free space of <work directory>: no such device` and is asked for no other path, also when the state directory is short. Rows of one parametrized test.
8. After a stopped tick, a tick with enough room clears the stop: the health status holds no `disk_low` stop and the factory log gains `stop cleared disk_low`.
9. A tick on boundaries with a fake disk and without `settings` asks the fake for no path and runs on; a tick on boundaries without `disk` runs on. Two rows of one parametrized test.
10. The string `disk_low` occurs as a string constant in a module of `src/factory/application` (the existing test over every reason).
11. `make check` stays green.
12. docs: the operator guide's table *The stops* gets the row `` `disk-low` `` (health status and factory log; the work or the state directory has less free space than `FACTORY_MIN_FREE_GB` asks for, or its free space cannot be read; what you do: make room on the file system the detail names, and nothing more, because the next tick clears the stop); its settings row for `FACTORY_MIN_FREE_GB` says what it guards; its section *The health status file* gives `disk_low` the scope `machine` beside `preflight_failed` and lists it among the reasons; its section *The stops of the tick* says that the tick reads the free space first, before the fetch. The project guide's section *The tick* names the first step and its order before the fetch. The decision log records the stop: why before the fetch, why one check per tick and not a preflight item, why an unreadable free space stops too, that the first clone of a missing checkout comes before the first check, and that on a full disk an `OSError` of the stop's own writes ends the iteration with the scheduler's `iteration failed` line. `python -m factory.entry.check_documents` prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.stop_table import STOP_TABLE
row = STOP_TABLE[7]
print(len(STOP_TABLE), row.id, row.destination, ','.join(row.limits), row.reason)
"
```
Expect: `15 disk-low health_status L64 disk_low`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_tick_disk.py tests/domain/test_stop_table.py tests/test_stop_table.py
uv run python -m factory.entry.check_documents
```
Expect: the pytest run's last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count; then the single line `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures: `domain/stops.py` (`RepositoryStopReason` gains `disk_low`, scope rule), `domain/stop_table.py` (the full `disk-low` row, fifteen rows), `application/tick.py` `Tick.run` (first step, no-op when `disk` or `settings` is `None`, read order, the three outcomes), the test module and the shared `FakeDiskSpace` in `tests/disk_support.py`. The human's leave for the four earlier tests is spelled out (FEATURE decision 34).
   - Criteria: each is testable by one test function. Every Interface behaviour has a criterion: scope rule (1), the row (2), the clear (8), the order of paths and the details (6), the no-op without `disk` or `settings` (9). Each rule has its failing side: exact threshold passes (3) and one byte short stops before the fetch (4); the stop's health status and log line (5); an unreadable path, with no later path read (7); a refused `repository` scope for `disk_low` (1). Criterion 10 is the existing all-reasons test.
   - Demo: both blocks are runnable. `STOP_TABLE[7]` is the eighth row, and the Expect line `15 disk-low health_status L64 disk_low` is checkable. The pytest and `documents ok` expectations are checkable against the output.
   - Architecture: the reason and scope rule are in domain, the check is in the application's `Tick` through the `DiskSpace` interface (from S0009), and the tests use a fake that derives from the interface. This fits the layering and CLAUDE.md.
   - Scope: within F0012 item 1.4 (low-disk stop, decision 20). Nothing in "Out of scope" is touched. The docs criterion (12) lists the guide, decision-log and document-check updates.
3. tester: Tests written. They are red on purpose: `make test` fails in `tests/application/test_tick_disk.py`, where the tick does not check the disk yet. All modules import, because `FakeDiskSpace` builds on the existing `DiskSpace` from `factory.application.machine`. `make lint` is green. I skipped the type check as the stage says: until `disk_low` joins `RepositoryStopReason` and `TickOutcome.stopped`, it flags the new literal.

   Criterion → test:
   - criterion 1: tests/domain/test_stops.py::test_each_reason_is_accepted_with_its_scope and ::test_each_reason_is_rejected_with_the_other_scope (`SCOPES` gains `("disk_low", "machine")`)
   - criterion 2: tests/domain/test_stop_table.py::test_the_table_holds_the_fifteen_stops_in_order (renamed; `ROWS` gains `disk-low` after `preflight-failed`) and the existing ::test_every_repository_stop_reason_is_the_reason_of_exactly_one_row
   - criterion 3: tests/application/test_tick_disk.py::test_exactly_the_minimum_free_on_both_paths_lets_the_tick_run_on
   - criterion 4: tests/application/test_tick_disk.py::test_a_short_work_directory_stops_the_tick_before_the_fetch
   - criterion 5: tests/application/test_tick_disk.py::test_the_low_disk_stop_reaches_the_health_status_and_the_factory_log
   - criterion 6: tests/application/test_tick_disk.py::test_the_detail_names_the_short_paths_the_work_directory_first (rows state-short, both-short)
   - criterion 7: tests/application/test_tick_disk.py::test_an_unreadable_free_space_stops_the_tick_with_the_error (rows state-unreadable, work-unreadable, work-unreadable-state-short; checks the detail and `asked`)
   - criterion 8: tests/application/test_tick_disk.py::test_a_tick_with_enough_room_clears_the_low_disk_stop
   - criterion 9: tests/application/test_tick_disk.py::test_a_tick_without_a_disk_or_settings_reads_nothing_and_runs_on (rows without-settings, without-disk)
   - criterion 10: the existing tests/test_stop_table.py::test_production_code_names_every_reason_of_a_repository_stop, which runs over `get_args(RepositoryStopReason)` and so picks up `disk_low` once it is added
   - criterion 11 (`make check`) and criterion 12 (docs) are not tester work.

   Files:
   - Created `tests/disk_support.py`: `FakeDiskSpace(DiskSpace)`. You give it a byte count or an `OSError` per path, in the mutable dicts `free` and `used`. A path you did not give raises `KeyError`. Every path asked, for either operation, goes into `asked` in order.
   - Created `tests/application/test_tick_disk.py`. Settings use `min_free_gb=2`, the checkout at `tmp_path/checkout` (so the work directory is `tmp_path`) and the state directory at `tmp_path/state`. The handlers are `{"idle": IdleHandler()}`, and the agents are installed by an autouse fixture.

   Changes to earlier stories' tests, under FEATURE decision 34:
   - `tests/domain/test_stop_table.py`: the new `ROWS` entry and the rename.
   - `tests/domain/test_stops.py`: the new `SCOPES` row.
   - `tests/test_stop_table.py`: the scope line in test_repository_stop_reaches_the_health_status_and_the_factory_log now gives `machine` to `preflight_failed` and `disk_low`.
   - `tests/entry/test_health.py`: `disk_low` joins the reasons of test_every_stop_reason_makes_the_check_fail_until_it_is_cleared.

   One change in that last test went slightly past the letter of the leave. Its scope line also had to give `disk_low` the scope `machine`, the same edit as in `tests/test_stop_table.py`; otherwise the new row would fail on the scope rule.

   Nothing is open.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared[disk_low]
4. coder: Implemented the low-disk stop. Commit "feat(application): stop the tick at disk_low before the fetch". `make check` is green, with coverage at 99.52 %.

   - `src/factory/domain/stops.py`: `RepositoryStopReason` gains `disk_low` after `preflight_failed`. The single `_MACHINE_REASON` became the frozenset `_MACHINE_REASONS` = {`preflight_failed`, `disk_low`}, so the scope validator checks membership in the set.
   - `src/factory/domain/stop_table.py`: added the row `_health("disk-low", ("L64",), "disk_low")` after `preflight-failed`, so the table now has fifteen rows. It uses the existing `_REPOSITORY_TEST` name.
   - `src/factory/application/tick.py`: `Tick.run` calls the new `_check_disk()` first, inside the same `try` as `_fetch`.
     - It does nothing when `boundaries.disk` or `boundaries.settings` is `None`.
     - Otherwise it reads `free_bytes` of `settings.checkout.parent`, then of `settings.state_directory`, into a dict. An `OSError` stops at once with `cannot read the free space of <path>: <error>`, so no later path is read.
     - It then applies `disk_low_detail` from `factory.domain.disk`. A detail raises the stop; no detail calls `clear_stop("disk_low")`.
     - `_stop` gained a keyword `scope: StopScope = "repository"`, so the existing stops are unchanged and the disk check passes `scope="machine"`.
     - Updated the module and `run` docstrings to name the new first step.

   Main design decision: I reused the tick's `_stop`/`_Stopped` path with a scope parameter. I rejected two alternatives: a separate `DiskCheck` service like `Preflight`, which is more wiring for one method, and building the machine `RepositoryStop` inline, which would duplicate `_stop`. Production wiring (`entry/wiring.py`) already passes `settings` and `ShutilDiskSpace()`, so nothing needed to change there.

   Refactor: I re-read my diff and found nothing to change, so there is no refactor commit.

   Noticed, not touched: `make duplicates` reports 2 new findings, both "unused method `used_bytes`", in `application/machine.py` and `adapters/disk_space.py`. That method comes from F0012-S0009 and is meant for F0012-S0016/S0017, so it is not dead code from this ticket. The docs criterion (12) is left to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 2 new, 39 known, 0 gone
5. reviewer: no findings.

   I read the whole diff of `src/` and `tests/`, and the tick, `domain/disk.py` and `StopService.clear_stop` it relies on.

   - Criteria: each of criteria 1 to 10 has a test that checks what it names.
     - The limit is tested on both sides: exactly `min_free_gb * GIGABYTE` runs on (3), and one byte short stops (4, 6).
     - "Before the fetch" (4) is a real test: a commit the human pushed after the clone is not at `origin/main` after the tick.
     - The read order and the early stop on an `OSError` (7) are checked through `FakeDiskSpace.asked`. The row where the state directory is also short shows that the error wins.
     - The test for a missing `disk` or `settings` (9) checks both that nothing is read and that the tick runs on.
     - `make check` was green after the coder, per entry 4.
   - Architecture: `Tick._check_disk` reaches the disk only through the `DiskSpace` interface and decides with `disk_low_detail` from the domain. The scope rule stays in the domain validator, now with a frozenset of machine reasons. `FakeDiskSpace` inherits `DiskSpace`. The layer direction holds.
   - Security: no suppression markers. The `OSError` text in the detail is the operator's own machine fault, which is the stop's purpose.
   - Quality:
     - `_stop` gained a `scope` parameter instead of building a second copy of the stop.
     - Calling `clear_stop` on every tick is safe: it does nothing and writes nothing when there is no `disk_low` stop, so the log gets no extra lines.
     - The new `make duplicates` findings (`used_bytes` unused) come from F0012-S0009 and are kept for S0016/S0017, not added by this diff.
   - Ticket: considered and accepted the tester's scope-line edit in `tests/entry/test_health.py`. It goes slightly past the letter of the leave (entry 3), but it is the consequence the leave needs: without it, the `disk_low` row the leave adds would fail the scope rule. The coder's log names the main decision and the two alternatives they rejected. `Assignment` matches what was built, and criterion 12 still describes what the documenter must write.
