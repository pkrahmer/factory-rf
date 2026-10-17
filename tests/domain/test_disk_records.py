"""The disk record: one moment's use of the instance's folders, and its factory log line."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from factory.domain.disk import DiskRecord, DiskUse, disk_line

AT = datetime(2026, 10, 17, 6, 0, tzinfo=UTC)


def _record(**changes: object) -> dict[str, object]:
    folder = {"path": "/work", "free_bytes": 1, "used_bytes": 1}
    return {"at": AT, "occasion": "start", "folders": [folder], **changes}


def test_the_disk_line_names_each_folder_in_gigabytes_or_unknown() -> None:
    record = DiskRecord(
        at=AT,
        occasion="start",
        folders=[
            DiskUse(path="/work", free_bytes=812_345_678_901, used_bytes=700_000_000),
            DiskUse(path="/state", free_bytes=None, used_bytes=1_000),
        ],
    )

    assert disk_line(record) == (
        "disk start: /work 812.3 GB free, 0.7 GB used; /state unknown free, 0.0 GB used"
    )


@pytest.mark.parametrize(
    ("data", "valid"),
    [
        pytest.param(_record(occasion="end"), False, id="other-occasion"),
        pytest.param(_record(occasion="acceptance"), True, id="acceptance"),
        pytest.param(_record(at=datetime(2026, 10, 17, 6, 0)), False, id="naive-at"),  # noqa: DTZ001
        pytest.param(
            _record(folders=[{"path": "/w", "free_bytes": -1, "used_bytes": 0}]),
            False,
            id="free-minus-one",
        ),
        pytest.param(
            _record(folders=[{"path": "/w", "free_bytes": 0, "used_bytes": -1}]),
            False,
            id="used-minus-one",
        ),
        pytest.param(
            _record(folders=[{"path": "/w", "free_bytes": None, "used_bytes": None}]),
            True,
            id="both-none",
        ),
        pytest.param(
            _record(folders=[{"path": "/w", "free_bytes": 0, "used_bytes": 0}]),
            True,
            id="both-zero",
        ),
    ],
)
def test_a_disk_record_refuses_an_unknown_occasion_a_naive_time_and_negative_bytes(
    data: dict[str, object], *, valid: bool
) -> None:
    if valid:
        DiskRecord.model_validate(data)
    else:
        with pytest.raises(ValidationError):
            DiskRecord.model_validate(data)
