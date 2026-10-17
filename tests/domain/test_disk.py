"""The low-disk fault: free bytes in gigabytes and the paths with too little room."""

from pathlib import Path

import pytest

from factory.domain.disk import GIGABYTE, disk_low_detail, gigabytes


@pytest.mark.parametrize(
    ("byte_count", "expected"),
    [
        (0, "0.0"),
        (999_999_999, "0.9"),
        (1_000_000_000, "1.0"),
        (3_299_999_999, "3.2"),
        (812_345_678_901, "812.3"),
    ],
)
def test_gigabytes_are_rounded_down_to_one_decimal(byte_count: int, expected: str) -> None:
    assert gigabytes(byte_count) == expected


WORK = Path("/work")
STATE = Path("/state")
WORK_LOW = "/work has 4.9 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for"


@pytest.mark.parametrize(
    ("free", "expected"),
    [
        ({WORK: 5 * GIGABYTE}, None),
        ({WORK: 5 * GIGABYTE - 1}, WORK_LOW),
        (
            {WORK: 1_200_000_000, STATE: 1_200_000_000},
            "/work has 1.2 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for; "
            "/state has 1.2 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for",
        ),
        ({WORK: 5 * GIGABYTE - 1, STATE: 6 * GIGABYTE}, WORK_LOW),
    ],
    ids=["exactly-the-minimum", "one-byte-below", "both-low-in-order", "one-low"],
)
def test_the_disk_low_detail_names_each_path_below_the_minimum(
    free: dict[Path, int], expected: str | None
) -> None:
    assert disk_low_detail(free, 5) == expected
