"""A stage's project commands, run only when no passed result is known for the same key."""

from datetime import timedelta

from factory.application.boundaries import Boundaries
from factory.application.files import RecordLog
from factory.domain.checks import CheckResult, ReusedRun
from factory.domain.errors import GitError
from factory.domain.known_results import ResultKey, ResultRecord, definition_digest, known_result
from factory.domain.pipeline_definition import PipelineDefinition


class KnownResults:
    """A stage's project commands: a passed result known for the same key is not run again."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None:
        """Run the commands of `definition` through `boundaries`."""
        self._boundaries = boundaries
        self._definition = definition
        self._digest = definition_digest(definition)

    def run(self, command: str) -> CheckResult:
        """Run `command`, or take the passed result known for its key.

        A `ProjectCommandError` or `ValueError` of the run propagates and nothing is recorded.
        """
        records = self._boundaries.result_records
        key = self._key(command)
        if key is None:
            return self._run(command)
        known = known_result(self._read(records), key)
        if known is not None:
            return self._reuse(records, key, known)
        at = self._boundaries.clock.now()
        result = self._run(command)
        record = ResultRecord(
            key=key,
            at=at,
            status=result.status,
            last_line=result.last_line,
            duration_seconds=result.duration.total_seconds(),
        )
        self._append(records, record)
        return result

    def _run(self, command: str) -> CheckResult:
        minutes = self._definition.project_commands[command].time_limit
        return self._boundaries.project_commands.run(command, time_limit=timedelta(minutes=minutes))

    def _key(self, command: str) -> ResultKey | None:
        not_read = self._definition.project_commands[command].not_read
        try:
            tree = self._boundaries.git.work_tree_id(not_read)
        except GitError as error:
            self._boundaries.log.line(f"known results: no key for {command}: {error}")
            return None
        image = self._boundaries.settings.image
        return ResultKey(command=command, tree=tree, definition=self._digest, image=image)

    def _read(self, records: RecordLog[ResultRecord]) -> list[ResultRecord]:
        try:
            return records.read()
        except OSError as error:
            # Unreadable records only cost a run; they must never stop a check.
            self._boundaries.log.line(f"known results: cannot read the records: {error}")
            return []

    def _reuse(
        self, records: RecordLog[ResultRecord], key: ResultKey, known: ResultRecord
    ) -> CheckResult:
        reuse = ResultRecord(
            key=key,
            at=self._boundaries.clock.now(),
            status="passed",
            last_line=known.last_line,
            duration_seconds=0,
            reused=known.at,
        )
        self._append(records, reuse)
        return CheckResult(
            command=key.command,
            status="passed",
            exit_status=0,
            duration=timedelta(0),
            last_line=known.last_line,
            output_tail="",
            targets=[],
            reused=ReusedRun(tree=key.tree, at=known.at),
        )

    def _append(self, records: RecordLog[ResultRecord], record: ResultRecord) -> None:
        try:
            records.append(record)
        except OSError as error:
            # The record is telemetry: losing it must never lose the command's result.
            self._boundaries.log.line(
                f"known results: cannot write the record of {record.key.command}: {error}"
            )
