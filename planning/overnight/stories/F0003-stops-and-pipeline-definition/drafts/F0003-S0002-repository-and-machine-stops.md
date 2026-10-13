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

Tests: `tests/application/test_boundaries.py`, `tests/application/test_stops.py`. The fixtures `kill_points`, `checkout`, `hosting`, `agent_runtime` and `clock` are the ones that earlier stories put in `tests/conftest.py`. This story adds there the fixture `boundaries`: a `Boundaries` built from `checkout`, `hosting` and `agent_runtime`, `MakeProjectCommands(tmp_path / CHECKOUT, kill_points)`, `FrontmatterWorkItemReader()`, `FrontmatterWorkItemWriter()`, `JsonLinesCostRecordReader()`, `JsonLinesCostRecordWriter()`, `clock`, a `TimestampedFactoryLog` at `<tmp_path>/state/factory.log`, a `JsonHealthStatusFile` at `<tmp_path>/state/health.json`, and `checkout=tmp_path / CHECKOUT`, the clone the `checkout` fixture works in. A test that needs other parts builds them with `dataclasses.replace(boundaries, ...)` and never calls `Boundaries(...)` itself, except the one that tests the keyword-only rule; so a later story that adds a required field changes only this fixture. A destination that cannot be written is a `JsonHealthStatusFile` or `TimestampedFactoryLog` whose path lies below a regular file. The standard output of the log is read with `capsys`.

## Acceptance criteria

1. `Boundaries` called with positional arguments raises `TypeError`.
2. `Boundaries` is frozen: assigning to one of its fields raises `dataclasses.FrozenInstanceError`.
3. `StopService.raise_stop` writes the health status with the stop in it: afterwards `boundaries.health.read().stops` equals `[stop]` and `healthy` is false.
4. `raise_stop` writes exactly one line, `<stamp> stop <scope> <reason>: <detail>`, to standard output and to the factory log file; the stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and is the clock's time.
5. `raise_stop` with a reason already in the status replaces that stop where it stood: after stops A, B and a second A with another `detail`, the status holds `[A', B]` in that order; a new reason is appended.
6. When the health status cannot be written, `raise_stop` still writes the line to standard output and the log file, and then raises `OSError`.
7. When the factory log file cannot be written, `raise_stop` still writes the stop into the health status, and then raises `OSError`; the line has reached standard output.
8. When neither can be written, `raise_stop` raises the `OSError` of the log (its `filename` lies below the log's regular file, not the health file's).
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
