"""The wired record logs read back, through themselves, what was appended to them."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.files import RecordLog
from factory.domain.disk import DiskRecord, DiskUse
from factory.domain.known_results import ResultKey, ResultRecord
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL

AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
RESULT_RECORD = ResultRecord(
    key=ResultKey(command="check", tree="a" * 40, definition="b" * 64, image=None),
    at=AT,
    status="passed",
    last_line="check: green",
    duration_seconds=12.5,
)
DISK_RECORD = DiskRecord(
    at=AT,
    occasion="start",
    folders=[DiskUse(path="/work", free_bytes=0, used_bytes=None)],
)

type ReadBack = Callable[[Boundaries], tuple[Sequence[BaseModel], Sequence[BaseModel]]]


def _read_back[R: BaseModel](log: RecordLog[R] | None, record: R) -> tuple[list[R], list[R]]:
    assert log is not None
    before = log.read()
    log.append(record)
    return before, log.read()


@pytest.mark.parametrize(
    ("read_back", "record"),
    [
        pytest.param(
            lambda b: _read_back(b.result_records, RESULT_RECORD),
            RESULT_RECORD,
            id="result_records",
        ),
        pytest.param(
            lambda b: _read_back(b.disk_records, DISK_RECORD), DISK_RECORD, id="disk_records"
        ),
    ],
)
def test_a_wired_record_log_reads_back_what_was_appended_through_it(
    local_settings: InstanceSettings, read_back: ReadBack, record: BaseModel
) -> None:
    boundaries = build_boundaries(local_settings, CREDENTIAL, hosting=FakeHostingService())

    before, after = read_back(boundaries)

    assert list(before) == []
    assert list(after) == [record]
