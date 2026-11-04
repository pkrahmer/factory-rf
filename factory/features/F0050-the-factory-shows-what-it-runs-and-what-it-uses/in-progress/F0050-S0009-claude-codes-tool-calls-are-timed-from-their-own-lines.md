---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T21:15:58.038128Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T21:15:58.031123Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T21:15:58.038128Z'
  stage: intake
---

# Claude Code's tool calls are timed from their own lines

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

S0006 sums up each run's tool calls in the cost record, with the seconds they took, so that the records show where a run spent its time. For Claude Code that last part is lost in practice. In the 21 records of F0050-S0007, every `Bash`, `Read`, `Edit` and `Write` entry has `seconds: null`; only `StructuredOutput` is timed. The feature's acceptance found the cause on a real Claude Code 2.1.318 session file. Besides its `assistant` and `user` lines, the file holds `api-request-blob` lines that repeat the conversation, `tool_use` items included, with `"timestamp": null`. `claude_tool_uses` reads `tool_use` and `tool_result` items from every line and keys them by id, so the replayed copy overwrites the time of the real `assistant` line. On that file, all lines give `Bash calls=49 seconds=None`; only the `assistant` and `user` lines give `seconds=123.326`. The counts of calls and failures happen to survive, because the copies carry the same ids. This story makes the reader take a call only from the line that made it: a `tool_use` from an `assistant` line, a `tool_result` from a `user` line. A line of any other type adds no call, no result and no time. opencode's reading and the record's form do not change, and so does not the records contract.

## Interface

- `factory.domain.tool_uses` (domain), unchanged signature:

  ```python
  def claude_tool_uses(lines: list[str]) -> list[ToolUse] | None: ...
  ```

  - A `tool_use` item counts only on a line whose `type` is `assistant`, and a `tool_result` item only on a line whose `type` is `user`.
  - A line of another `type` (for example `api-request-blob`, `attachment`, `tools-used`) or with no `type` adds no call and no result, and changes no time already read, even when it holds a `tool_use` or `tool_result` item with the same id.
  - When the same id appears on two lines of the right type, the first one's time stays (a resumed session repeats nothing, but a replay must not erase a time).
  - Everything else stays as S0006 built it: `None` for a line that cannot be read, `[]` for no call, the `other` rule, the sorting, an unanswered call counted and not timed.
- Tests: `tests/domain/test_tool_uses.py` gets the new rows (S0006's tester's module; adding rows to an existing parametrized test needs the human's leave in `feature.md`, or the rows go into a new module `tests/domain/test_tool_uses_replayed_lines.py`).

## Acceptance criteria

1. A transcript in which a call's `assistant` line has a timestamp, its `user` result line has a timestamp, and an `api-request-blob` line between them repeats the `tool_use` item with `"timestamp": null` gives that tool's `seconds` as the result's time minus the use's. Rows: the blob line after the `assistant` line, the blob line before it, and two blob lines.
2. A `tool_use` item that appears only on a line of another type (`api-request-blob`, `attachment`, a line without `type`) is no call: the tool has no entry, or its `calls` does not count it. Rows: one per line kind.
3. A `tool_result` with `is_error` that appears only on a line of another type marks no call as failed. A `tool_result` with `is_error` on the `user` line still does.
4. The counts are unchanged for a transcript without replay lines: S0006's existing rows still pass as written.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *The tool calls on the cost records*: the `seconds` row says the times come from the `assistant` line of the call and the `user` line of its result, and that other lines of the session file are not read. `docs/decisions.md`: none (the rule refines S0006's entry). `README.md` and the project guide: none.

## Smoke test

```bash
uv run pytest tests/domain -k tool_uses 2>&1 | tail -1
```

Expect: a line that ends in `passed` with no `failed`.

```bash
uv run python -c '
import json
from factory.domain.tool_uses import claude_tool_uses
use = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}
res = {"type": "tool_result", "tool_use_id": "t1"}
lines = [
  json.dumps({"type": "assistant", "timestamp": "2026-11-04T10:00:00.000Z", "message": {"content": [use]}}),
  json.dumps({"type": "api-request-blob", "timestamp": None, "message": {"content": [use]}}),
  json.dumps({"type": "user", "timestamp": "2026-11-04T10:00:02.500Z", "message": {"content": [res]}}),
]
print(claude_tool_uses(lines))'
```

Expect: `[ToolUse(tool='Bash', calls=1, failed=0, seconds=2.5)]`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
