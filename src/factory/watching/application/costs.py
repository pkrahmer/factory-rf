# SPDX-License-Identifier: Apache-2.0
"""The cost records of agent runs: recorded around each run, and billed from the remote."""

from __future__ import annotations

import uuid
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from factory.agents.domain.agent_runs import AgentRunResult
from factory.hosting.application.git import Git
from factory.machine.application.disk_records import bytes_or_unknown
from factory.pipeline.application.boundaries import Boundaries
from factory.shared.application.files import CostRecordReader
from factory.shared.domain.identifiers import (
    WorkItemId,
    branch_name,
    parse_work_item_file_name,
    work_item_of_branch,
    work_item_order,
)
from factory.shared.domain.paths import FEATURES_DIRECTORY, MAIN_BRANCH, REMOTE, cost_records_path
from factory.watching.domain.bills import (
    Bill,
    StageBill,
    bill,
    bills_by_stage,
    cost_line,
    cost_table,
)
from factory.watching.domain.cost_records import CostRecord, MachineMeasures, ToolUse, TranscriptRef
from factory.watching.domain.machine import MachineTotals, machine_differences
from factory.work.domain.work_item import require_state

if TYPE_CHECKING:
    from factory.pipeline.application.stage import StartedStage


class CostRun(BaseModel):
    """One run's sidecar in memory: its path, the run's id and every record, the run's last.

    `start_totals` are the machine's running totals when the run began; `None` when unread.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    run: str
    records: list[CostRecord]
    start_totals: MachineTotals | None = None


class CostRecorder:
    """Keeps a run's cost record in the sidecar beside its work item, uncommitted."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read and write the sidecar in the checkout of `boundaries`."""
        self._boundaries = boundaries

    def begin(self, started: StartedStage, role: str) -> CostRun:
        """Add a started record for a run of `role` in `started` and write the sidecar."""
        path = cost_records_path(started.path)
        earlier = self._boundaries.cost_reader.read(self._boundaries.checkout / path)
        error = ValueError(f"the work item {started.work_item} has no state")
        state = require_state(started.document, error)
        settings = self._boundaries.settings
        record = CostRecord(
            run=uuid.uuid4().hex,
            work_item=started.work_item,
            stage=started.stage,
            role=role,
            attempt=state.attempts,
            status="started",
            started_at=self._boundaries.clock.now(),
            image=settings.image,
            instance=settings.instance,
        )
        run = CostRun(
            path=path,
            run=record.run,
            records=[*earlier, record],
            start_totals=self._start_totals(),
        )
        self.write(run)
        return run

    def complete(
        self,
        run: CostRun,
        result: AgentRunResult,
        transcript: TranscriptRef | None = None,
        *,
        tools: list[ToolUse] | None = None,
    ) -> CostRun:
        """Replace the run's record by its completed one, with what `result` reported, and write.

        The completed record names `transcript`, the run's kept transcript, when there is one,
        and carries `tools`, the run's tool calls summed up, `None` when they were not read.
        """
        machine = self._machine_measures(run.start_totals)
        records = [
            _completed(record, result, machine, transcript, tools)
            if record.run == run.run
            else record
            for record in run.records
        ]
        completed = run.model_copy(update={"records": records})
        self.write(completed)
        return completed

    def write(self, run: CostRun) -> None:
        """Write the records of `run` to its sidecar, replacing whatever the file held."""
        self._boundaries.cost_writer.write(self._boundaries.checkout / run.path, run.records)

    def _start_totals(self) -> MachineTotals | None:
        machine = self._boundaries.machine
        return None if machine is None else machine.totals()

    def _machine_measures(self, start_totals: MachineTotals | None) -> MachineMeasures | None:
        boundaries = self._boundaries
        machine = boundaries.machine
        totals = None if machine is None else machine_differences(start_totals, machine.totals())
        measures = MachineMeasures(
            base_image_bytes=boundaries.base_image_bytes,
            project_layer_bytes=boundaries.project_layer_bytes,
            store_free_bytes=self._free_bytes(boundaries.image_store),
            dataset_free_bytes=self._free_bytes(boundaries.settings.workspace),
            memory_peak_since_boot_bytes=None if machine is None else machine.memory_peak_bytes(),
            memory_total_bytes=None if machine is None else machine.memory_total_bytes(),
            cpu_seconds=None if totals is None else totals.cpu_seconds,
            cpu_wait_seconds=None if totals is None else totals.cpu_wait_seconds,
            memory_wait_seconds=None if totals is None else totals.memory_wait_seconds,
        )
        # A machine that gave nothing is one unknown measure, not nine.
        return None if measures == MachineMeasures() else measures

    def _free_bytes(self, path: Path | None) -> int | None:
        if path is None:
            return None
        return bytes_or_unknown(self._boundaries.disk.free_bytes, path)


def _completed(
    record: CostRecord,
    result: AgentRunResult,
    machine: MachineMeasures | None,
    transcript: TranscriptRef | None,
    tools: list[ToolUse] | None,
) -> CostRecord:
    # Copied as reported: an unknown measure stays None and a reported zero stays zero (R24).
    # A run that died or met its time limit left no reply, so its denials are unknown.
    no_reply = result.end_reason in ("died", "time_limit")
    return CostRecord.model_validate(
        {
            **record.model_dump(),
            "status": "completed",
            "duration_seconds": result.duration.total_seconds(),
            "model_seconds": None
            if result.model_duration is None
            else result.model_duration.total_seconds(),
            "end_reason": result.end_reason,
            "turns": result.turns,
            "tokens": result.tokens,
            "cost_usd": result.cost_usd,
            "denials": None if no_reply else len(result.permission_denials),
            "denied_paths": None if no_reply else _denied_paths(result),
            "login": result.login,
            "machine": machine,
            "transcript": transcript,
            "tools": tools,
        }
    )


def _denied_paths(result: AgentRunResult) -> list[str]:
    paths = [denial.path for denial in result.permission_denials if denial.path is not None]
    # Each file once, in the order the runtime reported it.
    return list(dict.fromkeys(paths))


class WorkItemBill(BaseModel):
    """A work item's bill: its total, its stages, and their cost line and table texts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    work_item: WorkItemId
    total: Bill
    stages: list[StageBill]
    line: str
    table: str


class BillService:
    """Bills work items from their sidecars on the remote-tracking refs, never the work tree."""

    def __init__(self, git: Git, cost_reader: CostRecordReader) -> None:
        """Read the refs through `git` and the sidecars through `cost_reader`."""
        self._git = git
        self._cost_reader = cost_reader

    def for_work_item(self, work_item: WorkItemId) -> WorkItemBill | None:
        """The bill of `work_item`, or `None` when no remote-tracking ref holds its file."""
        ref = self._ref_of(work_item)
        path = self._work_item_path(ref, work_item)
        if path is None:
            return None
        records = read_cost_records(self._git, self._cost_reader, ref, cost_records_path(path))
        stages = bills_by_stage(records)
        whole = bill(records)
        return WorkItemBill(
            work_item=work_item,
            total=whole,
            stages=stages,
            line=cost_line(whole),
            table=cost_table(stages),
        )

    def in_flight(self) -> list[WorkItemId]:
        """The work items that have a branch on the remote, in work item order."""
        found = [work_item_of_branch(branch.name) for branch in self._git.remote_branches()]
        return sorted((each for each in found if each is not None), key=work_item_order)

    def _ref_of(self, work_item: WorkItemId) -> str:
        branch_ref = f"{REMOTE}/{branch_name(work_item)}"
        if self._git.resolve(branch_ref) is not None:
            return branch_ref
        return f"{REMOTE}/{MAIN_BRANCH}"

    def _work_item_path(self, ref: str, work_item: WorkItemId) -> str | None:
        for path in self._git.list_files(ref, FEATURES_DIRECTORY):
            file_name = parse_work_item_file_name(PurePosixPath(path).name)
            if file_name is not None and file_name.id == work_item:
                return path
        return None


def read_cost_records(
    git: Git, cost_reader: CostRecordReader, ref: str, sidecar: str
) -> list[CostRecord]:
    """The cost records of `sidecar` at `ref`; none when the file is missing there."""
    text = git.show_file(ref, sidecar)
    if text is None:
        return []
    return cost_reader.parse(text)
