"""The completed cost record keeps the login the run was handed."""

from datetime import UTC, datetime, timedelta

import pytest

from factory.application.boundaries import Boundaries
from factory.application.costs import CostRecorder, CostRun
from factory.domain.agent_runs import AgentRunResult, Login
from factory.domain.cost_records import CostRecord

SIDECAR = "F0001-S0001-first.costs.jsonl"


@pytest.mark.parametrize(
    "login", [pytest.param("api_key", id="api-key"), pytest.param(None, id="none")]
)
def test_the_completed_record_keeps_the_result_s_login(
    boundaries: Boundaries, login: Login | None
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
        duration=timedelta(seconds=60),
        decision="review",
        entry="done",
        login=login,
    )

    completed = CostRecorder(boundaries).complete(run, result)

    assert completed.records[-1].login == login
    written = (boundaries.checkout / SIDECAR).read_text(encoding="utf-8").splitlines()
    assert written[-1].endswith(',"login":"api_key"}') == (login == "api_key")
    assert ('"login"' in written[-1]) == (login is not None)
    assert boundaries.cost_reader.read(boundaries.checkout / SIDECAR)[-1].login == login
