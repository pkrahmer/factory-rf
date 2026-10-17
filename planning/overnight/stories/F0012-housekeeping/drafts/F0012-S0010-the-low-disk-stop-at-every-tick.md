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
- an `OSError` for a path: the same stop with the detail `cannot read the free space of <path>: <error>`, and the tick ends the same way.

Tests: `tests/application/test_tick_disk.py`, with a fake `DiskSpace` written in the test (deriving from the interface) that returns given byte counts per path or raises `OSError`, and the boundaries of `tests/conftest.py` with `disk` and `settings` replaced (`dataclasses.replace`), the settings' `checkout` and `state_directory` under `tmp_path`.

By the human's leave (FEATURE decision 34), and no other change to an earlier story's test: in `tests/domain/test_stop_table.py` the row `disk-low` joins `ROWS` after `preflight-failed`, and `test_the_table_holds_the_fourteen_stops_in_order` becomes `test_the_table_holds_the_fifteen_stops_in_order`; in `tests/test_stop_table.py`, `test_repository_stop_reaches_the_health_status_and_the_factory_log` gives `disk_low` the scope `machine`; in `tests/domain/test_stops.py`, `SCOPES` gains `("disk_low", "machine")`; in `tests/entry/test_health.py`, `disk_low` joins the reasons of `test_every_stop_reason_makes_the_check_fail_until_it_is_cleared`.

## Acceptance criteria

1. A `RepositoryStop` of reason `disk_low` is accepted with scope `machine` and refused with scope `repository`; `preflight_failed` keeps its scope `machine` and every other reason `repository` (the rows of `SCOPES`).
2. `STOP_TABLE` holds fifteen rows, `disk-low` the eighth, after `preflight-failed`, with the values of the Interface; every value of `RepositoryStopReason` is the reason of exactly one row.
3. A tick whose fake disk gives both paths `min_free_gb * GIGABYTE` bytes runs on (its outcome is not `stopped`), and the health status holds no `disk_low` stop; with the work directory one byte short, the tick ends with `stopped == "disk_low"` and the remote's branches and the fake hosting service's pull requests are as before the tick (no fetch, no claim, no post).
4. That stop is in the health status with scope `machine` and the detail `disk_low_detail` gives for the paths read, and the factory log gains one line that ends with `stop machine disk_low: ` and that detail.
5. With the state directory short and the work directory not, the detail names the state directory only; with both short, both, the work directory first. Rows of one parametrized test.
6. A fake disk that raises `OSError("no such device")` for the state directory stops the tick with the detail `cannot read the free space of <state directory>: no such device`.
7. After a stopped tick, a tick with enough room clears the stop: the health status holds no `disk_low` stop and the factory log gains `stop cleared disk_low`.
8. A tick on boundaries without `disk`, or without `settings`, reads no free space and ticks as before. Two rows of one parametrized test.
9. The string `disk_low` occurs as a string constant in a module of `src/factory/application` (the existing test over every reason).
10. `make check` stays green.
11. docs: the operator guide's table *The stops* gets the row `` `disk-low` `` (health status and factory log; what the operator does: free space on the host or raise the Docker Desktop disk limit, then nothing, the next tick clears it), and its settings row for `FACTORY_MIN_FREE_GB` says what it guards; the project guide's section *The tick* names the first step and its order before the fetch, and the stop table's description of the rows gains `disk-low`; the decision log records the stop: why before the fetch, why one check per tick and not a preflight item, and why an unreadable free space stops too. `python -m factory.entry.check_documents` prints `documents ok`.

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
