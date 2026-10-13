"""The health status file: written atomically, read back, and healthy when damaged."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.health_file import JsonHealthStatusFile
from factory.domain.stops import HealthStatus, RepositoryStop

AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
STATUS = HealthStatus(
    stops=[
        RepositoryStop(
            scope="repository", reason="main_branch_failing", detail="make check", at=AT
        ),
        RepositoryStop(scope="machine", reason="preflight_failed", detail="uv missing", at=AT),
        RepositoryStop(
            scope="repository", reason="fetch_failed", detail="origin unreachable", at=AT
        ),
    ]
)


def test_the_log_and_the_health_file_create_missing_parent_directories(
    tmp_path: Path, clock: ManualClock
) -> None:
    log_path = tmp_path / "state" / "logs" / "factory.log"
    health_path = tmp_path / "other" / "state" / "health.json"

    TimestampedFactoryLog(log_path, clock).line("hello")
    JsonHealthStatusFile(health_path).write(STATUS)

    assert log_path.read_bytes().decode("utf-8") == "2026-10-12T12:00:00Z hello\n"
    assert JsonHealthStatusFile(health_path).read() == STATUS


def test_a_path_below_a_regular_file_fails_the_write_after_standard_output(
    tmp_path: Path, clock: ManualClock, capsys: pytest.CaptureFixture[str]
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("a file\n", encoding="utf-8")
    log = TimestampedFactoryLog(blocker / "factory.log", clock)
    health = JsonHealthStatusFile(blocker / "health.json")

    with pytest.raises(OSError, match=r"."):
        log.line("hello")
    assert capsys.readouterr().out == "2026-10-12T12:00:00Z hello\n"
    with pytest.raises(OSError, match=r"."):
        health.write(STATUS)


def test_a_written_status_reads_back_equal_in_order(tmp_path: Path) -> None:
    health = JsonHealthStatusFile(tmp_path / "health.json")

    health.write(STATUS)
    status = health.read()

    assert status == STATUS
    assert [stop.reason for stop in status.stops] == [
        "main_branch_failing",
        "preflight_failed",
        "fetch_failed",
    ]


def test_a_missing_file_reads_as_healthy(tmp_path: Path) -> None:
    assert JsonHealthStatusFile(tmp_path / "health.json").read() == HealthStatus()


@pytest.mark.parametrize(
    "content",
    [b"not json", b'{"stops": [], "extra": 1}', b"", b"\xff\xfe", None],
    ids=["not-json", "unknown-field", "empty", "not-utf-8", "directory"],
)
def test_a_damaged_file_reads_as_healthy_and_is_replaced_by_the_next_write(
    tmp_path: Path, content: bytes | None
) -> None:
    path = tmp_path / "health.json"
    if content is None:
        path.mkdir()
    else:
        path.write_bytes(content)
    health = JsonHealthStatusFile(path)

    assert health.read() == HealthStatus()

    if content is not None:
        health.write(STATUS)
        assert health.read() == STATUS


def test_a_write_leaves_only_the_health_file_in_its_directory(tmp_path: Path) -> None:
    directory = tmp_path / "state"
    health = JsonHealthStatusFile(directory / "health.json")

    health.write(HealthStatus())
    health.write(STATUS)

    assert [path.name for path in directory.iterdir()] == ["health.json"]


def test_a_directory_at_the_path_fails_the_write_and_leaves_no_temporary_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "health.json"
    path.mkdir()
    health = JsonHealthStatusFile(path)

    with pytest.raises(OSError, match=r"."):
        health.write(STATUS)

    assert [entry.name for entry in tmp_path.iterdir()] == ["health.json"]
    assert path.is_dir()
