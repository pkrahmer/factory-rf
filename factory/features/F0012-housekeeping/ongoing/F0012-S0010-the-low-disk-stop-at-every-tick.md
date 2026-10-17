---
stage: tests
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
