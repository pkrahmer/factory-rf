"""The rig of the known check results tests, shared by the torn-record tests."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path

from factory.adapters.clock import ManualClock
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.known_results import KnownResults
from factory.domain.checks import CheckResult, status_of
from factory.domain.known_results import ResultRecord
from factory.domain.pipeline_definition import PipelineDefinition
from git_support import PIPELINE_YAML
from log_support import log_lines
from preflight_support import RecordingCommands

DEFINITION_YAML = PIPELINE_YAML.replace(
    "check: {time_limit: 10}", 'check: {time_limit: 10, not_read: ["docs/*"]}'
)


TIME_LIMIT = timedelta(minutes=10)


def _result(command: str, exit_status: int | None) -> CheckResult:
    return CheckResult(
        command=command,
        status=status_of(exit_status),
        exit_status=exit_status,
        duration=timedelta(seconds=42.5),
        last_line=f"{command}: green" if exit_status == 0 else "make: *** Error",
        output_tail="the tail\n",
        targets=[],
    )


def _answering(
    clock: ManualClock, exit_statuses: Sequence[int | None] = ()
) -> Callable[[str, timedelta], CheckResult]:
    """Answer each run with the next exit status (then 0), the clock advanced by a minute."""
    queue = list(exit_statuses)

    def answer(command: str, _limit: timedelta) -> CheckResult:
        clock.advance(timedelta(minutes=1))
        return _result(command, queue.pop(0) if queue else 0)

    return answer


@dataclass
class Rig:
    """Boundaries on the test's checkout whose project commands record their calls."""

    boundaries: Boundaries
    commands: RecordingCommands
    records: JsonLinesRecordLog[ResultRecord]
    definition: PipelineDefinition
    tmp_path: Path

    def known(self) -> KnownResults:
        """A `KnownResults` on the rig's boundaries and definition."""
        return KnownResults(self.boundaries, self.definition)

    def log_lines(self) -> list[str]:
        """The factory log's lines without their time stamps."""
        return [line.split(" ", 1)[1] for line in log_lines(self.tmp_path)]


def _rig(
    boundaries: Boundaries,
    tmp_path: Path,
    answer: Callable[[str, timedelta], CheckResult],
) -> Rig:
    commands = RecordingCommands(answer)
    records = JsonLinesRecordLog(
        tmp_path / "state" / "records" / "known-results.jsonl", ResultRecord
    )
    rigged = replace(boundaries, project_commands=commands, result_records=records)
    definition = rigged.pipeline_reader.parse(DEFINITION_YAML)
    return Rig(rigged, commands, records, definition, tmp_path)
