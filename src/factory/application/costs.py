"""The cost records of agent runs: begun before the run, completed after it, kept in memory."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import CostRecord
from factory.domain.paths import cost_records_path

if TYPE_CHECKING:
    from factory.application.stage import StartedStage


class CostRun(BaseModel):
    """One run's sidecar in memory: its path, the run's id and every record, the run's last."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    run: str
    records: list[CostRecord]


class CostRecorder:
    """Keeps a run's cost record in the sidecar beside its work item, uncommitted."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read and write the sidecar in the checkout of `boundaries`."""
        self._boundaries = boundaries

    def begin(self, started: StartedStage, role: str) -> CostRun:
        """Add a started record for a run of `role` in `started` and write the sidecar."""
        path = cost_records_path(started.path)
        earlier = self._boundaries.cost_reader.read(self._boundaries.checkout / path)
        state = started.document.state
        if state is None:
            raise ValueError(f"the work item {started.work_item} has no state")
        record = CostRecord(
            run=uuid.uuid4().hex,
            work_item=started.work_item,
            stage=started.stage,
            role=role,
            attempt=state.attempts,
            status="started",
            started_at=self._boundaries.clock.now(),
        )
        run = CostRun(path=path, run=record.run, records=[*earlier, record])
        self.write(run)
        return run

    def complete(self, run: CostRun, result: AgentRunResult) -> CostRun:
        """Replace the run's record by its completed one, with what `result` reported, and write."""
        records = [
            _completed(record, result) if record.run == run.run else record
            for record in run.records
        ]
        completed = run.model_copy(update={"records": records})
        self.write(completed)
        return completed

    def write(self, run: CostRun) -> None:
        """Write the records of `run` to its sidecar, replacing whatever the file held."""
        self._boundaries.cost_writer.write(self._boundaries.checkout / run.path, run.records)


def _completed(record: CostRecord, result: AgentRunResult) -> CostRecord:
    # Copied as reported: an unknown measure stays None and a reported zero stays zero (R24).
    return CostRecord.model_validate(
        {
            **record.model_dump(),
            "status": "completed",
            "duration_seconds": result.duration.total_seconds(),
            "end_reason": result.end_reason,
            "turns": result.turns,
            "tokens": result.tokens,
            "cost_usd": result.cost_usd,
        }
    )
