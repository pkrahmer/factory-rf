# A record of every project command

## Assignment (as of log entry 1)

`make check` inside agent runs took 34 % of the agents' time while v1 built v1.1, and the factory's own runs of it after each stage were not counted at all. The human's word ("Telemetry in v1.1") is that every project command the factory runs is a record: command, commit, duration, exit status, and for `make check` each target's time (F0012-S0012). The records also let the count of `make check` runs on one commit be measured, the lever "skip a check whose result for that commit is known" (FEATURE decision 22). This story wraps the project commands in a recorder that appends one JSON line per run to `records/project-commands.jsonl` in the state directory, through a small interface for append-only record files that F0012-S0016 uses again for the disk record. The records are telemetry beside the factory log, not a work item's state, so they are not committed (FEATURE decision 21). The wiring test that names the project commands' class changes by the human's leave (FEATURE decision 36).

## Interface

`src/factory/domain/command_records.py` (new):

```python
class CommandRecord(BaseModel):
    """One run of a project command: what, on which commit, when, how long and how it ended."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    command: CommandName
    commit: CommitId | None
    started_at: UtcDatetime
    duration_seconds: NonNegativeFloat
    status: CheckStatus
    exit_status: int | None
    targets: list[TargetTime] = []
```

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

Tests: `tests/domain/test_command_records.py`, `tests/adapters/test_record_log_jsonl.py`, `tests/application/test_recording_project_commands.py` (with a fake `ProjectCommands` written in the test, the `checkout` fixture as `git`, a `JsonLinesRecordLog` in `tmp_path`, the `clock` fixture and a `TimestampedFactoryLog` in `tmp_path`), `tests/entry/test_wiring_command_records.py`. By the human's leave (FEATURE decision 36), and no other change to an earlier story's test: `test_build_boundaries_picks_the_concrete_adapters_and_writes_nothing` in `tests/entry/test_wiring_boundaries.py` expects `RecordingProjectCommands` for `project_commands`.

## Acceptance criteria

1. A `CommandRecord` with `commit=None`, `exit_status=None` and `status="time_limit"` is accepted; one whose `commit` is not 40 lowercase hexadecimal characters, whose `duration_seconds` is `-1`, or whose `status` is `"red"` (outside `CheckStatus`) is refused with `pydantic.ValidationError`. Rows of one parametrized test.
2. `JsonLinesRecordLog` appends records as lines and `read` gives them back equal and in order; a missing file reads `[]`; its folder is created on the first `append`.
3. A file whose middle line is `{"command":` and whose last line is `not json` reads as the valid lines only.
4. `RecordingProjectCommands.run("check", time_limit=...)` returns the inner result unchanged and appends one record with the command, the commit `HEAD` of the checkout, `started_at` equal to the clock's reading, the result's duration in seconds, its status, exit status and targets.
5. Three runs append three records in order; a red run (exit status 2) and a run ended by its time limit (`exit_status None`, `time_limit`) are recorded as such. Rows of one parametrized test.
6. An inner `ProjectCommandError` propagates and nothing is appended.
7. A record log whose `append` raises `OSError("disk full")` leaves the result returned and one factory log line `cannot write the record of check: disk full`.
8. A checkout whose `HEAD` cannot be resolved (a `git` whose `resolve` raises `GitError`, a fake written in the test) records `commit=None`.
9. `build_boundaries` gives `project_commands` that is a `RecordingProjectCommands`; a run of `lint` through it in the built checkout appends one record to `<state directory>/records/project-commands.jsonl`.
10. `make check` stays green.
11. docs: the operator guide's section on the factory log and the health status file gets a part *The records* that names `records/project-commands.jsonl` in the state directory, its fields, that it is telemetry the operator may delete, and how to count the `check` runs of one commit (one `jq` line); the project guide's section *Project commands* names `RecordingProjectCommands`, `RecordLog` and `JsonLinesRecordLog`; the decision log records why the records are not committed. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

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
