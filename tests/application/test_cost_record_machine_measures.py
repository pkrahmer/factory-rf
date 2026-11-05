"""The completed cost record carries the machine's measures, each `None` when it cannot be read."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cost_image_support import _launch
from disk_support import FakeDiskSpace
from factory.agents.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.agents.domain.agent_runs import AgentRunResult
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.cost_records import CostRecord, MachineMeasures
from factory.domain.machine import MachineTotals
from human_clone import HumanClone
from machine_readings_support import FakeMachineReadings

SIDECAR = "F0001-S0001-first.costs.jsonl"
STARTED = CostRecord(
    run="a" * 32,
    work_item="F0001-S0001",
    stage="doing",
    role="coder",
    attempt=0,
    status="started",
    started_at=datetime(2026, 11, 4, 9, 0, tzinfo=UTC),
)
RESULT = AgentRunResult(
    end_reason="completed",
    duration=timedelta(seconds=60),
    decision="review",
    entry="done",
)
GROWN = MachineTotals(cpu_seconds=160.5, cpu_wait_seconds=2.5, memory_wait_seconds=4.0)
AT_START = MachineTotals(cpu_seconds=100.0, cpu_wait_seconds=2.0, memory_wait_seconds=1.0)


class _GrowingReadings(FakeMachineReadings):
    """Answers `AT_START` at the first reading of the totals and `GROWN` at every later one."""

    def __init__(self) -> None:
        super().__init__(GROWN, 8_100_000_000, 16_000_000_000)
        self.readings = 0

    def totals(self) -> MachineTotals:
        self.readings += 1
        return AT_START if self.readings == 1 else GROWN


def _complete(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    store_free: int | OSError,
    dataset_free: int | OSError,
    machine: FakeMachineReadings,
    base_image_bytes: int | None,
    project_layer_bytes: int | None,
) -> CostRecord:
    store = tmp_path / "storage"
    workspace = tmp_path / "workspace"
    used = replace(
        boundaries,
        settings=boundaries.settings.model_copy(update={"workspace": workspace}),
        disk=FakeDiskSpace(free={store: store_free, workspace: dataset_free}),
        machine=machine,
        image_store=store,
        base_image_bytes=base_image_bytes,
        project_layer_bytes=project_layer_bytes,
    )
    run = CostRun(path=SIDECAR, run=STARTED.run, records=[STARTED])

    CostRecorder(used).complete(run, RESULT)

    return boundaries.cost_reader.read(boundaries.checkout / SIDECAR)[-1]


def test_a_completed_record_carries_what_the_machine_gives(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    record = _complete(
        boundaries,
        tmp_path,
        store_free=40_000_000_000,
        dataset_free=9_000_000_000,
        machine=FakeMachineReadings(GROWN, 8_100_000_000, 16_000_000_000),
        base_image_bytes=1_580_000_000,
        project_layer_bytes=420_000_000,
    )

    # The run's record was begun before any start reading, so the differences are unknown.
    assert record.machine == MachineMeasures(
        base_image_bytes=1_580_000_000,
        project_layer_bytes=420_000_000,
        store_free_bytes=40_000_000_000,
        dataset_free_bytes=9_000_000_000,
        memory_peak_since_boot_bytes=8_100_000_000,
        memory_total_bytes=16_000_000_000,
        cpu_seconds=None,
        cpu_wait_seconds=None,
        memory_wait_seconds=None,
    )


@pytest.mark.parametrize(
    ("store_free", "dataset_free", "field"),
    [
        pytest.param(OSError("unreadable"), 9_000_000_000, "store_free_bytes", id="store"),
        pytest.param(40_000_000_000, OSError("unreadable"), "dataset_free_bytes", id="dataset"),
    ],
)
def test_a_file_system_that_cannot_be_read_gives_none(
    boundaries: Boundaries,
    tmp_path: Path,
    store_free: int | OSError,
    dataset_free: int | OSError,
    field: str,
) -> None:
    record = _complete(
        boundaries,
        tmp_path,
        store_free=store_free,
        dataset_free=dataset_free,
        machine=FakeMachineReadings(GROWN, 8_100_000_000, 16_000_000_000),
        base_image_bytes=1_580_000_000,
        project_layer_bytes=0,
    )

    assert record.machine is not None
    assert getattr(record.machine, field) is None
    assert record.machine.memory_peak_since_boot_bytes == 8_100_000_000


def test_a_machine_that_gives_nothing_gives_a_null_machine(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    record = _complete(
        boundaries,
        tmp_path,
        store_free=OSError("unreadable"),
        dataset_free=OSError("unreadable"),
        machine=FakeMachineReadings(),
        base_image_bytes=None,
        project_layer_bytes=None,
    )

    assert record.machine is None
    written = (boundaries.checkout / SIDECAR).read_text(encoding="utf-8").splitlines()
    assert '"machine":null' in written[-1]


def test_a_record_begun_and_completed_holds_the_growth_of_the_totals(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
) -> None:
    launched = _launch(boundaries, human, agent_home, agent_runtime)
    machine = _GrowingReadings()
    recorder = CostRecorder(replace(boundaries, machine=machine))

    begun = recorder.begin(launched.started, "tester")
    recorder.complete(begun, RESULT)

    written = boundaries.cost_reader.read(boundaries.checkout / begun.path)[-1]
    assert written.run == begun.run
    assert written.machine is not None
    assert written.machine.cpu_seconds == pytest.approx(60.5)
    assert written.machine.cpu_wait_seconds == pytest.approx(0.5)
    assert written.machine.memory_wait_seconds == pytest.approx(3.0)
    assert machine.readings == 2
