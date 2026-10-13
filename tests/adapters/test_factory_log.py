"""The factory log writes time-stamped lines to standard output and its file."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.application.machine import Clock

FRACTIONAL = datetime(2026, 10, 12, 12, 0, 7, 987654, tzinfo=UTC)


class _EastClock(Clock):
    """A clock that tells its time two hours east of UTC."""

    def now(self) -> datetime:
        return datetime(2026, 10, 12, 14, 0, 7, 987654, tzinfo=timezone(timedelta(hours=2)))


def test_a_line_is_stamped_with_whole_utc_seconds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = TimestampedFactoryLog(tmp_path / "factory.log", ManualClock(FRACTIONAL))

    log.line("hello")

    assert capsys.readouterr().out == "2026-10-12T12:00:07Z hello\n"


def test_a_clock_east_of_utc_is_stamped_in_utc(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log = TimestampedFactoryLog(tmp_path / "factory.log", _EastClock())

    log.line("hello")

    assert capsys.readouterr().out == "2026-10-12T12:00:07Z hello\n"


def test_lines_are_appended_to_the_file_in_order(
    tmp_path: Path, clock: ManualClock, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "factory.log"
    path.write_text("earlier\n", encoding="utf-8")
    log = TimestampedFactoryLog(path, clock)

    log.line("first")
    clock.advance(timedelta(seconds=5))
    log.line("second")

    assert path.read_bytes().decode("utf-8") == (
        "earlier\n2026-10-12T12:00:00Z first\n2026-10-12T12:00:05Z second\n"
    )
    assert capsys.readouterr().out == ("2026-10-12T12:00:00Z first\n2026-10-12T12:00:05Z second\n")


def test_a_text_of_several_lines_writes_each_with_one_stamp(
    tmp_path: Path, clock: ManualClock, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "factory.log"
    log = TimestampedFactoryLog(path, clock)

    log.line("a\nb")

    expected = "2026-10-12T12:00:00Z a\n2026-10-12T12:00:00Z b\n"
    assert capsys.readouterr().out == expected
    assert path.read_bytes().decode("utf-8") == expected


def test_an_empty_text_and_a_trailing_newline_each_write_one_line(
    tmp_path: Path, clock: ManualClock, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "factory.log"
    log = TimestampedFactoryLog(path, clock)

    log.line("")
    log.line("a\n")

    expected = "2026-10-12T12:00:00Z \n2026-10-12T12:00:00Z a\n"
    assert capsys.readouterr().out == expected
    assert path.read_bytes().decode("utf-8") == expected
