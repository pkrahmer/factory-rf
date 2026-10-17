# The model's time in an agent run's record

## Assignment (as of log entry 1)

Coder runs took 20 to 30 minutes in three turns, and nobody could tell how much of it was the model thinking and how much the tools running (`make check` above all). `claude -p --output-format json` already reports both in its reply: `duration_ms`, the whole call, and `duration_api_ms`, the time spent waiting for the model. This story reads `duration_api_ms` into the run's result as the model's time, adds it over a resumed call, and writes it into the run's cost record as `model_seconds`, next to the duration and the cost; the rest of a run's time is the tools' and the factory's (FEATURE decision 22). A reply without the field, a call killed by its time limit and an older record all leave it unknown (`None`, never 0, R24). The pinned lines of the cost record file's test gain the new key, by the human's leave (FEATURE decision 37). F0012-S0015 shows the sum in the cost table.

## Interface

`src/factory/domain/agent_runs.py`: `AgentRunResult` gains `model_duration: timedelta | None = None`, after `duration`: the time the model took, `None` when unknown.

`src/factory/adapters/claude_runtime.py`:

- `_Reply` gains `duration_api_ms: NonNegativeInt | None = None`; a negative value makes the reply unparsable, so the call is `died`, as for the other measures.
- A result with measures (the reply parsed, the call not killed) has `model_duration = timedelta(milliseconds=reply.duration_api_ms)`, or `None` when the reply has no such field. A call killed by its time limit has `None`.
- A resumed run (a budget stop, then the resume) has the sum of both calls' model durations when both are known, the known one when only one is, `None` when neither; a resume that the time limit ended keeps the second call's `None`, as for the other measures.

`src/factory/domain/cost_records.py`: `CostRecord` gains `model_seconds: Duration | None = None`, after `duration_seconds`. A started record has none (the rule of `_measures_only_when_completed` names it with the other measures); a completed record may have it or not.

`src/factory/application/costs.py`: the completed record copies `result.model_duration` in seconds, or `None`.

`src/factory/adapters/cost_records_jsonl.py` writes the key in field order like every other key; a line without the key (an older file) still reads, with `model_seconds` `None`.

Tests: `tests/adapters/test_claude_runtime_model_time.py` (with the `claude` stand-in of `tests/adapters/claude_stand_in.py`), `tests/domain/test_cost_record_model_seconds.py`, `tests/application/test_costs_model_seconds.py`. By the human's leave (FEATURE decision 37), and no other change to an earlier story's test: `COMPLETED_LINE`, `STARTED_LINE` and `COMPLETED` in `tests/adapters/test_cost_records_jsonl.py` gain the key `model_seconds`, `41.5` for the completed record and `null` for the started one.

## Acceptance criteria

1. A reply with `"duration_api_ms": 41500` gives a completed result with `model_duration == timedelta(seconds=41.5)`; a reply without the field gives `None`; a reply with `-1` gives the end reason `died`. Rows of one parametrized test.
2. A call killed by its time limit gives `model_duration is None`, whatever its partial output held.
3. A budget stop with `duration_api_ms` 30000 resumed by a call with 5000 gives `timedelta(seconds=35)`; with the first unknown and the second 5000, `timedelta(seconds=5)`; with both unknown, `None`; a resume ended by the time limit gives `None`. Rows of one parametrized test.
4. A `CostRecord` with `status="started"` and `model_seconds=1.0` is refused with `pydantic.ValidationError`; a completed one with `model_seconds=None`, `0` or `41.5` is accepted; `-1` and `float("nan")` are refused. Rows of one parametrized test.
5. The cost record that `CostRecorder.complete` writes for a result with `model_duration=timedelta(seconds=41.5)` has `model_seconds == 41.5`, and for a result without it, `None`.
6. The writer renders `model_seconds` after `duration_seconds`; the reader reads a line without the key with `model_seconds is None` (the pinned lines and a line written before this story).
7. `make check` stays green.
8. docs: the project guide's section *Cost records* names `model_seconds` (the reply's `duration_api_ms`, unknown when not reported or when the time limit killed the call, summed over a resume) and says that the rest of the duration is the tools' and the factory's; the operator guide's description of the cost records file names the field; the decision log records why the time per tool command inside a run is not recorded (the single JSON reply does not carry it). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import timedelta
from factory.domain.agent_runs import AgentRunResult
from factory.domain.cost_records import CostRecord
result = AgentRunResult(end_reason='completed', decision='doing', entry='Done.', duration=timedelta(seconds=60), model_duration=timedelta(seconds=41.5))
print(result.model_duration.total_seconds(), list(CostRecord.model_fields).index('model_seconds') == list(CostRecord.model_fields).index('duration_seconds') + 1)
"
```
Expect: `41.5 True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_model_time.py tests/adapters/test_cost_records_jsonl.py tests/application/test_costs_model_seconds.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
