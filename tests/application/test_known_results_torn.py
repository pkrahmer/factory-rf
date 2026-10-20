"""A torn last line of the known-results log neither stops a check nor is logged."""

from collections.abc import Callable
from pathlib import Path

import pytest

from application.test_known_results import TIME_LIMIT, Rig, _answering, _result, _rig
from factory.adapters.clock import ManualClock
from factory.application.boundaries import Boundaries
from torn_record_support import result_record, torn_inside

TORN = torn_inside(result_record("x é"), "é", 1)


def _append_torn(tmp_path: Path) -> None:
    path = tmp_path / "state" / "records" / "known-results.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as file:
        file.write(TORN)


def _after_a_pass(rig: Rig) -> None:
    known = rig.known()
    known.run("check")
    _append_torn(rig.tmp_path)
    second = known.run("check")
    assert second.reused is not None
    assert second.last_line == "check: green"


def _only_a_torn_line(rig: Rig) -> None:
    _append_torn(rig.tmp_path)
    returned = rig.known().run("check")
    assert returned == _result("check", 0)


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(_after_a_pass, id="after-a-pass"),
        pytest.param(_only_a_torn_line, id="only-a-torn-line"),
    ],
)
def test_a_torn_last_line_of_the_known_results_neither_raises_nor_logs(
    boundaries: Boundaries,
    tmp_path: Path,
    clock: ManualClock,
    scenario: Callable[[Rig], None],
) -> None:
    rig = _rig(boundaries, tmp_path, _answering(clock))

    scenario(rig)

    assert rig.commands.calls == [("check", TIME_LIMIT)]
    assert rig.log_lines() == []
