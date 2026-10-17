"""The model's time in the cost record file: a line written before it existed still reads."""

from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader

STARTED_AT_TEXT = "2026-10-12T08:30:00Z"
EARLIER_COMPLETED_LINE = (
    '{"run":"' + "a" * 32 + '","work_item":"F0002-S0007","stage":"tests","role":"tester",'
    '"attempt":0,"status":"completed","started_at":"' + STARTED_AT_TEXT + '",'
    '"duration_seconds":41.0,"end_reason":"completed","turns":7,'
    '"tokens":{"input":12,"output":3438,"cache_read":127336,"cache_creation":31343},'
    '"cost_usd":"0.3450","image":null}\n'
)
EARLIER_STARTED_LINE = (
    '{"run":"' + "b" * 32 + '","work_item":"F0002-S0007","stage":"tests","role":"tester",'
    '"attempt":0,"status":"started","started_at":"' + STARTED_AT_TEXT + '",'
    '"duration_seconds":null,"end_reason":null,"turns":null,"tokens":null,'
    '"cost_usd":null,"image":null}\n'
)


def test_lines_without_model_seconds_read_with_it_unknown() -> None:
    completed, started = JsonLinesCostRecordReader().parse(
        EARLIER_COMPLETED_LINE + EARLIER_STARTED_LINE
    )

    assert completed.duration_seconds == 41.0
    assert completed.model_seconds is None
    assert started.model_seconds is None
