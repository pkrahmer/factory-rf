"""The cost record lines and records the JSON-lines cost record tests share."""

from datetime import UTC, datetime
from decimal import Decimal

from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord

STARTED_AT = datetime(2026, 10, 12, 8, 30, tzinfo=UTC)


STARTED_AT_TEXT = STARTED_AT.isoformat().removesuffix("+00:00") + "Z"


COMPLETED_LINE = (
    '{"run":"' + "a" * 32 + '","work_item":"F0002-S0007","stage":"tests","role":"tester",'
    '"attempt":0,"status":"completed","started_at":"' + STARTED_AT_TEXT + '",'
    '"duration_seconds":41.0,"model_seconds":41.5,"end_reason":"completed","turns":7,'
    '"tokens":{"input":12,"output":3438,"cache_read":127336,"cache_creation":31343},'
    '"cost_usd":"0.3450","image":null}\n'
)


STARTED_LINE = (
    '{"run":"' + "b" * 32 + '","work_item":"F0002-S0007","stage":"tests","role":"tester",'
    '"attempt":0,"status":"started","started_at":"' + STARTED_AT_TEXT + '",'
    '"duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,'
    '"cost_usd":null,"image":null}\n'
)


REQUIRED: dict[str, object] = {
    "run": "b" * 32,
    "work_item": "F0002-S0007",
    "stage": "tests",
    "role": "tester",
    "attempt": 0,
    "status": "started",
    "started_at": STARTED_AT_TEXT,
}


def _completed(run: str = "a" * 32) -> CostRecord:
    return CostRecord(
        run=run,
        work_item="F0002-S0007",
        stage="tests",
        role="tester",
        attempt=0,
        status="completed",
        started_at=STARTED_AT,
        duration_seconds=41.0,
        model_seconds=41.5,
        end_reason="completed",
        turns=7,
        tokens=TokenCounts(input=12, output=3438, cache_read=127336, cache_creation=31343),
        cost_usd=Decimal("0.3450"),
    )


def _started(run: str = "b" * 32) -> CostRecord:
    return CostRecord(
        run=run,
        work_item="F0002-S0007",
        stage="tests",
        role="tester",
        attempt=0,
        status="started",
        started_at=STARTED_AT,
    )
