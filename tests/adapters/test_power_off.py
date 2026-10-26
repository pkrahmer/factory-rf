"""The power-off wrapper: its one command, and each way that command can fail."""

import shlex
import time
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.power_off import SystemctlPowerOff
from factory.adapters.printed_output import no_end_detail
from factory.domain.errors import PowerOffError
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

LIMIT = timedelta(seconds=1)
REFUSAL = "sudo: a password is required"


def _stand_in(folder: Path, body: str) -> Path:
    # Each word on a line of its own, so that the test sees the words, not one joined line.
    words = folder / "words.txt"
    path = folder / "sudo"
    path.write_text(
        f"#!/bin/sh\nprintf '%s\\n' \"$@\" > {shlex.quote(str(words))}\n{body}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


@pytest.mark.parametrize(
    ("body", "time_limit", "detail"),
    [
        pytest.param("exit 0", ROOMY_LIMIT, None, id="exits-zero"),
        pytest.param(
            f"echo '{REFUSAL}' >&2\nexit 1",
            ROOMY_LIMIT,
            lambda detail: detail == REFUSAL,
            id="refused-on-standard-error",
        ),
        pytest.param(
            f"echo '{REFUSAL}'\nexit 1",
            ROOMY_LIMIT,
            lambda detail: REFUSAL in detail,
            id="refused-on-standard-output",
        ),
        pytest.param(
            "printf 'first line\\nsecond line\\n\\n'\nexit 1",
            ROOMY_LIMIT,
            lambda detail: "second line" in detail and "first line" not in detail,
            id="the-last-printed-line",
        ),
        pytest.param(
            "exit 1",
            ROOMY_LIMIT,
            lambda detail: detail == "exit status 1",
            id="nothing-printed",
        ),
        pytest.param(
            None, ROOMY_LIMIT, lambda detail: detail.startswith("cannot start "), id="missing"
        ),
        pytest.param(
            "exec sleep 60",
            LIMIT,
            lambda detail: detail == no_end_detail(LIMIT),
            id="time-limit",
        ),
    ],
)
def test_the_power_off_runs_its_one_command_or_raises_what_failed(
    tmp_path: Path,
    body: str | None,
    time_limit: timedelta,
    detail: Callable[[str], bool] | None,
) -> None:
    program = tmp_path / "no-sudo" if body is None else _stand_in(tmp_path, body)
    power = SystemctlPowerOff(str(program), time_limit=time_limit)

    started = time.monotonic()
    if detail is None:
        power.power_off()
        words = (tmp_path / "words.txt").read_text(encoding="utf-8").splitlines()
        assert words == ["-n", "/usr/bin/systemctl", "poweroff"]
    else:
        with pytest.raises(PowerOffError) as raised:
            power.power_off()
        assert detail(raised.value.detail), raised.value.detail
    assert time.monotonic() - started < ROOMY_BOUND_SECONDS
