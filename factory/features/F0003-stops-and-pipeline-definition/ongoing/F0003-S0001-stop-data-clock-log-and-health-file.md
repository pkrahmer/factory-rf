---
stage: tests
pr: 40
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Stop data, the clock, the factory log and the health file

## Assignment (as of log entry 1)

Build the data and the three machine stores behind every stop of the repository or the machine (R27): `RepositoryStop` and `HealthStatus`, the health status file that the container's health check will read, and a factory log whose every line carries a UTC time stamp (ST3.4). The story creates the `Clock`, `FactoryLog` and `HealthStatusStore` abstract base classes and their first implementations (`SystemClock`, `ManualClock`, `TimestampedFactoryLog`, `JsonHealthStatusFile`); each implementation inherits its interface. The service that raises and clears a stop with them (`StopService`) and `Boundaries`, the holder of the interfaces that wiring hands to services, are S0002. Covers ST3.4 and the data side of R27 (repository and machine); keeps kept thing 12 (a stop is reported, never carried past). The health check command, the container and the entrypoint's own stops are F0010 (ST3.3).

## Interface

`src/factory/domain/stops.py`

```python
RepositoryStopReason = Literal[
    "fetch_failed", "checkout_restore_failed", "pipeline_definition_invalid",
    "agent_definition_invalid", "repository_unavailable",
    "main_branch_failing", "preflight_failed",
]

class RepositoryStop(BaseModel):              # goes to the health status and a time-stamped line
    model_config = ConfigDict(frozen=True, extra="forbid")
    scope: Literal["repository", "machine"]
    reason: RepositoryStopReason
    detail: str                               # names the fault: the key, stage, file or both versions
    at: AwareDatetime                         # converted to UTC by a validator

class HealthStatus(BaseModel):                # the file the health check reads
    model_config = ConfigDict(frozen=True, extra="forbid")
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
    def read(self) -> HealthStatus: ...               # a missing, unreadable or invalid file is HealthStatus()
    @abstractmethod
    def write(self, status: HealthStatus) -> None: ...   # OSError
```

`src/factory/adapters/clock.py`

```python
class SystemClock(Clock):
    def now(self) -> datetime: ...                    # aware, offset zero

class ManualClock(Clock):                             # for tests
    def __init__(self, start: datetime) -> None: ...  # ValueError for a naive start
    def now(self) -> datetime: ...                    # start in UTC, plus every advance
    def advance(self, by: timedelta) -> None: ...
```

`src/factory/adapters/factory_log.py`

```python
class TimestampedFactoryLog(FactoryLog):
    def __init__(self, path: Path, clock: Clock) -> None: ...
    def line(self, text: str) -> None: ...            # OSError, only on the write
```

`src/factory/adapters/health_file.py`

```python
class JsonHealthStatusFile(HealthStatusStore):
    def __init__(self, path: Path) -> None: ...       # the wiring puts it at <state directory>/health.json
    def read(self) -> HealthStatus: ...
    def write(self, status: HealthStatus) -> None: ...   # OSError, only on the write
```

Rules:

- `RepositoryStop.detail` must not be blank (empty or whitespace only); `scope` is `"machine"` exactly when `reason` is `"preflight_failed"`, and `"repository"` for every other reason; `at` must be timezone-aware and is stored in UTC; `HealthStatus.stops` holds at most one stop per reason. Both models are frozen and refuse unknown fields. A violation is a pydantic `ValidationError`.
- `HealthStatus.healthy` is true exactly when `stops` is empty.
- `ManualClock(start)` refuses a naive `start` with `ValueError`; `now()` is `start` converted to UTC plus every `advance`. `SystemClock.now()` is `datetime.now(UTC)`.
- `TimestampedFactoryLog.line(text)` splits `text` with `str.splitlines()` (an empty `text` counts as one empty line, so `line("")` writes `<stamp> ` once, and `line("a\n")` writes one line) and, for each line, writes `<stamp> <line>` and a newline to standard output, then appends the same line to the file at `path` (UTF-8, line end `\n`). The stamp has the form `YYYY-MM-DDTHH:MM:SSZ`: the time of `clock.now()` converted to UTC, whole seconds only (a fraction is dropped, not rounded). The clock is read once per call, so all lines of one call carry one stamp.
- `TimestampedFactoryLog` and `JsonHealthStatusFile` create the missing parent directories of their path before they write. An `OSError` of a write is not caught; the line has reached standard output before the file is written.
- `JsonHealthStatusFile.write` stores `status.model_dump_json()` by writing a temporary file in the same directory and replacing the target with `os.replace`, so a reader never sees half a file and no temporary file stays behind. `read` returns the stored status back equal. A file that does not exist, cannot be read (an `OSError`, such as a directory at the path, or bytes that are not UTF-8), is not JSON or is not a valid `HealthStatus` reads as `HealthStatus()`, and the next `write` replaces it: a hand edit or a lost file never stops the factory from raising its stop again.
- Each abstract method's body is its docstring alone, and every implementation inherits its interface.

Tests: `tests/domain/test_stops.py`, `tests/application/test_machine.py`, `tests/adapters/test_clock.py`, `tests/adapters/test_factory_log.py`, `tests/adapters/test_health_file.py`. This story adds to `tests/conftest.py` the fixture `clock`, a `ManualClock` started at `datetime(2026, 10, 12, 12, 0, tzinfo=UTC)`. The refusal of an unknown field is tested through a variable typed `type[BaseModel]`, as `CLAUDE.md` asks. A test of a non-UTC clock uses a small test class that inherits `Clock`. The standard output of the log is read with `capsys`. The refusal of an assignment to a frozen model's field assigns with `setattr(instance, field, value)`, the field's name in a variable, because a direct assignment is a `mypy --strict` error under the pydantic plugin (`misc`, the property is read-only) and `setattr` with a constant name is ruff's `B010`. The test that the three interfaces cannot be instantiated (criterion 24) calls each through a variable typed `type[object]`, as `tests/application/test_interfaces.py` does, because a direct call such as `Clock()` is a `mypy --strict` error (`abstract`).

## Acceptance criteria

1. A `RepositoryStop` whose `detail` is empty, or only whitespace, is rejected with `ValidationError`; a `detail` of `x` is accepted.
2. For each of the seven reasons, a `RepositoryStop` is accepted with the matching scope: `machine` for `preflight_failed`, `repository` for the other six.
3. For each of the seven reasons, a `RepositoryStop` with the other scope is rejected with `ValidationError`.
4. A `RepositoryStop` whose `reason` is not one of the seven (`other`, and the empty text) is rejected with `ValidationError`.
5. A `RepositoryStop` with a naive `at` is rejected with `ValidationError`.
6. A `RepositoryStop` with an `at` that has an offset of two hours east of UTC is accepted, and its `at` is the same instant with `utcoffset()` equal to zero.
7. A `RepositoryStop` and a `HealthStatus` each reject an unknown field with `ValidationError` (one test, both models).
8. A field of a `RepositoryStop` and the `stops` of a `HealthStatus` cannot be assigned: the assignment raises `ValidationError` (one test, both models).
9. `HealthStatus().healthy` is true; a `HealthStatus` holding one stop is not healthy.
10. A `HealthStatus` holding two stops of the same reason is rejected with `ValidationError`; two stops of different reasons are accepted.
11. `ManualClock(start).now()`, for a `start` with an offset of two hours east of UTC, is the same instant with `utcoffset()` equal to zero until `advance`, and after `advance(timedelta(seconds=5))` it is 5 seconds later; `SystemClock().now()` is aware and its `utcoffset()` is zero.
12. `ManualClock` with a naive `start` raises `ValueError`.
13. `TimestampedFactoryLog.line("hello")` with a clock whose time has a fractional second (for example `.987654`) writes to standard output exactly `<stamp> hello` and a newline, where the stamp has the form `YYYY-MM-DDTHH:MM:SSZ`, in UTC, with the clock's whole seconds (the fraction is dropped, not rounded up).
14. With a `Clock` whose time has an offset of two hours east of UTC, the stamp is the same instant in UTC: the time of day in the stamp is two hours earlier than the clock's own.
15. `line` also appends the same line to the file at `path`: after two calls, with the clock advanced by 5 seconds between them, the file holds the two lines in order, the second stamped 5 seconds after the first, and what the file held before the first call is kept.
16. `line("a\nb")` writes two lines, `<stamp> a` and `<stamp> b`, both to standard output and to the file, with the same stamp.
17. `line("")` writes the one line `<stamp> ` (the stamp and a space), and `line("a\n")` writes the one line `<stamp> a` (one test, two calls).
18. When the parent directory of its path does not exist, `TimestampedFactoryLog.line` and `JsonHealthStatusFile.write` create it and write (one test, both classes).
19. When the path of the log or of the health file lies below a regular file, `line` and `write` raise `OSError` (one test, both classes); for the log, the line has reached standard output.
20. `JsonHealthStatusFile.write(status)` then `read()` returns a status equal to it, with its stops in order.
21. `JsonHealthStatusFile.read()` on a path that does not exist returns `HealthStatus()`.
22. `JsonHealthStatusFile.read()` returns `HealthStatus()` for a file that holds `not json`, for one that holds `{"stops": [], "extra": 1}`, for an empty file and for one that holds the bytes `b"\xff\xfe"`, and in these four cases a `write` afterwards replaces the file and `read()` then returns what was written; it also returns `HealthStatus()` when the path is a directory, where no `write` is tried (one test, five cases).
23. After `JsonHealthStatusFile.write`, the directory of the file holds the one file `health.json` and no other file.
24. `Clock`, `FactoryLog` and `HealthStatusStore` are abstract base classes that cannot be instantiated, whose abstract methods are exactly `now`; `line`; and `read` and `write`, each with a body that is its docstring alone; `SystemClock` and `ManualClock` inherit `Clock`, `TimestampedFactoryLog` inherits `FactoryLog` and `JsonHealthStatusFile` inherits `HealthStatusStore`.
25. `make check` stays green.
26. docs: `docs/operator-guide.md` explains the health status file (`health.json` in the state directory, one stop per reason, a missing or damaged file reads as healthy until the next stop is raised) and the time-stamped line format (`YYYY-MM-DDTHH:MM:SSZ`, UTC, whole seconds, one stamp per call); `docs/decisions.md` records that a damaged health file reads as healthy because every stop is raised again while its fault lasts, and that the file is replaced atomically.

## Demo

```bash
uv run python -c "
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.health_file import JsonHealthStatusFile
from factory.domain.stops import HealthStatus, RepositoryStop
state = Path(tempfile.mkdtemp()) / 'state'
clock = ManualClock(datetime(2026, 10, 12, 12, 0, 7, 987654, tzinfo=UTC))
log = TimestampedFactoryLog(state / 'factory.log', clock)
health = JsonHealthStatusFile(state / 'health.json')
log.line('first\nsecond')
clock.advance(timedelta(seconds=5))
log.line('third')
stop = RepositoryStop(scope='repository', reason='fetch_failed', detail='origin unreachable', at=clock.now())
health.write(HealthStatus(stops=[stop]))
status = health.read()
print([item.reason for item in status.stops], status.healthy)
print(sorted(path.name for path in state.iterdir()))
(state / 'health.json').write_text('not json')
print(health.read().healthy)
"
```
Expect: six lines of output. Lines 1 and 2 are `<stamp> first` and `<stamp> second` with one and the same stamp; line 3 is `<stamp> third` with a stamp 5 seconds after the first; every stamp has the form `YYYY-MM-DDTHH:MM:SSZ` and starts with the date `2026-10-12T`. Line 4 is `['fetch_failed'] False`, line 5 is `['factory.log', 'health.json']` and line 6 is `True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures in all four layers (`domain/stops.py`, `application/machine.py`, `adapters/clock.py`, `factory_log.py`, `health_file.py`). Every comment-stated behaviour has a criterion: UTC conversion (6, 11), the stamp format and whole seconds (13, 14), splitlines (16, 17), parent directories (18), the atomic replace (23), and a damaged file reading as `HealthStatus()` (21, 22).
   - Criteria: each is testable by one test function. Every rule has its failing side: blank `detail` (1), wrong scope (3), unknown reason (4), naive `at` (5), duplicate reason (10), unknown field (7), assignment (8), naive `ManualClock` start (12), `OSError` on write (19), and damaged or missing file (21, 22).
   - Demo: it is runnable. It prints six lines (three log lines and three prints), and each `Expect:` line can be checked against the output.
   - Architecture: models are in domain, ABCs in application, implementations in adapters, and each implementation inherits its interface (24). Nothing is wired here, which matches the assignment.
   - Scope: the story is inside F0003 (S0001, ST3.4, R27) and touches nothing under "Out of scope". `StopService` and `Boundaries` are left to S0002.
