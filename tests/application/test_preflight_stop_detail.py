"""A failed probe of main that printed nothing says why; one the factory cut off is not judged."""

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import timedelta

import pytest

import preflight_support
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.application.dispatcher import Handler
from factory.application.handlers.run import RunHandler
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.checks import CheckResult, status_of
from factory.domain.events import EventKind
from factory.domain.pipeline_definition import PipelineDefinition
from factory.hosting.adapters.fake_hosting import FakeHostingService
from preflight_support import RecordingCommands, Rig
from stage_run_support import INSTANCE

rig = preflight_support.rig

BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"


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


def test_a_tick_whose_probe_the_factorys_stop_cut_off_dispatches_nothing(
    rig: Rig, agent_runtime: FakeAgentRuntime, hosting: FakeHostingService
) -> None:
    stopping = {"requested": False}

    def cut_off(_command: str, _limit: timedelta) -> CheckResult:
        stopping["requested"] = True
        return _ended(-15)

    rig.boundaries = replace(rig.boundaries, stop_requested=lambda: stopping["requested"])
    rig.commands = RecordingCommands(cut_off)
    rig.human.start(BACKLOG_PATH)
    boundaries = rig.boundaries

    def handlers(definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
        return {
            "idle": IdleHandler(),
            "run": RunHandler(boundaries, INSTANCE, definition, {}),
        }

    outcome = Tick(boundaries, INSTANCE, handlers, preflight=rig.preflight()).run()

    assert len(rig.commands.calls) == 1
    assert outcome == TickOutcome()
    assert "main_branch_failing" not in rig.reasons()
    assert agent_runtime.requests() == []
    assert hosting.pull_requests() == []
