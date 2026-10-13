# Repository and machine stops: health status and time-stamped lines

## Assignment (as of log entry 1)

Build the destination of every stop of the repository or the machine (R27): a health status file that the container's health check will read, and a factory log whose every line carries a UTC time stamp (ST3.4). `StopService` raises such a stop (the health status plus one stamped line) and clears it when its fault is gone; a stop of the repository or the machine never goes to a pull request. The story also creates what the stop service needs and what later features share: the `Clock`, `FactoryLog` and `HealthStatusStore` protocols with their first implementations (`SystemClock`, `ManualClock`, `TimestampedFactoryLog`, `JsonHealthStatusFile`) and `Boundaries`, the holder of the interfaces that wiring hands to services. Covers ST3.4 and R27 (repository and machine side); keeps kept thing 12 (a stop is reported, never carried past). The health check command, the container and the entrypoint's own stops are F0010 (ST3.3), and wiring the concrete adapters is `factory.entry.wiring`'s, grown by F0010; neither is built here.

## Interface

`src/factory/domain/stops.py`

```python
RepositoryStopReason = Literal[
    "fetch_failed", "checkout_restore_failed", "pipeline_definition_invalid",
    "agent_definition_invalid", "v1_work_item_found", "repository_unavailable",
    "main_branch_failing", "preflight_failed",
]

class RepositoryStop(BaseModel):              # goes to the health status and a time-stamped line
    scope: Literal["repository", "machine"]
    reason: RepositoryStopReason
    detail: str                               # names the fault: the key, stage, file or both versions
    at: AwareDatetime

class HealthStatus(BaseModel):                # the file the health check reads
    stops: list[RepositoryStop] = []
    @property
    def healthy(self) -> bool: ...
```

`src/factory/application/machine.py`

```python
class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...                    # aware, UTC

class FactoryLog(ABC):
    @abstractmethod
    def line(self, text: str) -> None: ...            # time-stamped, to standard output and the factory log file

class HealthStatusStore(ABC):
    @abstractmethod
    def read(self) -> HealthStatus: ...               # a missing file is HealthStatus()
    @abstractmethod
    def write(self, status: HealthStatus) -> None: ...
```

`src/factory/application/boundaries.py`

```python
@dataclass(frozen=True)
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
    def raise_stop(self, stop: RepositoryStop) -> None: ...                  # health status and one line; OSError
    def clear_stop(self, reason: RepositoryStopReason) -> None: ...          # OSError
```

`src/factory/adapters/clock.py`

```python
class SystemClock:
    def now(self) -> datetime: ...                    # aware, offset zero

class ManualClock:                                    # for tests
    def __init__(self, start: datetime) -> None: ...
    def now(self) -> datetime: ...                    # start in UTC, plus every advance
    def advance(self, by: timedelta) -> None: ...
```

`src/factory/adapters/factory_log.py`

```python
class TimestampedFactoryLog:
    def __init__(self, path: Path, clock: Clock) -> None: ...
    def line(self, text: str) -> None: ...            # OSError, only on the write
```

`src/factory/adapters/health_file.py`

```python
class JsonHealthStatusFile:
    def __init__(self, path: Path) -> None: ...       # the wiring puts it at <state directory>/health.json
    def read(self) -> HealthStatus: ...
    def write(self, status: HealthStatus) -> None: ...   # OSError, only on the write
```

Rules:

- `RepositoryStop.detail` must not be blank (empty or whitespace only); `HealthStatus.stops` holds at most one stop per reason; `scope` is `"machine"` exactly when `reason` is `"preflight_failed"`, and `"repository"` for every other reason. A violation is a pydantic `ValidationError`.
- `HealthStatus.healthy` is true exactly when `stops` is empty.
- `TimestampedFactoryLog.line(text)` splits `text` at its line ends and, for each line, writes `<stamp> <line>` and a newline to standard output and appends the same line to the file at `path`. The stamp has the form `YYYY-MM-DDTHH:MM:SSZ`: the time of `clock.now()` converted to UTC, whole seconds only (a fraction is dropped, not rounded). The clock is read once per call, so all lines of one call carry one stamp.
- `TimestampedFactoryLog` and `JsonHealthStatusFile` create the missing parent directories of their path before they write. An `OSError` of a write is not caught.
- `JsonHealthStatusFile.write` stores the status as JSON (`status.model_dump_json()`); `read` returns it back equal; a file that does not exist reads as `HealthStatus()`.
- `StopService.raise_stop(stop)` does two things and tries both: it writes through `boundaries.log` the line `stop <scope> <reason>: <detail>`, and it writes through `boundaries.health` the current health status with the stop in it. A stop whose reason is already in the status replaces that stop where it stood; a new reason is appended. If one of the two writes raises `OSError`, the other is still done, and the first `OSError` is raised afterwards. It posts nothing and opens no pull request.
- `StopService.clear_stop(reason)` writes the health status without the stop of that reason, then the line `stop cleared <reason>`. When the status holds no stop of that reason it does nothing: no write, no line.
- `Boundaries` is built with keyword arguments only; later stories add their fields to it (`pipeline_reader`, `agent_definitions`, `run_record`).

Tests: `tests/domain/test_stops.py`, `tests/adapters/test_clock.py`, `tests/adapters/test_factory_log.py`, `tests/adapters/test_health_file.py`, `tests/application/test_stops.py`. The fixtures `kill_points`, `checkout`, `hosting` and `agent_runtime` are the ones that earlier stories put in `tests/conftest.py`. This story adds there, where missing, the fixtures `clock` (a `ManualClock` started at `datetime(2026, 10, 12, 12, 0, tzinfo=UTC)`) and `boundaries`: a `Boundaries` built from `checkout`, `hosting` and `agent_runtime`, a `MakeProjectCommands` on the checkout, the work item and cost readers and writers, `clock`, a `TimestampedFactoryLog` at `<tmp_path>/state/factory.log`, a `JsonHealthStatusFile` at `<tmp_path>/state/health.json`, and `checkout` set to the directory of the `checkout` fixture's clone. The standard output of the log is read with `capsys`.

## Acceptance criteria

1. A `RepositoryStop` whose `detail` is empty, or only whitespace, is rejected with `ValidationError`; a `detail` of `x` is accepted.
2. For each of the eight reasons, a `RepositoryStop` is accepted with the matching scope: `machine` for `preflight_failed`, `repository` for the other seven.
3. For each of the eight reasons, a `RepositoryStop` with the other scope is rejected with `ValidationError`.
4. `HealthStatus().healthy` is true; a `HealthStatus` holding one stop is not healthy.
5. A `HealthStatus` holding two stops of the same reason is rejected with `ValidationError`; two stops of different reasons are accepted.
6. `ManualClock(start).now()` equals `start` converted to UTC until `advance`, and after `advance(timedelta(seconds=5))` it is 5 seconds later; `SystemClock().now()` is aware and its `utcoffset()` is zero.
7. `TimestampedFactoryLog.line("hello")` with a clock whose time has a fractional second (for example `.987654`) writes to standard output exactly `<stamp> hello` and a newline, where the stamp has the form `YYYY-MM-DDTHH:MM:SSZ`, in UTC, with the clock's whole seconds (the fraction is dropped, not rounded up).
8. `line` also appends the same line to the file at `path`: after two calls, with the clock advanced by 5 seconds between them, the file holds the two lines in order, the second stamped 5 seconds after the first, and what the file held before the first call is kept.
9. `line("a\nb")` writes two lines, `<stamp> a` and `<stamp> b`, both to standard output and to the file, with the same stamp.
10. When the parent directory of its path does not exist, `TimestampedFactoryLog.line` and `JsonHealthStatusFile.write` create it and write (one test, both classes).
11. `JsonHealthStatusFile.write(status)` then `read()` returns a status equal to it, with its stops in order.
12. `JsonHealthStatusFile.read()` on a path that does not exist returns `HealthStatus()`.
13. `StopService.raise_stop` writes the health status with the stop in it: afterwards `boundaries.health.read().stops` equals `[stop]` and `healthy` is false.
14. `raise_stop` writes exactly one line, `<stamp> stop <scope> <reason>: <detail>`, to standard output and to the factory log file; the stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and is the clock's time.
15. `raise_stop` with a reason already in the status replaces that stop where it stood: after stops A, B and a second A with another `detail`, the status holds `[A', B]` in that order; a new reason is appended.
16. When the health status cannot be written (its path lies below a regular file), `raise_stop` still writes the line to standard output and the log file, and then raises `OSError`.
17. When the factory log file cannot be written (its path lies below a regular file), `raise_stop` still writes the stop into the health status, and then raises `OSError`.
18. `raise_stop` opens no pull request and posts nothing: afterwards `hosting.pull_requests()` is empty.
19. `clear_stop(reason)` with a stop of that reason in the status removes it, leaves the other stops, and writes the line `<stamp> stop cleared <reason>`.
20. `clear_stop(reason)` with no stop of that reason does nothing: it writes no line, and a health status file that did not exist still does not exist.
21. `make check` stays green.
22. docs: `docs/operator-guide.md` explains the health status file (`health.json` in the state directory, one stop per reason, replaced on a repeat, removed when the fault is gone), the time-stamped line format and the two lines `stop <scope> <reason>: <detail>` and `stop cleared <reason>`; `docs/decisions.md` records that both destinations are tried and one failing destination never loses the stop.

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
