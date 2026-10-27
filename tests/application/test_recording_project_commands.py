"""The project commands that record every run of another implementation."""

from collections.abc import Callable, Sequence
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.files import RecordLog
from factory.application.git import Git
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.checks import CheckResult, TargetTime, status_of
from factory.domain.command_records import CommandRecord
from factory.domain.errors import GitError, ProjectCommandError
from factory.domain.git import CommitId
from preflight_support import RecordingCommands
from project_command_support import raising
from record_support import UnwritableRecordLog

TIME_LIMIT = timedelta(minutes=10)
TARGETS = [TargetTime(target="lint", seconds=4.5), TargetTime(target="test", seconds=170.0)]


def _result(command: str, exit_status: int | None, seconds: float = 183.5) -> CheckResult:
    return CheckResult(
        command=command,
        status=status_of(exit_status),
        exit_status=exit_status,
        duration=timedelta(seconds=seconds),
        last_line=f"{command}: green" if exit_status == 0 else "make: *** Error",
        output_tail="",
        targets=TARGETS if exit_status == 0 else [],
    )


def _answering(results: Sequence[CheckResult]) -> Callable[[str, timedelta], CheckResult]:
    queue = list(results)
    return lambda _command, _limit: queue.pop(0)


class UnresolvableGit(GitCli):
    """A checkout whose every ref fails to resolve."""

    @override
    def resolve(self, ref: str) -> CommitId | None:
        raise GitError(f"git rev-parse {ref}", 128, "fatal: not a git repository")


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[CommandRecord]:
    """Return the record log of the test, in `tmp_path`."""
    return JsonLinesRecordLog(tmp_path / "records" / "project-commands.jsonl", CommandRecord)


@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    """Return the path of the test's factory log."""
    return tmp_path / "state" / "factory.log"


def _recorder(
    answer: Callable[[str, timedelta], CheckResult],
    git: Git,
    records: RecordLog[CommandRecord],
    clock: ManualClock,
    log_path: Path,
) -> RecordingProjectCommands:
    inner = RecordingCommands(answer)
    return RecordingProjectCommands(
        inner, git, records, clock, TimestampedFactoryLog(log_path, clock)
    )


def test_a_run_returns_the_inner_result_and_records_it(
    checkout: GitCli,
    records: JsonLinesRecordLog[CommandRecord],
    clock: ManualClock,
    log_path: Path,
) -> None:
    result = _result("check", 0)
    recorder = _recorder(_answering([result]), checkout, records, clock, log_path)

    returned = recorder.run("check", time_limit=TIME_LIMIT)

    assert returned == result
    assert records.read() == [
        CommandRecord(
            command="check",
            commit=checkout.resolve("HEAD"),
            started_at=clock.now(),
            duration_seconds=183.5,
            status="passed",
            exit_status=0,
            targets=TARGETS,
        )
    ]


@pytest.mark.parametrize(
    "exit_statuses",
    [[0, 2, None], [None, 0, 2], [2, None, 0]],
    ids=["passed-red-limit", "limit-passed-red", "red-limit-passed"],
)
def test_every_run_is_recorded_in_order_with_its_status(
    exit_statuses: list[int | None],
    checkout: GitCli,
    records: JsonLinesRecordLog[CommandRecord],
    clock: ManualClock,
    log_path: Path,
) -> None:
    results = [
        _result("check", status, seconds=10.0 * (index + 1))
        for index, status in enumerate(exit_statuses)
    ]
    recorder = _recorder(_answering(results), checkout, records, clock, log_path)

    for _ in results:
        recorder.run("check", time_limit=TIME_LIMIT)

    assert [
        (record.status, record.exit_status, record.duration_seconds) for record in records.read()
    ] == [
        (result.status, result.exit_status, result.duration.total_seconds()) for result in results
    ]


@pytest.mark.parametrize(
    "error",
    [ProjectCommandError("check", "make not found"), ValueError("time_limit must be positive")],
    ids=["cannot-start", "no-time-limit"],
)
def test_an_inner_error_propagates_and_records_nothing(
    error: Exception,
    checkout: GitCli,
    records: JsonLinesRecordLog[CommandRecord],
    clock: ManualClock,
    log_path: Path,
) -> None:
    recorder = _recorder(raising(error), checkout, records, clock, log_path)

    with pytest.raises(type(error)):
        recorder.run("check", time_limit=TIME_LIMIT)

    assert records.read() == []


def test_a_record_that_cannot_be_written_is_logged_and_the_result_still_returned(
    checkout: GitCli, clock: ManualClock, log_path: Path
) -> None:
    result = _result("check", 0)
    unwritable: UnwritableRecordLog[CommandRecord] = UnwritableRecordLog(OSError("disk full"))
    recorder = _recorder(_answering([result]), checkout, unwritable, clock, log_path)

    returned = recorder.run("check", time_limit=TIME_LIMIT)

    assert returned == result
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert [line.split(" ", 1)[1] for line in lines] == [
        "cannot write the record of check: disk full"
    ]


def test_a_head_that_cannot_be_resolved_records_no_commit(
    tmp_path: Path,
    records: JsonLinesRecordLog[CommandRecord],
    clock: ManualClock,
    log_path: Path,
) -> None:
    git = UnresolvableGit(tmp_path)
    recorder = _recorder(_answering([_result("check", 2)]), git, records, clock, log_path)

    recorder.run("check", time_limit=TIME_LIMIT)

    assert [record.commit for record in records.read()] == [None]
