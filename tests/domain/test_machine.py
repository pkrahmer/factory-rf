"""The machine's readings in text: build warnings, sizes in GB, cgroup totals and the memory."""

import pytest

from factory.domain.machine import (
    MachineTotals,
    count_warnings,
    cpu_usage_seconds,
    gigabytes,
    machine_differences,
    mem_total_bytes,
    pressure_total_seconds,
)

APT_LINE = (
    "update-alternatives: warning: skip creation of /usr/share/man/man1/pager.1.gz because"
    " associated file /usr/share/man/man1/less.1.gz (of link group pager) doesn't exist"
)


@pytest.mark.parametrize(
    ("output", "warnings"),
    [
        pytest.param("STEP 1/2: FROM base\nSTEP 2/2: RUN true\nCOMMIT", 0, id="no-warning"),
        pytest.param("npm warn EBADENGINE Unsupported engine {\nadded 3 packages", 1, id="npm"),
        pytest.param("WARNING: image platform does not match\nCOMMIT", 1, id="podman"),
        pytest.param(f"{APT_LINE}\nCOMMIT", 0, id="apt-update-alternatives"),
        pytest.param("warn: a deprecated option\nCOMMIT", 1, id="lowercase-warn"),
        pytest.param("Warning: the cache is stale\nCOMMIT", 1, id="mixed-case-warning"),
    ],
)
def test_the_warnings_of_a_build_output_are_counted(output: str, warnings: int) -> None:
    assert count_warnings(output) == warnings


@pytest.mark.parametrize(
    ("size", "text"),
    [
        pytest.param(1_580_000_000, "1.58", id="ten-to-the-nine"),
        pytest.param(2_400_000_000, "2.40", id="two-decimals"),
    ],
)
def test_a_size_is_given_in_gigabytes_of_ten_to_the_nine_bytes(size: int, text: str) -> None:
    assert gigabytes(size) == text


PRESSURE = (
    "some avg10=0.00 avg60=0.00 avg300=0.00 total={some}\n"
    "full avg10=0.00 avg60=0.00 avg300=0.00 total=1000000\n"
)


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        pytest.param(PRESSURE.format(some="2500000"), 2.5, id="some-total"),
        pytest.param(PRESSURE.format(some="many"), None, id="not-a-number"),
    ],
)
def test_the_pressure_total_is_the_some_line_in_seconds(text: str, seconds: float | None) -> None:
    assert pressure_total_seconds(text) == seconds


@pytest.mark.parametrize(
    ("usage", "seconds"),
    [
        pytest.param("123500000", 123.5, id="usage"),
        pytest.param("lots", None, id="not-a-number"),
    ],
)
def test_the_cpu_usage_is_the_usage_of_cpu_stat_in_seconds(
    usage: str, seconds: float | None
) -> None:
    text = f"usage_usec {usage}\nuser_usec 100000000\nsystem_usec 23500000\n"

    assert cpu_usage_seconds(text) == seconds


def test_the_memory_total_is_mem_total_in_bytes() -> None:
    meminfo = "MemTotal:       15625000 kB\nMemFree:         2000000 kB\n"

    assert mem_total_bytes(meminfo) == 15_625_000 * 1024


def _totals(cpu: float | None, cpu_wait: float | None, memory_wait: float | None) -> MachineTotals:
    return MachineTotals(
        cpu_seconds=cpu, cpu_wait_seconds=cpu_wait, memory_wait_seconds=memory_wait
    )


NONE = _totals(None, None, None)


@pytest.mark.parametrize(
    ("start", "end", "difference"),
    [
        pytest.param(
            _totals(100.0, 2.0, 1.0), _totals(160.5, 2.5, 4.0), _totals(60.5, 0.5, 3.0), id="grew"
        ),
        pytest.param(None, _totals(160.5, 2.5, 4.0), NONE, id="start-missing"),
        pytest.param(
            _totals(None, 2.0, 1.0),
            _totals(160.5, 2.5, 4.0),
            _totals(None, 0.5, 3.0),
            id="start-total-not-a-number",
        ),
        pytest.param(
            _totals(100.0, 2.0, 1.0),
            _totals(160.5, None, 4.0),
            _totals(60.5, None, 3.0),
            id="end-total-not-a-number",
        ),
        pytest.param(
            _totals(100.0, 2.0, 1.0),
            _totals(40.0, 2.5, 4.0),
            _totals(None, 0.5, 3.0),
            id="total-went-back",
        ),
    ],
)
def test_the_run_s_totals_are_the_end_reading_minus_the_start_reading(
    start: MachineTotals | None, end: MachineTotals, difference: MachineTotals
) -> None:
    assert machine_differences(start, end) == difference
