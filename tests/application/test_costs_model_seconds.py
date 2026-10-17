"""The completed cost record carries the run's model time in seconds, or leaves it unknown."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import CostRecord

SIDECAR = "F0001-S0001-first.costs.jsonl"


@pytest.mark.parametrize(
    ("model_duration", "expected"),
    [(timedelta(seconds=41.5), 41.5), (None, None)],
    ids=["known", "unknown"],
)
def test_completed_record_copies_the_model_duration_in_seconds(
    boundaries: Boundaries, model_duration: timedelta | None, expected: float | None
) -> None:
    started = CostRecord(
        run="a" * 32,
        work_item="F0001-S0001",
        stage="doing",
        role="coder",
        attempt=0,
        status="started",
        started_at=datetime(2026, 10, 17, 9, 0, tzinfo=UTC),
    )
    run = CostRun(path=SIDECAR, run=started.run, records=[started])
    result = AgentRunResult(
        end_reason="completed",
        decision="review",
        entry="Done.",
        duration=timedelta(seconds=60),
        model_duration=model_duration,
    )

    completed = CostRecorder(boundaries).complete(run, result)

    assert completed.records[-1].model_seconds == expected
    written = boundaries.cost_reader.read(boundaries.checkout / SIDECAR)
    assert written[-1].model_seconds == expected
