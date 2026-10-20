"""A record line a kill cut, or one that is not UTF-8, is skipped; the others still count."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.domain.known_results import ResultRecord
from torn_record_support import line_of, result_record, torn_inside


@pytest.fixture
def path(tmp_path: Path) -> Path:
    """The path of the known-results log under test."""
    return tmp_path / "known-results.jsonl"


@pytest.fixture
def log(path: Path) -> JsonLinesRecordLog[ResultRecord]:
    """A record log of `ResultRecord`s at `path`."""
    return JsonLinesRecordLog(path, ResultRecord)


WHOLE = [result_record("check: green é"), result_record("lint: green ✓")]


def _ascii_cut() -> bytes:
    line = line_of(result_record("x é"))
    marker = b'"last_line":"x'
    return line[: line.index(marker) + len(marker)]


@pytest.mark.parametrize(
    ("whole", "torn"),
    [
        pytest.param(WHOLE, torn_inside(result_record("x é"), "é", 1), id="e-acute-1-of-2"),
        pytest.param(WHOLE, torn_inside(result_record("x €"), "€", 1), id="euro-1-of-3"),
        pytest.param(WHOLE, torn_inside(result_record("x €"), "€", 2), id="euro-2-of-3"),
        pytest.param(WHOLE, torn_inside(result_record("x 😀"), "😀", 3), id="emoji-3-of-4"),
        pytest.param(WHOLE, _ascii_cut(), id="ascii"),
        pytest.param([], torn_inside(result_record("x é"), "é", 1), id="only-torn"),
    ],
)
def test_a_torn_last_line_is_skipped_and_the_whole_lines_before_it_count(
    path: Path,
    log: JsonLinesRecordLog[ResultRecord],
    whole: list[ResultRecord],
    torn: bytes,
) -> None:
    path.write_bytes(b"".join(line_of(record) + b"\n" for record in whole) + torn)

    assert log.read() == whole


A = result_record("a é")
B = result_record("b ✓")
C = result_record("c 😀")


def _invalid_inside_b(line: bytes) -> bytes:
    marker = b'"last_line":"b'
    at = line.index(marker) + len(marker)
    return line[:at] + b"\xc3\x28" + line[at:]


def _unchanged(line: bytes) -> bytes:
    return line


def _prefixed(line: bytes) -> bytes:
    return b"\xff" + line


def _lines(
    a: Callable[[bytes], bytes] = _unchanged,
    b: Callable[[bytes], bytes] = _unchanged,
    between: bytes = b"",
) -> bytes:
    return a(line_of(A)) + b"\n" + between + b(line_of(B)) + b"\n" + line_of(C) + b"\n"


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(_lines(), [A, B, C], id="unchanged"),
        pytest.param(_lines(b=_prefixed), [A, C], id="ff-before-b"),
        pytest.param(_lines(b=_invalid_inside_b), [A, C], id="c3-28-inside-b"),
        pytest.param(_lines(a=_prefixed), [B, C], id="ff-before-a"),
        pytest.param(_lines(between=b"\n"), [A, B, C], id="empty-line"),
    ],
)
def test_a_line_that_does_not_decode_is_skipped_wherever_it_stands(
    path: Path,
    log: JsonLinesRecordLog[ResultRecord],
    content: bytes,
    expected: list[ResultRecord],
) -> None:
    path.write_bytes(content)

    assert log.read() == expected


def _appended(log: JsonLinesRecordLog[ResultRecord], _path: Path, record: ResultRecord) -> None:
    log.append(record)


def _written_with_crlf(
    _log: JsonLinesRecordLog[ResultRecord], path: Path, record: ResultRecord
) -> None:
    path.write_bytes(line_of(record) + b"\r\n")


@pytest.mark.parametrize(
    ("last_line", "write"),
    [
        pytest.param("before\u2028after", _appended, id="u2028"),
        pytest.param("before\u2029after", _appended, id="u2029"),
        pytest.param("before\u0085after", _appended, id="u0085"),
        pytest.param("plain", _written_with_crlf, id="crlf"),
    ],
)
def test_a_record_holding_a_line_break_other_than_a_line_feed_reads_back_whole(
    path: Path,
    log: JsonLinesRecordLog[ResultRecord],
    last_line: str,
    write: Callable[[JsonLinesRecordLog[ResultRecord], Path, ResultRecord], None],
) -> None:
    record = result_record(last_line)

    write(log, path, record)

    assert path.read_bytes().count(b"\n") == 1
    assert log.read() == [record]


@pytest.mark.parametrize("directory", [True, False], ids=["directory", "no-file"])
def test_an_error_of_reading_propagates_and_a_missing_file_reads_empty(
    path: Path, log: JsonLinesRecordLog[ResultRecord], *, directory: bool
) -> None:
    if directory:
        path.mkdir()
        with pytest.raises(IsADirectoryError):
            log.read()
    else:
        assert log.read() == []
