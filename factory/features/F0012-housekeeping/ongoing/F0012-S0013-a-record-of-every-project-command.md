---
stage: docs
pr: 165
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A record of every project command

## Assignment (as of log entry 1)

`make check` inside agent runs took 34 % of the agents' time while v1 built v1.1, and the factory's own runs of it after each stage were not counted at all. The human's word ("Telemetry in v1.1") is that every project command the factory runs is a record: command, commit, duration, exit status, and for `make check` each target's time (F0012-S0012). The records also let the count of `make check` runs on one commit be measured, the lever "skip a check whose result for that commit is known" (FEATURE decision 22). This story wraps the project commands in a recorder that appends one JSON line per run to `records/project-commands.jsonl` in the state directory, through a small interface for append-only record files that F0012-S0016 uses again for the disk record. The records are telemetry beside the factory log, not a work item's state, so they are not committed (FEATURE decision 21). `read` has no caller in `src/factory` until F0012-S0016's disk record uses it, so the duplicates record after the coder lists it as new dead code until then; that is expected, not a finding. The wiring test that names the project commands' class changes by the human's leave (FEATURE decision 36).

## Interface

`src/factory/domain/command_records.py` (new):

```python
class CommandRecord(BaseModel):
    """One run of a project command: what, on which commit, when, how long and how it ended."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    command: CommandName
    commit: CommitId | None
    started_at: UtcDatetime
    duration_seconds: Duration
    status: CheckStatus
    exit_status: int | None
    targets: list[TargetTime] = []
```

`Duration` is `factory.domain.cost_records.Duration`: a float of at least 0, finite.

`src/factory/application/files.py` gains:

```python
class RecordLog[R: BaseModel](ABC):
    """An append-only file of records, one JSON object per line."""

    @abstractmethod
    def append(self, record: R) -> None:
        """Add `record` as the last line, creating the file and its folder; `OSError` when it cannot."""

    @abstractmethod
    def read(self) -> list[R]:
        """The records in file order; `[]` without a file; a line that does not validate is skipped."""
```

`src/factory/adapters/record_log_jsonl.py` (new): `class JsonLinesRecordLog[R: BaseModel](RecordLog[R])` with `__init__(self, path: Path, model: type[R])`. `append` writes `record.model_dump_json()` and `\n` in one write to the file opened for appending. `read` validates each non-blank line with `model.model_validate_json` and skips one that raises `ValidationError` (a kill can tear the last line).

`src/factory/application/project_commands.py` gains:

```python
class RecordingProjectCommands(ProjectCommands):
    """Runs the project commands of another implementation and records every run."""

    def __init__(
        self, inner: ProjectCommands, git: Git, records: RecordLog[CommandRecord], clock: Clock, log: FactoryLog
    ) -> None: ...

    def run(self, command: str, *, time_limit: timedelta) -> CheckResult: ...
```

`run` reads `git.resolve("HEAD")` (a `GitError` gives `None`), takes `clock.now()` as `started_at`, runs `inner.run`, appends `CommandRecord(command, commit, started_at, duration_seconds=<the result's duration in seconds>, status, exit_status, targets)` and returns the inner result unchanged. A `ProjectCommandError` or `ValueError` of `inner.run` propagates and records nothing. An `OSError` of `append` writes the factory log line `cannot write the record of <command>: <error>` and the result is still returned.

`src/factory/entry/wiring.py`: `build_boundaries` builds `project_commands=RecordingProjectCommands(MakeProjectCommands(settings.checkout), <its GitCli>, JsonLinesRecordLog(<state directory>/records/project-commands.jsonl, CommandRecord), <its clock>, <its log>)`, the same `GitCli`, clock and log it puts into the boundaries.

Tests: `tests/domain/test_command_records.py`, `tests/adapters/test_record_log_jsonl.py`, `tests/application/test_recording_project_commands.py` and `tests/entry/test_wiring_command_records.py`. The recorder's inner project commands are `RecordingCommands` of `tests/application/test_preflight_run.py`, imported as `tests/application/test_interfaces.py` imports from `tests/application/test_git_interface.py`, with an `answer` that returns the given result or raises; `git` is the `checkout` fixture, the record log a `JsonLinesRecordLog` in `tmp_path`, the clock the `clock` fixture and the log a `TimestampedFactoryLog` in `tmp_path`; criterion 8's `git` is a fake written in the test whose `resolve` raises `GitError`. A new shared helper module `tests/record_support.py` holds `UnwritableRecordLog`, a `RecordLog` whose `append` raises the `OSError` it was given and whose `read` is `[]`; F0012-S0016 imports it. By the human's leave (FEATURE decision 36), and no other change to an earlier story's test: `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` in `tests/entry/test_wiring_boundaries.py` expects `RecordingProjectCommands` for `project_commands`.

## Acceptance criteria

1. A `CommandRecord` with `commit=None`, `exit_status=None`, `status="time_limit"` and `duration_seconds=0` is accepted; one whose `commit` is not 40 lowercase hexadecimal characters, whose `command` is `"Check"`, whose `duration_seconds` is `-1` or `float("inf")`, whose `status` is `"red"` (outside `CheckStatus`), or whose `started_at` has no offset, is refused with `pydantic.ValidationError`. Rows of one parametrized test.
2. `JsonLinesRecordLog` appends records as lines and `read` gives them back equal and in order; a missing file reads `[]`; its folder is created on the first `append`.
3. A file whose middle line is `{"command":` and whose last line is `not json` reads as the valid lines only.
4. `RecordingProjectCommands.run("check", time_limit=...)` returns the inner result unchanged and appends one record with the command, the commit `HEAD` of the checkout, `started_at` equal to the clock's reading, the result's duration in seconds, its status, exit status and targets.
5. Three runs append three records in order; a red run (exit status 2) and a run ended by its time limit (`exit_status None`, `time_limit`) are recorded as such. Rows of one parametrized test.
6. An inner `ProjectCommandError` and an inner `ValueError` (as `MakeProjectCommands` raises for a time limit of 0) each propagate from `run`, and nothing is appended. Two rows of one parametrized test.
7. With an `UnwritableRecordLog` whose `append` raises `OSError("disk full")`, the result is still returned and the factory log gains one line `cannot write the record of check: disk full`.
8. A checkout whose `HEAD` cannot be resolved (a `git` whose `resolve` raises `GitError`, a fake written in the test) records `commit=None`.
9. `build_boundaries` gives `project_commands` that is a `RecordingProjectCommands`; a run of `lint` through it in the built checkout appends one record to `<state directory>/records/project-commands.jsonl`.
10. `make check` stays green.
11. docs: the operator guide's section on the factory log and the health status file gets a part *The records* that names `records/project-commands.jsonl` in the state directory, its fields, that it is telemetry the operator may delete, and how to count the `check` runs of one commit (one `python3 -c` line that reads the file with the `json` module; neither image has `jq`); the project guide's section *Project commands* names `RecordingProjectCommands`, `RecordLog` and `JsonLinesRecordLog`; the decision log records why the records are not committed. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.command_records import CommandRecord
with tempfile.TemporaryDirectory() as folder:
    log = JsonLinesRecordLog(Path(folder) / 'records' / 'project-commands.jsonl', CommandRecord)
    log.append(CommandRecord(command='check', commit='a' * 40, started_at=datetime(2026, 10, 17, tzinfo=UTC), duration_seconds=183.5, status='passed', exit_status=0))
    print(len(log.read()), log.read()[0].command, log.read()[0].duration_seconds)
"
```
Expect: `1 check 183.5`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_recording_project_commands.py tests/adapters/test_record_log_jsonl.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures throughout (domain/command_records.py, application/files.py RecordLog, adapters/record_log_jsonl.py, RecordingProjectCommands, wiring). The types it names exist: CommitId, Duration, CheckStatus, CommandName, TargetTime, UtcDatetime, Clock and FactoryLog.
   - Criteria: each is testable by one test function or one parametrized test. Rules and their failing sides: the model's refused values (1), a torn or invalid line skipped (3), an inner error propagating with nothing appended (6), an OSError on append logged without losing the result (7), an unresolvable HEAD giving None (8). The Interface's behaviours (read order, a missing file, folder creation, unchanged result, started_at from the clock) are in 2, 4 and 5.
   - Demo: both blocks are runnable and each Expect line is checkable (`1 check 183.5`; the pytest summary with no failed, error or skipped count).
   - Architecture: the interface in application, the JSONL adapter in adapters, the wiring only in entry, the DTO in domain, so the layers are respected. The test changes (decision 36 leave, tests/record_support.py) are named in the story.
   - Scope: inside F0012 scope 1.4, and not in its Out of scope.
3. tester: Wrote red tests for criteria 1–9.
   - criterion 1: tests/domain/test_command_records.py::test_a_command_record_accepts_valid_values_and_refuses_the_others. One parametrized test. Accepted rows: the criterion's case with duration 0, and a passed record whose commit is "a"*40. Refused rows: a commit of 39 characters, of 41, uppercase, and non-hex; command "Check"; duration -1; duration inf; status "red"; a naive started_at.
   - criterion 2: tests/adapters/test_record_log_jsonl.py::test_appended_records_read_back_equal_and_in_order_and_the_folder_is_created
   - criterion 3: tests/adapters/test_record_log_jsonl.py::test_lines_that_do_not_validate_are_skipped. The file has five lines: valid, valid, `{"command":` in the middle, valid, `not json` last.
   - criterion 4: tests/application/test_recording_project_commands.py::test_a_run_returns_the_inner_result_and_records_it
   - criterion 5: tests/application/test_recording_project_commands.py::test_every_run_is_recorded_in_order_with_its_status. Three rows, each running three results (exit 0, 2 and None) in a different order.
   - criterion 6: tests/application/test_recording_project_commands.py::test_an_inner_error_propagates_and_records_nothing. Two rows: ProjectCommandError and ValueError.
   - criterion 7: tests/application/test_recording_project_commands.py::test_a_record_that_cannot_be_written_is_logged_and_the_result_still_returned
   - criterion 8: tests/application/test_recording_project_commands.py::test_a_head_that_cannot_be_resolved_records_no_commit. The fake is `UnresolvableGit`, defined in the test: a GitCli subclass whose `resolve` raises GitError.
   - criterion 9: tests/entry/test_wiring_command_records.py::test_the_built_project_commands_record_a_run_in_the_state_directory. It clones the remote into settings.checkout, writes a Makefile with a `lint` target and checks for one record (lint, HEAD of the built git, passed).

   Files created: tests/domain/test_command_records.py, tests/adapters/test_record_log_jsonl.py, tests/application/test_recording_project_commands.py, tests/entry/test_wiring_command_records.py, and the shared helper tests/record_support.py (`UnwritableRecordLog[R]`).

   File changed by the human's leave (FEATURE decision 36): tests/entry/test_wiring_boundaries.py. `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` now expects `RecordingProjectCommands`, and the import of MakeProjectCommands that is no longer used is gone. Nothing else in that file changed.

   The recorder's inner commands are `RecordingCommands`, imported from `application.test_preflight_run`.

   make test: collection errors only, because these imports fail: factory.domain.command_records, factory.adapters.record_log_jsonl, `RecordLog` from factory.application.files and `RecordingProjectCommands` from factory.application.project_commands. make lint: green. The type check was not run, as this stage's skill says.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/entry/test_wiring_command_records.py - ImportError while importin...
4. coder: Built the project command recorder; `make check` is green (99.5 % coverage) and the tests are untouched.
      - `src/factory/domain/command_records.py`: the new `CommandRecord`, built from the existing types `CommandName`, `CommitId`, `UtcDatetime`, `Duration`, `CheckStatus` and `TargetTime`.
      - `src/factory/application/files.py`: the new generic interface `RecordLog[R: BaseModel]` with `append` and `read`. Both docstrings are split over two lines to stay within the line length.
      - `src/factory/adapters/record_log_jsonl.py`: the new `JsonLinesRecordLog`. `append` creates the folder and writes `model_dump_json()` plus `\n` in one write to the file opened for appending. `read` gives `[]` without a file, skips blank lines and skips a line that raises `ValidationError`.
      - `src/factory/application/project_commands.py`: the new `RecordingProjectCommands`. It reads `HEAD` before the run (a `GitError` gives `None`) and the clock's `started_at`, then runs `inner.run`. Errors from the inner run propagate before anything is recorded. An `OSError` on append becomes the factory log line `cannot write the record of <command>: <error>`, and the result is returned unchanged either way.
      - `src/factory/entry/wiring.py`: `build_boundaries` now builds one `GitCli` and one log and shares them, with the clock, between the boundaries and the recorder. The record file is `<state>/records/project-commands.jsonl`, held in the constant `_COMMAND_RECORDS_PATH`.
      - Main decision: the record takes `command` from the caller's argument, not from `result.command`, as the Interface says. The two are equal for every real implementation. I rejected a dedicated reader and writer pair like the cost records have: the Interface asks for one generic append-only log that the disk record can use again.
      - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
      - Noticed, not touched: `make duplicates` reports `duplicates: 2 new, 39 known, 0 gone`. Both new findings are an unused `used_bytes` in `adapters/disk_space.py` and `application/machine.py`, which this ticket did not change. `RecordLog.read` is not listed as dead code, although the Assignment expected it to be. Line 34 of `record_log_jsonl.py`, the blank-line skip, is the one line no test covers.

   `make check`: check: green
   `make duplicates`: duplicates: 2 new, 39 known, 0 gone
5. reviewer: no findings.
      - Acceptance criteria: criteria 1–9 each have the test the tester's entry names, and each test checks its criterion. Criterion 1 covers both sides of every limit: `Duration` is accepted at 0 and refused at -1 and at inf; `CommitId` is accepted as `"a"*40` and refused with 39 or 41 characters, in uppercase and with non-hex characters; `CommandName` is accepted as `check` and refused as `Check`; `CheckStatus` refuses `red`; a `started_at` with an offset is accepted and a naive one refused. The failing sides of the Interface's rules are all tested: a torn or invalid line is skipped (3), an inner error propagates with nothing appended (6), an `OSError` on `append` is logged and the result still returned (7), and a `GitError` from `resolve` gives `commit=None` (8). The coder's entry says `make check` was green. The only change to an earlier story's test is the `isinstance` line in `tests/entry/test_wiring_boundaries.py`, by the human's leave (FEATURE decision 36), plus the import that became unused.
      - Architecture: `CommandRecord` is in domain. `RecordLog` is an `abc.ABC` in `application/files.py` whose abstract methods have docstring-only bodies. `RecordingProjectCommands` in application depends only on application interfaces. `JsonLinesRecordLog` in adapters inherits its interface. Wiring happens only in `entry/wiring.py`, which shares one `GitCli`, clock and log between the boundaries and the recorder. No `dict[str, Any]` crosses a boundary and no tool is called outside a wrapper.
      - Security: no secrets, no suppression markers, no shell or string-built commands; the record path comes from the settings.
      - Quality: names and docstrings fit the project's conventions, and the comments explain why (one write per line; telemetry must not lose a result). `CommandRecord` reuses the existing types (`CommandName`, `CommitId`, `UtcDatetime`, `Duration`, `CheckStatus`, `TargetTime`) rather than redefining them. Considered and not raised: the blank-line skip in `JsonLinesRecordLog._parse` (`src/factory/adapters/record_log_jsonl.py:34`) has no test and changes nothing, because `model_validate_json` raises `ValidationError` for a blank line anyway. It follows the Interface's "each non-blank line" literally. The 2 new `make duplicates` findings (`used_bytes` in `adapters/disk_space.py` and `application/machine.py`) are in files this diff does not touch.
      - Ticket hygiene: the coder's entry gives the main decision (`command` comes from the caller's argument) and the rejected alternative (a separate reader and writer pair like the cost records). `Assignment` matches what was built, and criterion 11 still describes what the documenter must write.
