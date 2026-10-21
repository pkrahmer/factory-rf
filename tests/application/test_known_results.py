"""A stage's project command whose passed result is known for the same key is not run again."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from application.test_preflight_run import RecordingCommands
from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.files import RecordLog
from factory.application.known_results import KnownResults
from factory.domain.checks import CheckResult, ReusedRun, status_of
from factory.domain.errors import GitError, ProjectCommandError
from factory.domain.git import TreeId
from factory.domain.known_results import ResultKey, ResultRecord, definition_digest
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import InstanceSettings
from git_support import PIPELINE_YAML
from human_clone import HumanClone
from log_support import log_lines
from project_command_support import raising
from record_support import UnwritableRecordLog

NOT_READ = ["docs/*"]
DEFINITION_YAML = PIPELINE_YAML.replace(
    "check: {time_limit: 10}", 'check: {time_limit: 10, not_read: ["docs/*"]}'
)
OTHER_LINT_YAML = DEFINITION_YAML.replace("lint: {time_limit: 5}", "lint: {time_limit: 6}")
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


class KeylessGit(GitCli):
    """A checkout whose tree cannot be computed."""

    @override
    def work_tree_id(self, left_out: Sequence[str] = ()) -> TreeId:
        raise GitError("git write-tree", 128, "fatal: index file corrupt")


class UnreadableRecordLog(RecordLog[ResultRecord]):
    """Raises `OSError("unreadable")` on every `read`; appends to `inner`."""

    def __init__(self, inner: RecordLog[ResultRecord]) -> None:
        self._inner = inner

    @override
    def append(self, record: ResultRecord) -> None:
        self._inner.append(record)

    @override
    def read(self) -> list[ResultRecord]:
        raise OSError("unreadable")


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


def test_a_first_run_is_recorded_under_its_key_at_the_time_before_it(
    boundaries: Boundaries, tmp_path: Path, clock: ManualClock, checkout: GitCli
) -> None:
    rig = _rig(boundaries, tmp_path, _answering(clock))
    before = clock.now()

    returned = rig.known().run("check")

    assert rig.commands.calls == [("check", TIME_LIMIT)]
    assert returned == _result("check", 0)
    assert rig.records.read() == [
        ResultRecord(
            key=ResultKey(
                command="check",
                tree=checkout.work_tree_id(NOT_READ),
                definition=definition_digest(rig.definition),
                image=None,
            ),
            at=before,
            status="passed",
            last_line="check: green",
            duration_seconds=42.5,
            reused=None,
        )
    ]


def test_a_second_run_on_the_same_input_takes_the_known_result(
    boundaries: Boundaries, tmp_path: Path, clock: ManualClock
) -> None:
    rig = _rig(boundaries, tmp_path, _answering(clock))
    known = rig.known()
    known.run("check")
    clock.advance(timedelta(minutes=5))

    second = known.run("check")

    [first, reuse] = rig.records.read()
    assert rig.commands.calls == [("check", TIME_LIMIT)]
    assert second == CheckResult(
        command="check",
        status="passed",
        exit_status=0,
        duration=timedelta(0),
        last_line="check: green",
        output_tail="",
        targets=[],
        reused=ReusedRun(tree=first.key.tree, at=first.at),
    )
    assert reuse == ResultRecord(
        key=first.key,
        at=clock.now(),
        status="passed",
        last_line="check: green",
        duration_seconds=0,
        reused=first.at,
    )


@dataclass(frozen=True)
class Between:
    """What happens between a first and a second run, and which command each run is."""

    change: Callable[[Rig, HumanClone], KnownResults | None] = lambda _rig, _human: None
    first_exit: int | None = 0
    second_command: str = "check"


def _write(path: str) -> Callable[[Rig, HumanClone], None]:
    def change(rig: Rig, _human: HumanClone) -> None:
        target = rig.boundaries.checkout / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("changed\n", encoding="utf-8")

    return change


def _merged(path: str) -> Callable[[Rig, HumanClone], None]:
    def change(rig: Rig, human: HumanClone) -> None:
        human.push_file("main", path, "news\n")
        rig.boundaries.git.fetch()
        rig.boundaries.git.merge("origin/main")

    return change


def _other_lint_limit(rig: Rig, _human: HumanClone) -> KnownResults:
    definition = rig.boundaries.pipeline_reader.parse(OTHER_LINT_YAML)
    return KnownResults(rig.boundaries, definition)


def _new_image(rig: Rig, _human: HumanClone) -> KnownResults:
    settings = rig.boundaries.settings
    assert settings is not None
    updated = replace(rig.boundaries, settings=settings.model_copy(update={"image": "img-2"}))
    return KnownResults(updated, rig.definition)


@pytest.mark.parametrize(
    ("between", "reused"),
    [
        pytest.param(Between(change=_write("docs/guide.md")), True, id="edit-not-read"),
        pytest.param(Between(change=_write("src/a.py")), False, id="edit-read"),
        pytest.param(Between(change=_merged("docs/news.md")), True, id="merge-not-read"),
        pytest.param(Between(change=_merged("src/b.py")), False, id="merge-read"),
        pytest.param(Between(change=_other_lint_limit), False, id="definition"),
        pytest.param(Between(change=_new_image), False, id="image"),
        pytest.param(Between(first_exit=2), False, id="first-failed"),
        pytest.param(Between(first_exit=None), False, id="first-time-limit"),
        pytest.param(Between(second_command="lint"), False, id="other-command"),
    ],
)
def test_only_a_change_of_what_the_command_reads_gives_a_new_key(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    clock: ManualClock,
    human: HumanClone,
    local_settings: InstanceSettings,
    between: Between,
    reused: bool,
) -> None:
    settings = local_settings.model_copy(update={"image": "img-1"})
    rig = _rig(
        replace(boundaries, settings=settings), tmp_path, _answering(clock, [between.first_exit])
    )
    known = rig.known()
    known.run("check")

    second = between.change(rig, human) or known
    second.run(between.second_command)

    [first, record] = rig.records.read()
    assert (len(rig.commands.calls) == 1) is reused
    assert record.reused == (first.at if reused else None)


@pytest.mark.parametrize(
    ("fault", "logged", "recorded"),
    [
        pytest.param("no-key", "known results: no key for check: ", 0, id="git-error"),
        pytest.param(
            "unwritable",
            "known results: cannot write the record of check: disk full",
            0,
            id="append-error",
        ),
        pytest.param(
            "unreadable",
            "known results: cannot read the records: unreadable",
            1,
            id="read-error",
        ),
    ],
)
def test_a_fault_of_the_key_or_the_records_runs_the_command_and_is_logged(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    clock: ManualClock,
    fault: str,
    logged: str,
    recorded: int,
) -> None:
    rig = _rig(boundaries, tmp_path, _answering(clock))
    faulty = rig.boundaries
    if fault == "no-key":
        faulty = replace(faulty, git=KeylessGit(faulty.checkout))
    elif fault == "unwritable":
        unwritable: UnwritableRecordLog[ResultRecord] = UnwritableRecordLog(OSError("disk full"))
        faulty = replace(faulty, result_records=unwritable)
    else:
        faulty = replace(faulty, result_records=UnreadableRecordLog(rig.records))

    returned = KnownResults(faulty, rig.definition).run("check")

    assert returned == _result("check", 0)
    assert rig.commands.calls == [("check", TIME_LIMIT)]
    assert len(rig.records.read()) == recorded
    [line] = rig.log_lines()
    assert line.startswith(logged)
    if fault != "no-key":
        assert line == logged


@pytest.mark.parametrize(
    "error",
    [ProjectCommandError("check", "make not found"), ValueError("time_limit must be positive")],
    ids=["cannot-start", "no-time-limit"],
)
def test_an_error_of_the_inner_run_propagates_and_records_nothing(
    boundaries: Boundaries, tmp_path: Path, error: Exception
) -> None:
    rig = _rig(boundaries, tmp_path, raising(error))

    with pytest.raises(type(error)):
        rig.known().run("check")

    assert rig.records.read() == []
