# The run record counts the refused tool calls

## Description

The agent runtime already reports the tool calls it refused, but the factory's run record does not keep them. This story gives the run record room for what the runtime reports: the cost record of a completed run gains `denials`, the number of tool calls the agent runtime reports as refused (the result's `permission_denials`, whatever refused them: a permission or deny rule of the runtime's settings or anything else the runtime reports there; under opencode, F0020 fills the same list), and `denied_paths`, the files those calls named (the feature's decision 8). Both are optional and left out of the sidecar line when unknown, so every line written before stays as it is; F0020 adds its spend-limit waits beside them in the same way (decision 9). A refusal the runtime does not report as a refused tool call, such as a write the kernel refuses, is only text in a tool's output inside the agent's transcript; it is not parsed and not counted. The stop records are S0003's.

## Interface

`factory.domain.agent_runs.PermissionDenial` (`domain`): a new field `path: str | None = None`, the file the refused call named.

`factory.adapters.claude_runtime` (`adapters`): `_denials` sets `path` to the denial's `tool_input["file_path"]`, or else its `tool_input["notebook_path"]`, when `tool_input` is an object and that value is a string; otherwise `None`. `detail` stays as today.

`factory.domain.cost_records.CostRecord` (`domain`): two new last fields, after `instance`:

```python
denials: NonNegativeInt | None = None
denied_paths: list[str] | None = None
```

- A `started` record with either set is refused, like its other measures.

`factory.application.costs.CostRecorder.complete` (`application`): the completed record gets `denials=len(result.permission_denials)` and `denied_paths` the `path` of each denial that has one, each path once, in the order the runtime reported them; for a run that ended `died` or `time_limit` (no reply from the runtime) both stay `None`.

`factory.adapters.cost_records_jsonl` (`adapters`): the line leaves `denials` out when it is `None` and `denied_paths` out when it is `None`, as it leaves out a `None` `instance`; when set they are written after `instance`, and the reader reads them back.

Test modules (new): `tests/adapters/test_claude_runtime_denial_paths.py`, `tests/domain/test_cost_record_denials.py`, `tests/application/test_costs_denials.py`, `tests/adapters/test_cost_records_jsonl_denials.py`. Earlier tests this story changes, under the feature's decision 14: `tests/adapters/test_claude_runtime_resume.py`, the expected `Write` denial gaining `path="x"`, and nothing else.

## Acceptance criteria

1. `_denials` of the `claude -p` runtime's reply, rows of one parametrized test: a `Write` with `{"file_path": "src/a.py"}` gives `path` `src/a.py`; a `NotebookEdit` with `{"notebook_path": "n.ipynb"}` gives `n.ipynb`; a call with both keys gives the `file_path`; a `Bash` with `{"command": "git push"}` gives `None`; `{"file_path": 3}` gives `None`; a `tool_input` that is a string gives `None`. `detail` is as today in every row.
2. `CostRecord`, rows of one parametrized test: a `completed` record with `denials=0` and with `denials=2` and `denied_paths=["src/a.py"]` is accepted; `denials=-1` is refused; a `started` record with `denials=0`, and one with `denied_paths=[]`, is refused.
3. `CostRecorder.complete`, rows of one parametrized test over the end reasons: a `completed`, a `budget` and a `no_result` run with the denials `Write src/a.py`, `Bash` (no path), `Edit src/a.py`, `Write docs/b.md` give `denials` 4 and `denied_paths` `["src/a.py", "docs/b.md"]`; a `completed` run without denials gives `denials` 0 and `denied_paths` `[]`; a `died` and a `time_limit` run give `None` for both.
4. The cost record writer, rows of one parametrized test: a record with both `None` is written as today, without `denials` and `denied_paths` keys; a record with `denials` 2 and `denied_paths` `["src/a.py"]` is written with `"denials":2,"denied_paths":["src/a.py"]` after `instance`; each line read back equals its record.
5. `make check` stays green.
6. docs:
    - `docs/operator-guide.md`, *The cost table* or *What a work item cost*: the sidecar's `denials` and `denied_paths`, and that only the tool calls the runtime reports as refused are in them, not a refusal that is only text in a tool's output.
    - `docs/project-guide.md`, *Cost records*: the two new fields and their `None`.

## Smoke test

```bash
uv run -q python -c '
import json
from datetime import UTC, datetime
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.cost_records import CostRecord

fields = dict(
    run="a" * 32, work_item="F0001-S0001", stage="doing", role="coder", attempt=0,
    started_at=datetime(2026, 10, 18, 10, 0, tzinfo=UTC),
)
started = CostRecord(status="started", **fields)
done = CostRecord(
    status="completed", duration_seconds=1.0, end_reason="completed",
    denials=2, denied_paths=["src/a.py"], **fields,
)
for line in JsonLinesCostRecordWriter().render([started, done]).splitlines():
    record = json.loads(line)
    print(record.get("denials", "absent"), record.get("denied_paths", "absent"))
'
```

Expect: two lines, `absent absent` and `2 ['src/a.py']`.

## Journal
