"""The cost record of a run that died is the same whatever text the run died with."""

from datetime import UTC, datetime, timedelta

from factory.agents.domain.agent_runs import AgentRunResult
from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.cost_records import CostRecord

SIDECAR = "F0001-S0001-first.costs.jsonl"


def test_a_died_run_s_text_leaves_its_cost_record_as_it_was(boundaries: Boundaries) -> None:
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
    without = AgentRunResult(end_reason="died", duration=timedelta(seconds=60))
    with_text = AgentRunResult(
        end_reason="died",
        duration=timedelta(seconds=60),
        died_text="You've hit your limit · resets 12am",
    )
    recorder = CostRecorder(boundaries)

    plain = recorder.complete(run, without)
    plain_file = (boundaries.checkout / SIDECAR).read_text(encoding="utf-8")
    quoted = recorder.complete(run, with_text)
    quoted_file = (boundaries.checkout / SIDECAR).read_text(encoding="utf-8")

    assert quoted.records == plain.records
    assert quoted_file == plain_file
