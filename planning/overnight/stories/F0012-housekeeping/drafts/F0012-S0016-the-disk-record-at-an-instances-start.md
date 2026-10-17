# The disk record at an instance's start

## Assignment (as of log entry 1)

The human's word ("Disk space", the watch at the end of every major change) is that disk use must not grow without bound: the free space and the size of the work directory, the state directory and the container's `/tmp` are recorded at the start of a run and at each feature acceptance, and compared with the last record. Until now the session wrote these numbers into the night log by hand. This story makes the factory write one disk record when an instance starts: a JSON line in `records/disk.jsonl` in the state directory (through the record file interface of F0012-S0013) and one line in the factory log. F0012-S0017 writes one at each feature acceptance and tells the acceptance reviewer. The host's own numbers (its free space, Docker's disk image) cannot be seen from the container and stay with the session (FEATURE, out of scope).

## Interface

`src/factory/domain/disk.py` (of F0012-S0009) gains:

```python
DiskOccasion = Literal["start", "acceptance"]


class DiskUse(BaseModel):
    """One folder: its path, the bytes free on its file system and the bytes under it; None is unknown."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    free_bytes: NonNegativeInt | None
    used_bytes: NonNegativeInt | None


class DiskRecord(BaseModel):
    """The folders' use at one moment, and why it was taken."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    at: UtcDatetime
    occasion: DiskOccasion
    folders: list[DiskUse]


def disk_line(record: DiskRecord) -> str:
    """`disk <occasion>: <path> <free> free, <used> used; ...`, each value in GB or `unknown`."""
```

Each folder is `<path> <free> free, <used> used`, each value written `<gigabytes(n)> GB`, or `unknown` when it is `None` (`/tmp unknown free, 4.3 GB used`); the folders are joined by `; ` after `disk <occasion>: `.

`src/factory/domain/settings.py`: `InstanceSettings` gains `temporary_directory: Path | None = None`, the last field. `read_settings` does not set it.

`src/factory/application/boundaries.py`: `Boundaries` gains a last, optional field `disk_records: RecordLog[DiskRecord] | None = None`.

`src/factory/application/disk_records.py` (new):

```python
class DiskRecorder:
    """Measures the instance's folders and keeps the measure in the records and the factory log."""

    def __init__(self, boundaries: Boundaries) -> None: ...

    def record(self, occasion: DiskOccasion) -> DiskRecord | None:
        """Measure, append and log one record; None when the boundaries have no disk, records or settings."""

    def last(self, occasion: DiskOccasion) -> DiskRecord | None:
        """The last record of `occasion` in the records, or None."""
```

- The folders, in this order: `settings.checkout.parent`, `settings.state_directory`, and `settings.temporary_directory` when it is set. For each, `disk.free_bytes` and `disk.used_bytes`; an `OSError` of either leaves that value `None`.
- `at` is `clock.now()`. The record is appended to `disk_records` and `disk_line(record)` is written as one factory log line. An `OSError` of the append writes the log line `cannot write the disk record: <error>` after the record's own line, and `record` still returns the record.

`src/factory/entry/wiring.py`: `build_boundaries` sets `disk_records=JsonLinesRecordLog(<state directory>/records/disk.jsonl, DiskRecord)`; `read_environment_settings` sets `temporary_directory` to `Path(tempfile.gettempdir())`.

`src/factory/entry/run.py`: `run_instance` calls `DiskRecorder(boundaries).record("start")` once, after it builds the boundaries and before the scheduler runs.

Tests: `tests/domain/test_disk_records.py`, `tests/application/test_disk_recorder.py` (with a fake `DiskSpace` written in the test, a `JsonLinesRecordLog` in `tmp_path`, the boundaries of `tests/conftest.py` given `disk`, `disk_records` and `settings` by `dataclasses.replace`), `tests/entry/test_run_disk_record.py` (with the settings and fakes `tests/entry/test_run.py` uses). No existing test changes.

## Acceptance criteria

1. `disk_line` of a record at `start` with `/work` (812_345_678_901 free, 700_000_000 used) and `/state` (`None` free, 1_000 used) is `disk start: /work 812.3 GB free, 0.7 GB used; /state unknown free, 0.0 GB used`.
2. A `DiskRecord` with an occasion outside `start` and `acceptance`, or a folder with `free_bytes=-1`, is refused with `pydantic.ValidationError`; a folder with both values `None` is accepted. Rows of one parametrized test.
3. `DiskRecorder.record("start")` with a fake disk returns a record of the checkout's parent and the state directory, in that order, with the fake's values and `at` equal to the clock's reading; the record log then holds exactly that record, and the factory log gains one line that ends with `disk_line` of it.
4. With `temporary_directory` set, a third folder is that directory; without it, there are two. Rows of one parametrized test.
5. A fake disk whose `free_bytes` raises `OSError` for the state directory records `free_bytes=None` for it and its `used_bytes` as given.
6. A record log whose `append` raises `OSError("disk full")` gives two factory log lines, the record's and `cannot write the disk record: disk full`, and `record` returns the record.
7. Boundaries without `disk`, without `disk_records` or without `settings` make `record` return `None`, append nothing and write no line. Rows of one parametrized test.
8. `last("start")` gives the latest `start` record of the log, ignoring `acceptance` records after it; with no record of that occasion, `None`.
9. `run_instance` with the test settings appends exactly one `start` record to `<state directory>/records/disk.jsonl` before its first tick; `read_environment_settings` gives `temporary_directory == Path(tempfile.gettempdir())`.
10. `make check` stays green.
11. docs: the operator guide's part *The records* (F0012-S0013) names `records/disk.jsonl`, its line in the factory log, when it is written, and that the host's own numbers (free space of the drive, the size of Docker's disk image, `docker system df`) are read on the host by hand at the same moments; the project guide names `DiskRecorder`, `DiskRecord` and `disk_line`. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.disk import DiskRecord, DiskUse, disk_line
record = DiskRecord(at=datetime(2026, 10, 17, tzinfo=UTC), occasion='start', folders=[DiskUse(path='/work', free_bytes=812_345_678_901, used_bytes=700_000_000), DiskUse(path='/tmp', free_bytes=None, used_bytes=4_300_000_000)])
print(disk_line(record))
"
```
Expect: `disk start: /work 812.3 GB free, 0.7 GB used; /tmp unknown free, 4.3 GB used`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_disk_records.py tests/application/test_disk_recorder.py tests/entry/test_run_disk_record.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
