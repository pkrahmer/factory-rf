"""A failed machine keeps the stop of a red main across commits that only record stops."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

import preflight_support
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.preflight import PreflightStamp
from factory.domain.stops import StopRecord, stop_records_text
from log_support import log_lines
from preflight_support import CLEARED_LINE, IMAGE, OTHER_IMAGE, Rig, fail_once

rig = preflight_support.rig
red_main = preflight_support.red_main
failed_once = preflight_support.failed_once

AT = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
FIRST = StopRecord(event="raised", scope="repository", reason="fetch_failed", at=AT)
SECOND = StopRecord(
    event="cleared", scope="repository", reason="fetch_failed", at=AT.replace(minute=1)
)


def _logged_cleared(tmp_path: Path) -> bool:
    return any(line.endswith(CLEARED_LINE) for line in log_lines(tmp_path))


def _one_stops_commit(rig: Rig) -> None:
    rig.push_main(STOP_RECORDS_FILE, stop_records_text([FIRST]))


def _two_stops_commits(rig: Rig) -> None:
    rig.push_main(STOP_RECORDS_FILE, stop_records_text([FIRST]))
    rig.push_main(STOP_RECORDS_FILE, stop_records_text([FIRST, SECOND]))


def _stops_and_other_file(rig: Rig) -> None:
    rig.human.push_files(
        "main", {STOP_RECORDS_FILE: stop_records_text([FIRST]), "README.md": "moved\n"}
    )


def _other_file_only(rig: Rig) -> None:
    rig.push_main("README.md", "moved\n")


def _move_main(rig: Rig, move: Callable[[Rig], None]) -> None:
    move(rig)
    # As the tick's restore leaves it before the preflight runs: on main at the remote's commit.
    rig.checkout.fetch()
    rig.checkout.checkout("main", start_point="origin/main")
    rig.checkout.reset_to("origin/main")


@pytest.fixture
def failed_once_recording(red_main: Rig, records: JsonLinesRecordLog[StopRecord]) -> Rig:
    """Return the rig with the stop records after one probe of its red main."""
    red_main.boundaries = replace(red_main.boundaries, stop_records=records)
    return fail_once(red_main)


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
    del failed_once.which.paths["uv"]

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
    del failed_once_recording.which.paths["uv"]

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
    del failed_once.which.paths["uv"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert "main_branch_failing" not in failed_once.reasons()
    assert _logged_cleared(tmp_path)
