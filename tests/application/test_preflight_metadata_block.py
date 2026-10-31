"""The preflight item `metadata-block`: a container must not reach the metadata server."""

from dataclasses import replace
from datetime import timedelta

import pytest

import preflight_support
from factory.application.preflight import MachineChecks, Preflight, metadata_block_item
from factory.application.stops import StopService
from factory.domain.containers import ContainerResult
from factory.domain.errors import ContainerError
from preflight_support import IMAGE, Rig

rig = preflight_support.rig

REACHED = (
    "a container reached the metadata server (HTTP {code}); "
    "reject tcp port 80 to 169.254.169.254 in the job's firewall"
)
TIMED_OUT = "the metadata probe did not end within its limit"


def _ended(output: str, exit_status: int) -> ContainerResult:
    return ContainerResult(
        exit_status=exit_status, output=output, timed_out=False, duration=timedelta(seconds=1)
    )


def _timed_out(output: str) -> ContainerResult:
    return ContainerResult(
        exit_status=None, output=output, timed_out=True, duration=timedelta(seconds=30)
    )


@pytest.mark.parametrize(
    ("result", "passed", "detail"),
    [
        pytest.param(_ended("000", 7), True, "refused", id="refused"),
        pytest.param(_ended("000", 28), True, "refused", id="curl-timed-out"),
        pytest.param(_ended("200", 0), False, REACHED.format(code=200), id="http-200"),
        pytest.param(_ended("404", 0), False, REACHED.format(code=404), id="http-404"),
        pytest.param(_ended("x\n000", 7), True, "refused", id="last-line-counts"),
        pytest.param(
            _ended("", 127),
            False,
            "the metadata probe could not tell (exit 127): no output",
            id="no-output",
        ),
        pytest.param(
            _ended("curl: not found", 127),
            False,
            "the metadata probe could not tell (exit 127): curl: not found",
            id="no-curl",
        ),
        pytest.param(_timed_out(""), False, TIMED_OUT, id="timed-out"),
        pytest.param(_timed_out("000"), False, TIMED_OUT, id="timed-out-with-000"),
        pytest.param(_ended("000\n\n", 7), True, "refused", id="trailing-blank-lines"),
        pytest.param(_ended(" 000 ", 7), True, "refused", id="stripped"),
        pytest.param(
            _ended("2000", 0),
            False,
            "the metadata probe could not tell (exit 0): 2000",
            id="four-digits",
        ),
    ],
)
def test_the_metadata_block_item_passes_only_when_the_probe_could_not_connect(
    result: ContainerResult, *, passed: bool, detail: str
) -> None:
    item = metadata_block_item(lambda: result)

    assert item.name == "metadata-block"
    assert item.passed is passed
    assert item.detail == detail


def _cannot_run() -> ContainerResult:
    raise ContainerError("curl", "no such image")


def test_a_probe_that_cannot_run_fails_the_metadata_block_item() -> None:
    item = metadata_block_item(_cannot_run)

    assert item.name == "metadata-block"
    assert not item.passed
    assert item.detail == (
        "cannot run the metadata probe: container command curl failed: no such image"
    )


def test_a_failed_metadata_block_item_stops_the_machine(rig: Rig) -> None:
    boundaries = replace(rig.boundaries, project_commands=rig.commands)
    checks = MachineChecks(
        boundaries,
        rig.settings,
        rig.which,
        [lambda: metadata_block_item(lambda: _ended("200", 0))],
    )
    preflight = Preflight(boundaries, checks, rig.stamps, StopService(boundaries), IMAGE)

    reason = preflight.run()

    assert reason == "preflight_failed"
    stops = rig.stops()
    assert len(stops) == 1
    assert stops[0].scope == "machine"
    assert stops[0].reason == "preflight_failed"
    assert stops[0].detail == f"metadata-block: {REACHED.format(code=200)}"
    assert rig.commands.calls == []
