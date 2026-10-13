---
stage: accept
pr: 41
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Raising and clearing the stops of the repository and the machine

## Assignment (as of log entry 1)

Build the destination of every stop of the repository or the machine (R27): `StopService` raises such a stop (the health status plus one stamped line, both tried) and clears it when its fault is gone; a stop of the repository or the machine never goes to a pull request. The story also creates `Boundaries`, the holder of the interfaces that wiring hands to services, and the `boundaries` fixture of the tests. It uses S0001's `Clock`, `FactoryLog` and `HealthStatusStore` and their implementations. Covers ST3.4 and R27 (repository and machine side); keeps kept thing 12 (a stop is reported, never carried past). Wiring the concrete adapters is `factory.entry.wiring`'s, which grows feature by feature and whose `build_boundaries` F0010-S0001 completes (questionnaire 1, Q20); F0003 registers no handler and builds no wiring. The health check command, the container and the entrypoint's own stops are F0010 (ST3.3).

## Interface

`src/factory/application/boundaries.py`

```python
@dataclass(frozen=True, kw_only=True)
class Boundaries:                                     # not a DTO: the interfaces wiring hands to services
    git: Git
    hosting: HostingService
    agent_runtime: AgentRuntime
    project_commands: ProjectCommands
    work_item_reader: WorkItemReader
    work_item_writer: WorkItemWriter
    cost_reader: CostRecordReader
    cost_writer: CostRecordWriter
    clock: Clock
    log: FactoryLog
    health: HealthStatusStore
    checkout: Path                                    # the checkout root
```

`src/factory/application/stops.py`

```python
class StopService:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def raise_stop(self, stop: RepositoryStop) -> None: ...                  # the line and the health status; OSError
    def clear_stop(self, reason: RepositoryStopReason) -> None: ...          # OSError
```

Rules:

- `Boundaries` is built with keyword arguments only (`kw_only=True`) and is frozen; later stories add their fields to it (`pipeline_reader` in S0004, `agent_definitions` in S0005).
- `StopService.raise_stop(stop)` does two things and tries both: first it writes through `boundaries.log` the line `stop <scope> <reason>: <detail>`, then it writes through `boundaries.health` the current health status with the stop in it. A stop whose reason is already in the status replaces that stop where it stood; a new reason is appended. If one of the two writes raises `OSError`, the other is still done, and the first `OSError` is raised afterwards (the log's when both fail). It posts nothing and opens no pull request.
- `StopService.clear_stop(reason)` first writes the health status without the stop of that reason, then the line `stop cleared <reason>`. When the status holds no stop of that reason it does nothing: no write, no line. When the health write raises `OSError`, nothing else is done and the error is raised (the stop is still in the status, so no line says it is cleared); when the line then raises `OSError`, the stop is already removed and the error is raised.

Tests: `tests/application/test_boundaries.py`, `tests/application/test_stops.py`. The fixtures `kill_points`, `checkout`, `hosting`, `agent_runtime` and `clock` are the ones that earlier stories put in `tests/conftest.py`. This story adds there the fixture `boundaries`: a `Boundaries` built from `checkout`, `hosting` and `agent_runtime`, `MakeProjectCommands(tmp_path / CHECKOUT, kill_points)`, `FrontmatterWorkItemReader()`, `FrontmatterWorkItemWriter()`, `JsonLinesCostRecordReader()`, `JsonLinesCostRecordWriter()`, `clock`, a `TimestampedFactoryLog` at `<tmp_path>/state/factory.log`, a `JsonHealthStatusFile` at `<tmp_path>/state/health.json`, and `checkout=tmp_path / CHECKOUT`, the clone the `checkout` fixture works in. A test that needs other parts builds them with `dataclasses.replace(boundaries, ...)` and never calls `Boundaries(...)` itself, except the one that tests the keyword-only rule; so a later story that adds a required field changes only this fixture. The test of the keyword-only rule calls `Boundaries` through a variable typed `Callable[..., Boundaries]` (`build: Callable[..., Boundaries] = Boundaries`), because a direct positional call is a `mypy --strict` error (`call-arg`); the test of the frozen rule assigns with `setattr(boundaries, field, value)`, the field's name in a variable, because a direct assignment is a `mypy --strict` error (`misc`). A destination that cannot be written is a `JsonHealthStatusFile` or `TimestampedFactoryLog` whose path lies below a regular file. The standard output of the log is read with `capsys`.

## Acceptance criteria

1. `Boundaries` called with positional arguments raises `TypeError`.
2. `Boundaries` is frozen: assigning to one of its fields raises `dataclasses.FrozenInstanceError`.
3. `StopService.raise_stop` writes the health status with the stop in it: afterwards `boundaries.health.read().stops` equals `[stop]` and `healthy` is false.
4. `raise_stop` writes exactly one line, `<stamp> stop <scope> <reason>: <detail>`, to standard output and to the factory log file; the stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and is the clock's time.
5. `raise_stop` with a reason already in the status replaces that stop where it stood: after stops A, B and a second A with another `detail`, the status holds `[A', B]` in that order; a new reason is appended.
6. When the health status cannot be written, `raise_stop` still writes the line to standard output and the log file, and then raises `OSError`.
7. When the factory log file cannot be written, `raise_stop` still writes the stop into the health status, and then raises `OSError`; the line has reached standard output.
8. When neither can be written, `raise_stop` raises the `OSError` of the log: its `filename` is the log's regular file or a path below it, not the health file's or one below that.
9. `raise_stop` opens no pull request and posts nothing: afterwards `hosting.pull_requests()` is empty.
10. `clear_stop(reason)` with a stop of that reason in the status removes it, leaves the other stops, and writes the line `<stamp> stop cleared <reason>`.
11. `clear_stop(reason)` with no stop of that reason does nothing: it writes no line, and a health status file that did not exist still does not exist.
12. When the health status cannot be written, `clear_stop` of a reason that is in the status raises `OSError` and writes no line.
13. When the factory log cannot be written, `clear_stop` of a reason that is in the status raises `OSError`, and the stop is removed from the health status.
14. `make check` stays green.
15. docs: `docs/operator-guide.md` explains the two lines `stop <scope> <reason>: <detail>` and `stop cleared <reason>`, that a stop is replaced and not repeated in the health status, and that it is removed when the fault is gone; `docs/project-guide.md` explains `Boundaries` (keyword-only, frozen, the interfaces it holds, the `boundaries` fixture and `dataclasses.replace` in tests); `docs/decisions.md` records that both destinations of a stop are tried and one failing destination never loses the stop.

## Demo

```bash
uv run python -c "
import re
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.health_file import JsonHealthStatusFile
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.stops import RepositoryStop
state = Path(tempfile.mkdtemp()) / 'state'
clock = ManualClock(datetime(2026, 10, 12, 12, 0, 7, 987654, tzinfo=UTC))
health = JsonHealthStatusFile(state / 'health.json')
log = TimestampedFactoryLog(state / 'factory.log', clock)
parts = dict.fromkeys(['git', 'hosting', 'agent_runtime', 'project_commands', 'work_item_reader', 'work_item_writer', 'cost_reader', 'cost_writer'])
service = StopService(Boundaries(**parts, clock=clock, log=log, health=health, checkout=state))
service.raise_stop(RepositoryStop(scope='repository', reason='fetch_failed', detail='origin unreachable', at=clock.now()))
print([stop.reason for stop in health.read().stops], health.read().healthy)
clock.advance(timedelta(seconds=5))
service.clear_stop('fetch_failed')
print([stop.reason for stop in health.read().stops], health.read().healthy)
lines = (state / 'factory.log').read_text().splitlines()
pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z '
print(len(lines), all(re.match(pattern, line) for line in lines))
print([re.sub(pattern, '', line) for line in lines])
"
```
Expect: six lines of output. Line 1 is `<stamp> stop repository fetch_failed: origin unreachable`, where the stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and starts with the date `2026-10-12T`; line 2 is `['fetch_failed'] False`; line 3 is `<stamp> stop cleared fetch_failed` with a stamp 5 seconds after the first; line 4 is `[] True`; line 5 is `2 True`; line 6 is `['stop repository fetch_failed: origin unreachable', 'stop cleared fetch_failed']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `Boundaries` (frozen, kw_only, twelve named fields) and `StopService` (`raise_stop`, `clear_stop`) are in concrete modules, `application/boundaries.py` and `application/stops.py`. They have signatures, `OSError` contracts and the fixture recipe, including the mypy-safe ways to test keyword-only and frozen.
   - Criteria: every criterion is testable by one test function. Each Interface behaviour has one: the replace-in-place and append order (5), the line format and stamp (4, 10), the silent no-op (11), and the write order and error propagation. Each failing side has a criterion: health unwritable (6, 12), log unwritable (7, 13), both unwritable with the log's `OSError` winning (8), and positional and mutation attempts (1, 2).
   - Demo: runnable. It calls only S0001 classes and the new ones. The `Expect:` line gives six output lines that I checked against the script's prints, and the stamps are checkable with a regex and a 5 s offset.
   - Architecture: `Boundaries` and `StopService` sit in `factory.application` and import only interfaces and domain types. Wiring stays in `factory.entry`, and the story builds none.
   - Scope: this is S0002 of F0003, the repository and machine side of stops. Work item stops, the health check command and the pipeline definition are other stories or out of scope, and none of them is touched.
3. tester: I wrote red tests for criteria 1–13. Each criterion maps to one test function, and criterion 11 has two.
   - criterion 1: tests/application/test_boundaries.py::test_boundaries_refuse_positional_arguments (calls `Boundaries` through `Callable[..., Boundaries]` with the fixture's field values in order)
   - criterion 2: tests/application/test_boundaries.py::test_boundaries_refuse_assignment_to_a_field (`setattr` on `checkout`)
   - criterion 3: tests/application/test_stops.py::test_a_raised_stop_is_in_the_health_status
   - criterion 4: tests/application/test_stops.py::test_a_raised_stop_writes_one_stamped_line_to_output_and_log_file (the clock is advanced by 7.987654 s, so the expected stamp is `2026-10-12T12:00:07Z`)
   - criterion 5: tests/application/test_stops.py::test_a_stop_of_a_known_reason_replaces_it_in_place_and_a_new_reason_is_appended (A, B, A' gives `[A', B]`, then a new reason C gives `[A', B, C]`)
   - criterion 6: tests/application/test_stops.py::test_a_stop_reaches_the_log_when_the_health_status_cannot_be_written
   - criterion 7: tests/application/test_stops.py::test_a_stop_reaches_the_health_status_when_the_log_file_cannot_be_written
   - criterion 8: tests/application/test_stops.py::test_the_log_error_is_raised_when_neither_destination_can_be_written (the `filename` is the log's blocking file or a path below it, and is neither the health file's blocker nor a path below that)
   - criterion 9: tests/application/test_stops.py::test_a_raised_stop_opens_no_pull_request
   - criterion 10: tests/application/test_stops.py::test_clearing_a_stop_removes_only_it_and_writes_the_cleared_line
   - criterion 11: tests/application/test_stops.py::test_clearing_a_reason_that_is_not_stopped_does_nothing (no line, and neither the log file nor the health file exists afterwards) and ::test_clearing_a_reason_that_is_not_stopped_keeps_the_other_stops_silently (the Interface rule "no write, no line" when other stops are present)
   - criterion 12: tests/application/test_stops.py::test_clearing_raises_and_writes_no_line_when_the_health_status_cannot_be_written
   - criterion 13: tests/application/test_stops.py::test_clearing_removes_the_stop_and_raises_when_the_log_file_cannot_be_written

   Why criterion 12 uses a fake: the Interface's recipe for an unwritable destination is a `JsonHealthStatusFile` below a regular file, but such a file reads as `HealthStatus()`, so there would be no stop to clear. The test therefore uses `_UnwritableHealth`, a small `HealthStatusStore` defined in the test module. It returns a status that holds the stop and raises `OSError` on every write. The other unwritable destinations follow the Interface's recipe.

   Files:
   - created: tests/application/test_boundaries.py and tests/application/test_stops.py
   - changed: tests/conftest.py, which gains the `boundaries` fixture built exactly as the Interface says. Its parameters after `checkout` are keyword-only to satisfy ruff's PLR0917.

   What fails, and why: conftest imports `factory.application.boundaries` at the top, so `make test` stops while loading conftest with `ModuleNotFoundError: No module named 'factory.application.boundaries'`. The whole suite is blocked until the coder creates that module. `factory.application.stops` is missing as well.

   Checks: `make lint` is green. I skipped the type check as this stage says.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.application.boundaries'
4. coder: I implemented `Boundaries` and `StopService`, and `make check` is green. The tester's tests are unchanged.
   - `src/factory/application/boundaries.py`: `Boundaries` is a `@dataclass(frozen=True, kw_only=True)` with the twelve fields the Interface lists. It imports only application interfaces and `Path`.
   - `src/factory/application/stops.py`:
     - `StopService.raise_stop` writes the line `stop <scope> <reason>: <detail>` through `boundaries.log`. It then reads the health status and writes it back with the stop: a stop with a known reason is replaced where it stood, and a new reason is appended. Each write sits in its own `try`, and the first `OSError` is raised once both have been tried. The log is tried first, so the log's error wins when both fail.
     - `clear_stop` does nothing when the status holds no stop of that reason. Otherwise it writes the status without that stop first and then the line `stop cleared <reason>`. An `OSError` from the health write therefore stops it before the line.
   - Commits:
     - `61b20ec` feat(application): boundaries and the stop service
     - `d5bfeaa` refactor(application): `_with_stop` now decides between replacing and appending by checking the reason. Before, it checked whether the stop was in the list.

   Design: the replace-or-append rule lives in two private helpers in `application/stops.py`. I rejected adding public methods to `HealthStatus` in `factory.domain.stops`. That would put a domain API in this story's diff that only this service uses. If later stories need the rule elsewhere, it can move to the domain then.

   Noticed, not touched: `HealthStatusStore.read()` is documented as never raising. `raise_stop` still reads inside the health `try`, so a store that breaks this contract with an `OSError` cannot lose the line. `clear_stop` lets a read error propagate before anything is written, which matches "nothing else is done".

   Open: none. The docs criterion (15) is the documenter's.

   `make check`: check: green
5. reviewer: no findings.
   - Acceptance criteria: I read every test against its criterion. Criteria 1–13 each have a test that checks what the criterion says. Criterion 11 has two tests, one with no status file and one with other stops present. The failing side of each `OSError` rule has a test: health unwritable (6, 12), log unwritable (7, 13), and both unwritable with the log's error winning (8). Criterion 12 uses `_UnwritableHealth`, a `HealthStatusStore` defined in the test module. I accept it because the Interface's recipe (a file below a regular file) reads as `HealthStatus()`, so there would be no stop to clear. It inherits the interface and does not stand in for the code under test. The Interface states no numeric limit. The coder's entry records `make check` green.
   - Architecture: `src/factory/application/boundaries.py` imports only application interfaces and `Path`. `src/factory/application/stops.py` imports only `Boundaries` and `factory.domain.stops`. The story builds no wiring, and no tool is called.
   - Security: no secrets, no shell or SQL built from strings, no suppression markers. The diff adds no external input.
   - Quality: `raise_stop` tries the log first and then the health status, each in its own `try`, and raises `errors[0]`, so the log's error wins as the rule says. `clear_stop` returns early when the reason is absent, writes the health status before the line, and lets `OSError` propagate in that order. The private helpers `_with_stop` and `_without_stop` replace a stop in place or append it, and `HealthStatus` keeps its one-stop-per-reason validator. The module, the public classes and the public methods carry docstrings, and the comments say why.
   - Ticket hygiene: the coder's entry gives the main decision and what was rejected (the replace-or-append rule stays private, not a public `HealthStatus` API). `Assignment` matches what was built. Criterion 15 still describes what the documenter has to write.
6. documenter: I wrote the three documents criterion 15 asks for, and `make check` is green.
   - `docs/operator-guide.md`:
     - New section "Stops of the repository or the machine" with the two lines `stop <scope> <reason>: <detail>` and `stop cleared <reason>`, each with an example.
     - It says a stop is replaced in place and not repeated, that a new reason is appended, and that a stop is removed when the fault is gone.
     - It says what happens when one destination cannot be written.
     - I replaced the intro of the log/health section, which said `StopService` was still to come.
   - `docs/project-guide.md`:
     - The "Stops, the clock and the factory log" section now describes `StopService`, with the write order and the `OSError` rules. The "comes with F0003-S0002" sentence is gone.
     - New "Boundaries" subsection: keyword-only, frozen, the twelve fields, the `boundaries` fixture, `dataclasses.replace`, the mypy-safe tests, and the note that wiring is not built yet.
   - `docs/decisions.md`: a new entry records that both destinations of a stop are tried and one failing never loses it. It also records why `clear_stop` writes the health status first, and the alternatives I rejected.
   - I cross-read the README (it names no stop or boundary) and the rest of the operator guide and project guide against the diff. I found them current.
   - I found nothing stale to leave alone, and no findings for the coder. The code matches the Interface.
   - I did not run the demo script. The log line examples in the operator guide use the demo's format.

   `make check`: check: green
7. demo: the one command under `## Demo` ran from the repository root with exit code 0. Its output matches its `Expect:` line, and I found no findings.

   Command 1 (the `uv run python -c` script that raises and then clears `fetch_failed`):
   ```
   2026-10-12T12:00:07Z stop repository fetch_failed: origin unreachable
   ['fetch_failed'] False
   2026-10-12T12:00:12Z stop cleared fetch_failed
   [] True
   2 True
   ['stop repository fetch_failed: origin unreachable', 'stop cleared fetch_failed']
   ```
   It met its `Expect:` line. There are six lines:
   - Line 1 is the stop line. Its stamp is `YYYY-MM-DDTHH:MM:SSZ`, starts with `2026-10-12T`, and is the clock's time cut to whole seconds.
   - Line 2 is `['fetch_failed'] False`.
   - Line 3 is the cleared line, with a stamp 5 seconds after the first (12:00:12).
   - Line 4 is `[] True`.
   - Line 5 is `2 True`.
   - Line 6 lists the two lines with their stamps removed.

   Criteria check: the demo agrees with criteria 3 (the stop is in the status and `healthy` is false), 4 (one stamped line on standard output and in the log file, stamped with the clock's time), 10 (clear removes the stop and writes `stop cleared <reason>`) and 1/2 (built with keyword arguments only). It contradicts no criterion. The demo does not exercise the error paths (6–8, 12, 13), the replace-in-place rule (5) or the no-op clear (11); tests cover them, according to the tester's and reviewer's entries. I did not run `make check`, which the factory runs itself after this stage.
