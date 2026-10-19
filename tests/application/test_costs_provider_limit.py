"""The completed cost record of a run ended by a provider's limit counts its refused calls."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.agent_runs import AgentRunResult, EndReason, PermissionDenial
from factory.domain.cost_records import CostRecord

SIDECAR = "F0001-S0001-first.costs.jsonl"
DENIAL = PermissionDenial(tool="Write", detail='{"file_path": "/work/a.py"}', path="/work/a.py")


@pytest.mark.parametrize(
    ("end_reason", "denials", "expected_count", "expected_paths"),
    [
        pytest.param("provider_limit", [DENIAL], 1, ["/work/a.py"], id="limit-one-denial"),
        pytest.param("provider_limit", [], 0, [], id="limit-no-denial"),
        pytest.param("died", [], None, None, id="died"),
        pytest.param("time_limit", [], None, None, id="time-limit"),
    ],
)
def test_a_provider_limit_record_counts_its_denials_and_keeps_its_end_reason(
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
        end_reason=end_reason, duration=timedelta(seconds=60), permission_denials=denials
    )

    completed = CostRecorder(boundaries).complete(run, result)

    written = boundaries.cost_reader.read(boundaries.checkout / SIDECAR)
    for record in (completed.records[-1], written[-1]):
        assert record.end_reason == end_reason
        assert (record.denials, record.denied_paths) == (expected_count, expected_paths)
