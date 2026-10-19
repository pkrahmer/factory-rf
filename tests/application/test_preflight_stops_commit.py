"""A failed machine keeps the stop of a red main across commits that only record stops."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application import test_preflight_run
from application.test_preflight_run import IMAGE, OTHER_IMAGE, Rig
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.preflight import PreflightStamp
from factory.domain.stops import StopRecord, stop_records_text
from git_support import run_git, write_files

rig = test_preflight_run.rig
red_main = test_preflight_run.red_main

CLEARED_LINE = "stop cleared main_branch_failing"
AT = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
FIRST = StopRecord(event="raised", scope="repository", reason="fetch_failed", at=AT)
SECOND = StopRecord(
    event="cleared", scope="repository", reason="fetch_failed", at=AT.replace(minute=1)
)


def _log_lines(tmp_path: Path) -> list[str]:
    log = tmp_path / "state" / "factory.log"
    return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


def _logged_cleared(tmp_path: Path) -> bool:
    return any(line.endswith(CLEARED_LINE) for line in _log_lines(tmp_path))


def _commit_on_main(rig: Rig, files: dict[str, str]) -> None:
    human = rig.directory / "human"
    run_git(human, "fetch", "-q", "origin")
    run_git(human, "checkout", "-q", "-B", "main", "origin/main")
    write_files(human, files)
    run_git(human, "add", "-A")
    run_git(human, "commit", "-q", "-m", f"write {', '.join(files)}")
    run_git(human, "push", "-q", "origin", "main")


def _one_stops_commit(rig: Rig) -> None:
    _commit_on_main(rig, {STOP_RECORDS_FILE: stop_records_text([FIRST])})


def _two_stops_commits(rig: Rig) -> None:
    _commit_on_main(rig, {STOP_RECORDS_FILE: stop_records_text([FIRST])})
    _commit_on_main(rig, {STOP_RECORDS_FILE: stop_records_text([FIRST, SECOND])})


def _stops_and_other_file(rig: Rig) -> None:
    _commit_on_main(rig, {STOP_RECORDS_FILE: stop_records_text([FIRST]), "README.md": "moved\n"})


def _other_file_only(rig: Rig) -> None:
    _commit_on_main(rig, {"README.md": "moved\n"})


def _move_main(rig: Rig, move: Callable[[Rig], None]) -> None:
    move(rig)
    # As the tick's restore leaves it before the preflight runs: on main at the remote's commit.
    rig.checkout.fetch()
    rig.checkout.checkout("main", start_point="origin/main")
    rig.checkout.reset_to("origin/main")


@pytest.fixture
def records(tmp_path: Path) -> JsonLinesRecordLog[StopRecord]:
    """The stop records in the test's state directory."""
    return JsonLinesRecordLog(tmp_path / "state" / "records" / "stops.jsonl", StopRecord)


def _failed_once(rig: Rig) -> Rig:
    assert rig.preflight(IMAGE).run() == "main_branch_failing"
    stamp = rig.stamps.read()
    assert stamp is not None
    assert stamp.main_failed == rig.main()
    return rig


@pytest.fixture
def failed_once(red_main: Rig) -> Rig:
    """Return the rig after one probe of its red main, the stamp holding `main_failed`."""
    return _failed_once(red_main)


@pytest.fixture
def failed_once_recording(red_main: Rig, records: JsonLinesRecordLog[StopRecord]) -> Rig:
    """Return the rig with the stop records after one probe of its red main."""
    red_main.boundaries = replace(red_main.boundaries, stop_records=records)
    return _failed_once(red_main)


@pytest.mark.parametrize(
    ("move", "stays"),
    [
        pytest.param(_one_stops_commit, True, id="one-stops-commit"),
        pytest.param(_two_stops_commits, True, id="two-stops-commits"),
        pytest.param(_stops_and_other_file, False, id="stops-and-other-file"),
        pytest.param(_other_file_only, False, id="other-file-only"),
    ],
)
def test_a_failed_machine_keeps_the_failing_stop_only_across_stop_records_commits(
    failed_once: Rig, tmp_path: Path, move: Callable[[Rig], None], stays: bool
) -> None:
    _move_main(failed_once, move)
    del failed_once.which.paths["make"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert ("main_branch_failing" in failed_once.reasons()) is stays
    assert _logged_cleared(tmp_path) is not stays


@pytest.mark.parametrize(
    ("move", "cleared"),
    [
        pytest.param(_one_stops_commit, 0, id="one-stops-commit"),
        pytest.param(_stops_and_other_file, 1, id="stops-and-other-file"),
    ],
)
def test_a_kept_failing_stop_appends_no_cleared_record(
    failed_once_recording: Rig,
    records: JsonLinesRecordLog[StopRecord],
    move: Callable[[Rig], None],
    cleared: int,
) -> None:
    before = len(records.read())
    _move_main(failed_once_recording, move)
    del failed_once_recording.which.paths["make"]

    assert failed_once_recording.preflight(OTHER_IMAGE).run() == "preflight_failed"
    appended = [
        record
        for record in records.read()[before:]
        if record.event == "cleared" and record.reason == "main_branch_failing"
    ]
    assert len(appended) == cleared


def test_a_failed_machine_clears_the_stop_when_the_remembered_commit_is_not_in_the_clone(
    failed_once: Rig, tmp_path: Path
) -> None:
    failed_once.stamps.write(PreflightStamp(image=IMAGE, main_failed="a" * 40))
    del failed_once.which.paths["make"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert "main_branch_failing" not in failed_once.reasons()
    assert _logged_cleared(tmp_path)
