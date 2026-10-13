---
stage: doing
pr: 40
blocked: asked
comments_seen: 1
round: 1
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
3. tester: I wrote red tests for criteria 1–24. Criterion 25 is `make check` and criterion 26 is docs, so neither gets a test.
      - criterion 1: tests/domain/test_stops.py::test_a_blank_detail_is_rejected (cases: empty, whitespace only, `x` accepted)
      - criterion 2: tests/domain/test_stops.py::test_each_reason_is_accepted_with_its_scope (all seven reasons)
      - criterion 3: tests/domain/test_stops.py::test_each_reason_is_rejected_with_the_other_scope (all seven reasons)
      - criterion 4: tests/domain/test_stops.py::test_an_unknown_reason_is_rejected (`other` and the empty text)
      - criterion 5: tests/domain/test_stops.py::test_a_naive_time_is_rejected
      - criterion 6: tests/domain/test_stops.py::test_an_aware_time_is_stored_as_the_same_instant_in_utc
      - criterion 7: tests/domain/test_stops.py::test_both_models_reject_an_unknown_field (through variables typed `type[BaseModel]`)
      - criterion 8: tests/domain/test_stops.py::test_a_field_cannot_be_assigned (uses `setattr`; one case per model)
      - criterion 9: tests/domain/test_stops.py::test_a_status_is_healthy_exactly_when_it_holds_no_stop
      - criterion 10: tests/domain/test_stops.py::test_a_status_holds_at_most_one_stop_per_reason
      - criterion 11: tests/adapters/test_clock.py::test_the_clocks_tell_aware_utc_time
      - criterion 12: tests/adapters/test_clock.py::test_a_manual_clock_refuses_a_naive_start
      - criterion 13: tests/adapters/test_factory_log.py::test_a_line_is_stamped_with_whole_utc_seconds (clock at 12:00:07.987654 UTC; expects exactly `2026-10-12T12:00:07Z hello\n`)
      - criterion 14: tests/adapters/test_factory_log.py::test_a_clock_east_of_utc_is_stamped_in_utc (a small `Clock` subclass at +02:00)
      - criterion 15: tests/adapters/test_factory_log.py::test_lines_are_appended_to_the_file_in_order
      - criterion 16: tests/adapters/test_factory_log.py::test_a_text_of_several_lines_writes_each_with_one_stamp
      - criterion 17: tests/adapters/test_factory_log.py::test_an_empty_text_and_a_trailing_newline_each_write_one_line
      - criterion 18: tests/adapters/test_health_file.py::test_the_log_and_the_health_file_create_missing_parent_directories
      - criterion 19: tests/adapters/test_health_file.py::test_a_path_below_a_regular_file_fails_the_write_after_standard_output
      - criterion 20: tests/adapters/test_health_file.py::test_a_written_status_reads_back_equal_in_order (three stops, order checked)
      - criterion 21: tests/adapters/test_health_file.py::test_a_missing_file_reads_as_healthy
      - criterion 22: tests/adapters/test_health_file.py::test_a_damaged_file_reads_as_healthy_and_is_replaced_by_the_next_write (five cases; the directory case tries no write)
      - criterion 23: tests/adapters/test_health_file.py::test_a_write_leaves_only_the_health_file_in_its_directory (two writes, then the directory is listed)
      - criterion 24: tests/application/test_machine.py::test_each_machine_interface_is_an_abstract_base_class_of_its_operations (one case per interface; covers ABC, the exact abstract methods, a docstring-only body checked with ast, instantiation raises TypeError through a variable typed `type[object]`, and which classes inherit each interface)

      Files: I created tests/domain/test_stops.py, tests/application/test_machine.py, tests/adapters/test_clock.py, tests/adapters/test_factory_log.py and tests/adapters/test_health_file.py. tests/conftest.py now has the `clock` fixture, a `ManualClock` at `datetime(2026, 10, 12, 12, 0, tzinfo=UTC)`.

      Red: the test run cannot import `factory.adapters.clock`, `factory.adapters.factory_log`, `factory.adapters.health_file`, `factory.application.machine` or `factory.domain.stops`. Because conftest imports `ManualClock` at the top, the whole suite stops at the conftest ImportError until `factory.adapters.clock` exists. That is the expected red. `make lint` passes. I skipped the type check, as the stage says.

   `make lint`: lint: green
   `make test`: E   ModuleNotFoundError: No module named 'factory.adapters.clock'
4. coder: I implemented the interface. All tests pass and `make check` is green (5f7cf90 feat, d683e40 refactor).
      - Built:
        - `src/factory/domain/stops.py`: `RepositoryStop` and `HealthStatus`. Validators refuse a blank detail, convert `at` to UTC, require scope `machine` exactly for `preflight_failed`, and allow one stop per reason. `healthy` is a property.
        - `src/factory/application/machine.py`: `Clock`, `FactoryLog` and `HealthStatusStore` as ABCs whose abstract methods have docstring-only bodies.
        - `src/factory/adapters/clock.py`: `SystemClock` and `ManualClock`. A naive start raises `ValueError`, and the start is stored in UTC.
        - `src/factory/adapters/factory_log.py`: `TimestampedFactoryLog`. The clock is read once per call. The stamp is formatted with `strftime("%Y-%m-%dT%H:%M:%SZ")`, which truncates the fraction rather than rounding. `splitlines() or [""]` makes an empty text one line. Each call writes to stdout and flushes before it creates the parent directories and appends to the file.
        - `src/factory/adapters/health_file.py`: `JsonHealthStatusFile`. `write` uses `tempfile.mkstemp` in the target directory, writes `model_dump_json()`, then calls `os.replace`; if anything fails, the temporary file is removed and the error re-raised. `read` treats `OSError`, `UnicodeDecodeError` and `ValidationError` as `HealthStatus()`; pydantic's `model_validate_json` covers both non-JSON input and an invalid model.
      - Main decision: `write` puts the temporary file next to the target and moves it with `os.replace`, so the replace is atomic on one filesystem. I rejected writing the target in place, because a reader could see half a file.
      - Refactor: I merged the two `try` blocks in `read` into one.
      - Demo: I ran it, and its six lines match the Expect.
      - Noticed, not touched:
        - The cleanup branch in `write` (lines 45–47) is not covered. No test makes the write fail after `mkstemp` succeeds, and total coverage is 99.5 %.
        - Nothing is wired yet. As the assignment says, `StopService` and `Boundaries` belong to S0002.
        - The docs criterion (26) is left to the documenter.

   `make check`: check: green
5. reviewer: one finding, in group 1 (acceptance criteria). It is a gap in the story, not a fault of the tester or the coder.

   1. `src/factory/adapters/health_file.py:47-49`, Interface rule on `JsonHealthStatusFile.write` ("no temporary file stays behind") together with criterion 22. No criterion covers the failing side of this rule. A write that fails after `mkstemp` should leave no `.health.json.*.tmp` behind, but nothing tests that, and the `except BaseException` cleanup branch is never run (the coder's entry says so too). The failure can be produced without mocking. When `health.json` is a directory, `os.replace` raises `IsADirectoryError`. That is exactly the directory case criterion 22 skips ("where no write is tried"). It also means the Interface's "the next `write` replaces it" is not true for a directory at the path. Fix: the human adds a criterion before 25: "When the path of the health file is a directory, `write` raises `OSError` and leaves no file other than `health.json` in the parent directory." The Interface sentence should also say that a directory at the path is not replaced but fails the write. The tester then writes the test. The coder should end with `question` to the human, because R9 forbids the coder from adding the criterion or the test.

   Checked and fine:
   - Criteria 1–24: each has a test that tests what it is named after.
   - Both sides of the detail, scope, reason, naive-time, duplicate-reason and naive-start rules are covered.
   - The coder's `make check` was green.

   Because the review stops at the first failing group, I did not report on architecture, security, quality or hygiene. A first read found nothing there.
6. coder: coder (round 1): the review's one finding needs a criterion and a test that I am not allowed to add (R9, R13), so I am asking. I changed no code.

   The finding is that the failing side of the Interface rule "no temporary file stays behind" is untested. When `health.json` is a directory, `JsonHealthStatusFile.write` raises `IsADirectoryError` from `os.replace`. The code already handles this case: `src/factory/adapters/health_file.py:36-43` deletes the temporary file in `except BaseException` and re-raises. No test runs that branch, though, and the Interface's "the next `write` replaces it" is wrong for a directory at the path.

   Question: should the ticket get the criterion the reviewer proposes?

   Options:
   - (a) Yes (my choice). Add a criterion before 25: "When the path of the health file is a directory, `write` raises `OSError` and leaves no file other than `health.json` in the parent directory." Also add a sentence to the Interface's `JsonHealthStatusFile` rule: "a directory at the path is not replaced; `write` raises `OSError` and removes its temporary file." After your answer I end with `tests` so the tester writes that one test. The code should pass it as it stands.
   - (b) No. Accept the uncovered branch, because coverage is 99.5 %. The only change would be to drop "and the next `write` replaces it" for the directory case from the Interface wording. No test or code changes.
   - (c) Remove the cleanup branch and let a failed write leave its temporary file. I advise against this: it breaks the Interface rule.
