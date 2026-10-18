"""The completed cost record counts the run's refused tool calls and the files they named."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.agent_runs import AgentRunResult, EndReason, PermissionDenial
from factory.domain.cost_records import CostRecord

SIDECAR = "F0001-S0001-first.costs.jsonl"
DENIALS = [
    PermissionDenial(tool="Write", detail='{"file_path": "src/a.py"}', path="src/a.py"),
    PermissionDenial(tool="Bash", detail='{"command": "git push"}'),
    PermissionDenial(tool="Edit", detail='{"file_path": "src/a.py"}', path="src/a.py"),
    PermissionDenial(tool="Write", detail='{"file_path": "docs/b.md"}', path="docs/b.md"),
]
PATHS = ["src/a.py", "docs/b.md"]


@pytest.mark.parametrize(
    ("end_reason", "denials", "expected_count", "expected_paths"),
    [
        ("completed", DENIALS, 4, PATHS),
        ("budget", DENIALS, 4, PATHS),
        ("no_result", DENIALS, 4, PATHS),
        ("completed", [], 0, []),
        ("died", [], None, None),
        ("time_limit", [], None, None),
    ],
    ids=["completed", "budget", "no-result", "completed-none", "died", "time-limit"],
)
def test_completed_record_counts_the_denials_and_their_paths_once_each_in_order(
    boundaries: Boundaries,
    end_reason: EndReason,
    denials: list[PermissionDenial],
    expected_count: int | None,
    expected_paths: list[str] | None,
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
        end_reason=end_reason,
        duration=timedelta(seconds=60),
        permission_denials=denials,
    )

    completed = CostRecorder(boundaries).complete(run, result)

    record = completed.records[-1]
    assert (record.denials, record.denied_paths) == (expected_count, expected_paths)
    written = boundaries.cost_reader.read(boundaries.checkout / SIDECAR)
    assert (written[-1].denials, written[-1].denied_paths) == (expected_count, expected_paths)
