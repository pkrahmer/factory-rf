"""The stop publisher pushes the stop records main does not hold yet to main's stop records file."""

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.stops import StopPublisher
from factory.domain.errors import GitError, PushFailed
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.stops import StopRecord, stop_records_text
from git_support import clone, commit_all, remote_commit, run_git
from human_clone import HumanClone

AT = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
FIRST = StopRecord(event="raised", scope="repository", reason="fetch_failed", at=AT)
SECOND = StopRecord(
    event="cleared", scope="repository", reason="fetch_failed", at=AT.replace(minute=1)
)
THIRD = StopRecord(
    event="raised", scope="machine", reason="disk_low", at=AT.replace(minute=2), instance="self"
)
NOT_A_RECORD = "not a record\n"


def _remote_file(remote: Path) -> str | None:
    result = run_process(
        ProcessRequest(argv=["git", "show", f"main:{STOP_RECORDS_FILE}"], cwd=remote)
    )
    return result.stdout if result.exit_status == 0 else None


def _subjects(remote: Path) -> list[str]:
    return run_git(remote, "log", "--format=%s", "main").splitlines()


@pytest.fixture
def publishing(boundaries: Boundaries, records: JsonLinesRecordLog[StopRecord]) -> Boundaries:
    """The test's boundaries with the stop records."""
    return replace(boundaries, stop_records=records)


def _append(records: JsonLinesRecordLog[StopRecord], local: list[StopRecord]) -> None:
    for record in local:
        records.append(record)


def _remove_factory_folder(remote: Path, tmp_path: Path) -> None:
    other = clone(remote, tmp_path / "other")
    run_git(other, "rm", "-r", "-q", "factory")
    commit_all(other, "remove the factory folder")
    run_git(other, "push", "-q", "origin", "main")


@pytest.mark.parametrize("without_factory_folder", [False, True], ids=["no-file", "no-folder"])
def test_the_local_records_reach_a_new_file_on_main_in_local_order(
    publishing: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    *,
    checkout: GitCli,
    remote: Path,
    tmp_path: Path,
    without_factory_folder: bool,
) -> None:
    if without_factory_folder:
        _remove_factory_folder(remote, tmp_path)
        checkout.fetch()
    _append(records, [FIRST, SECOND])

    published = StopPublisher(publishing).publish()

    assert published == [FIRST, SECOND]
    assert _remote_file(remote) == stop_records_text([FIRST, SECOND])
    assert _subjects(remote)[0] == "stops recorded"


@pytest.mark.parametrize(
    ("existing", "local", "expected"),
    [
        pytest.param(
            stop_records_text([FIRST]) + NOT_A_RECORD,
            [FIRST, SECOND, THIRD],
            [SECOND, THIRD],
            id="earlier-lines-kept",
        ),
        pytest.param(
            stop_records_text([FIRST]) + NOT_A_RECORD.rstrip("\n"),
            [FIRST, SECOND, THIRD],
            [SECOND, THIRD],
            id="no-final-newline",
        ),
        pytest.param(
            stop_records_text([FIRST]),
            [FIRST, SECOND, SECOND],
            [SECOND],
            id="local-duplicate",
        ),
    ],
)
def test_only_the_missing_records_are_added_after_the_lines_main_holds(
    publishing: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    *,
    checkout: GitCli,
    remote: Path,
    human: HumanClone,
    existing: str,
    local: list[StopRecord],
    expected: list[StopRecord],
) -> None:
    human.push_file("main", STOP_RECORDS_FILE, existing)
    checkout.fetch()
    _append(records, local)

    published = StopPublisher(publishing).publish()

    assert published == expected
    earlier = existing if existing.endswith("\n") else existing + "\n"
    assert _remote_file(remote) == earlier + stop_records_text(expected)


@pytest.mark.parametrize(
    ("local", "on_main"),
    [
        pytest.param([], None, id="empty-record-log"),
        pytest.param([FIRST, SECOND], [FIRST, SECOND], id="main-holds-every-record"),
    ],
)
def test_nothing_to_publish_makes_no_commit(
    boundaries: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    *,
    checkout: GitCli,
    remote: Path,
    human: HumanClone,
    local: list[StopRecord],
    on_main: list[StopRecord] | None,
) -> None:
    if on_main is not None:
        human.push_file("main", STOP_RECORDS_FILE, stop_records_text(on_main))
        checkout.fetch()
    _append(records, local)
    head = remote_commit(remote, "main")
    publisher = StopPublisher(replace(boundaries, stop_records=records))

    published = publisher.publish()

    assert published == []
    assert remote_commit(remote, "main") == head


def test_a_main_moved_on_after_the_fetch_refuses_the_push_and_the_next_call_publishes_once(
    publishing: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    *,
    checkout: GitCli,
    remote: Path,
    human: HumanClone,
) -> None:
    _append(records, [FIRST, SECOND])
    human.push_file("main", "notes.txt", "pushed after the fetch\n")
    publisher = StopPublisher(publishing)

    with pytest.raises(PushFailed):
        publisher.publish()

    assert "stops recorded" not in _subjects(remote)
    checkout.fetch()
    assert publisher.publish() == [FIRST, SECOND]
    assert _remote_file(remote) == stop_records_text([FIRST, SECOND])
    assert _subjects(remote).count("stops recorded") == 1


def test_a_main_that_does_not_resolve_raises_git_error_and_keeps_the_records(
    publishing: Boundaries,
    records: JsonLinesRecordLog[StopRecord],
    *,
    checkout: GitCli,
    remote: Path,
) -> None:
    _append(records, [FIRST])
    run_git(remote, "update-ref", "-d", "refs/heads/main")
    checkout.fetch()
    assert checkout.resolve("origin/main") is None

    with pytest.raises(GitError):
        StopPublisher(publishing).publish()

    assert records.read() == [FIRST]
