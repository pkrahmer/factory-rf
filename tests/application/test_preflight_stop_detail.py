"""A failed probe of main that printed nothing says why; one the factory cut off is not judged."""

from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta

import pytest

import preflight_support
from factory.domain.checks import CheckResult, status_of
from preflight_support import RecordingCommands, Rig

rig = preflight_support.rig


def _ended(exit_status: int, last_line: str = "") -> CheckResult:
    return CheckResult(
        command="lint",
        status=status_of(exit_status),
        exit_status=exit_status,
        duration=timedelta(seconds=4),
        last_line=last_line,
        output_tail=last_line,
    )


def _answering(result: CheckResult) -> Callable[[str, timedelta], CheckResult]:
    return lambda _command, _limit: result


@pytest.mark.parametrize(
    ("result", "ending"),
    [
        pytest.param(_ended(2), "ended with exit status 2", id="exit-status-no-output"),
        pytest.param(_ended(-15), "ended by signal 15", id="signal-15-no-output"),
        pytest.param(_ended(-9), "ended by signal 9", id="signal-9-no-output"),
        pytest.param(_ended(2, " \t "), "ended with exit status 2", id="blank-output"),
    ],
)
def test_a_failed_probe_that_printed_nothing_names_the_command_and_its_ending(
    rig: Rig, *, result: CheckResult, ending: str
) -> None:
    rig.boundaries = replace(rig.boundaries, stop_requested=lambda: False)
    rig.commands = RecordingCommands(_answering(result))

    rig.preflight().run()

    stops = [stop for stop in rig.stops() if stop.reason == "main_branch_failing"]
    assert len(stops) == 1
    assert "lint" in stops[0].detail
    assert stops[0].detail.endswith(f"{ending} and printed nothing on main at {rig.main()[:12]}")


def test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again(rig: Rig) -> None:
    stopping = {"requested": False}

    def cut_off(_command: str, _limit: timedelta) -> CheckResult:
        stopping["requested"] = True
        return _ended(-15)

    rig.boundaries = replace(rig.boundaries, stop_requested=lambda: stopping["requested"])
    rig.commands = RecordingCommands(cut_off)

    rig.preflight().run()

    assert "main_branch_failing" not in rig.reasons()
    stamp = rig.stamps.read()
    assert stamp is None or stamp.main_failed is None

    stopping["requested"] = False
    rig.commands = RecordingCommands(_answering(_ended(0)))

    assert rig.preflight().run() is None
    assert len(rig.commands.calls) == 1
