---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 547
comments_read: [6642379279]
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T21:16:19.223093Z'
  stage: intake
  run: acfdc82cfd3b41f4a886e6c35eaf12ba
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T21:20:14.917374Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T21:20:18.419740Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T21:20:36.680857Z'
  stage: intake
  run: 3621820853474558b49dc2a9d78a859d
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T21:20:42.744958Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T21:21:44.113042Z'
  stage: tests
  run: d37a6294a04a4d7ebad820d940c9078d
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
- Tests: the rows go into a new module `tests/domain/test_tool_uses_replayed_lines.py`; no earlier test changes (the human, journal 4). A shared fixture of `tests/domain/test_tool_uses.py` may move under the standing leave.

## Acceptance criteria

1. A transcript in which a call's `assistant` line has a timestamp, its `user` result line has a timestamp, and an `api-request-blob` line between them repeats the `tool_use` item with `"timestamp": null` gives that tool's `seconds` as the result's time minus the use's. Rows: the blob line after the `assistant` line, the blob line before it, and two blob lines.
2. A `tool_use` item that appears only on a line of another type (`api-request-blob`, `attachment`, a line without `type`) is no call: the tool has no entry, or its `calls` does not count it. Rows: one per line kind.
3. A `tool_result` with `is_error` that appears only on a line of another type marks no call as failed. A `tool_result` with `is_error` on the `user` line still does.
4. The counts are unchanged for a transcript without replay lines: S0006's existing rows still pass as written.
5. Two `assistant` lines with the same `tool_use` id, the first with a timestamp and the second with a different one or `null`, give `seconds` from the first line's timestamp. Rows: second line later, second line `null`.
6. A `tool_result` that appears also on a line of another type (`api-request-blob`, `attachment`), with a timestamp that differs from the `user` line's, does not change `seconds`. Rows: the blob line before the `user` line, and after it.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *The tool calls on the cost records*: the `seconds` row says the times come from the `assistant` line of the call and the `user` line of its result, and that other lines of the session file are not read. `docs/decisions.md`: none (the rule refines S0006's entry). `README.md` and the project guide: none.

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
3. intake: Questions (the format check passed; the Interface, the smoke test, the architecture and the scope are fine; three gaps in the criteria):

   1. The Interface says that when the same id appears on two lines of the right type, the first one's time stays. No criterion tests it. Suggested new criterion before the two closing ones: "two `assistant` lines with the same `tool_use` id, the first with a timestamp and the second with a different one or `null`, give `seconds` from the first line's timestamp." Rows: second line later, second line `null`. Should I add it?

   2. The Interface says a line of another type "changes no time already read", but criterion 1 covers only a replayed `tool_use`. A `tool_result` on an `api-request-blob` or `attachment` line, with a timestamp that differs from the `user` line's, has no criterion for its time. Suggested: "a `tool_result` that appears also on a line of another type, with a different timestamp, does not change `seconds`; rows: the blob line before the `user` line, and after it." Should I add it?

   3. The Interface's Tests line leaves two options open: add rows to `tests/domain/test_tool_uses.py` (which needs the human's leave in `feature.md`), or a new module `tests/domain/test_tool_uses_replayed_lines.py`. I would choose the new module, which needs no leave. Please confirm, so the tester doesn't have to decide.

   Checked and fine: the pytest `addopts` already sets `-q`, and the smoke test command passes none; the second smoke test is runnable and its Expect line can be checked.
4. 2026-11-04 human: Answers of the human: all three as you propose.

   1. Yes, add that criterion, with the two rows (second line later, second line `null`).
   2. Yes, add that criterion, with the two rows (the blob line before the `user` line, and after it).
   3. Yes: a new module `tests/domain/test_tool_uses_replayed_lines.py`; no earlier test changes. If a shared fixture of `tests/domain/test_tool_uses.py` is needed, the standing leave to move a shared helper covers it.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `claude_tool_uses(lines: list[str]) -> list[ToolUse] | None` in `factory.domain.tool_uses` has an unchanged signature and concrete rules (`assistant` for the use, `user` for the result, other types ignored, first time stays). The Tests line now names the new module `tests/domain/test_tool_uses_replayed_lines.py` (human's answer 3, journal 4).
   - Criteria: each one is testable by one parametrized test. I added two criteria from the human's answers (journal 4, answers 1 and 2). Criterion 5: the first line's time stays when the same `tool_use` id appears twice on `assistant` lines, with rows for a later second line and a `null` one. Criterion 6: a replayed `tool_result` on a line of another type does not change `seconds`, with rows for the blob line before and after the `user` line. They went before the two closing ones, which are now 7 and 8. The failing side is covered by criteria 2 and 3 (other-type lines add no call and no failure).
   - Smoke test: both commands are runnable. The pytest line passes no `-q`, and `addopts` already sets it. Both `Expect:` lines can be checked against the output.
   - Architecture: the change stays in the domain layer. It does no I/O and adds no wiring. The records contract is unaffected.
   - Scope: it is the feature's story S0009 (from A0001) on tool-call timing, consistent with S0006's summary of tool calls. It touches nothing in the feature's Out of scope.
7. factory: started tests as vm.
8. tester: Wrote the tests for the criteria in a new module, `tests/domain/test_tool_uses_replayed_lines.py` (the human, journal 4). Its own small line builder writes each line's `type` and `timestamp` (or none), so `tests/tool_use_support.py` and `tests/domain/test_tool_uses.py` were not changed and nothing was moved.

   - criterion 1: tests/domain/test_tool_uses_replayed_lines.py::test_a_replayed_tool_use_without_a_time_keeps_the_call_s_seconds (rows: blob-after-the-assistant-line, blob-before-the-assistant-line, two-blob-lines)
   - criterion 2: tests/domain/test_tool_uses_replayed_lines.py::test_a_tool_use_only_on_a_line_of_another_type_is_no_call (rows: api-request-blob, attachment, no-type; in each row a `Read` use that has no entry and a `Bash` use that `calls` does not count)
   - criterion 3: tests/domain/test_tool_uses_replayed_lines.py::test_a_failed_result_marks_a_call_failed_only_on_a_user_line (rows: api-request-blob and attachment give failed 0, user gives failed 1)
   - criterion 4: S0006's existing tests in tests/domain/test_tool_uses.py, unchanged (the criterion says "as written"; no new test)
   - criterion 5: tests/domain/test_tool_uses_replayed_lines.py::test_a_repeated_assistant_tool_use_keeps_the_first_line_s_time (rows: second-line-later, second-line-null)
   - criterion 6: tests/domain/test_tool_uses_replayed_lines.py::test_a_replayed_tool_result_with_another_time_does_not_change_seconds (rows: before/after × api-request-blob/attachment)
   - criteria 7, 8: not tests (make check, docs).

   Choices: criteria 3, 5 and 6 check only what they name (tool, calls, failed or seconds). They do not check `calls` for a repeated id, which no criterion states. In the criterion 3 rows the foreign result is the only result, so that call is unanswered.

   File created: tests/domain/test_tool_uses_replayed_lines.py. No import failed: the module exists, and the tests fail on wrong results. 9 of them fail against the current code: the rows where the replayed copy now overwrites or adds. The rows where today's code already gives the right result pass, for example a blob before the `user` line, or criterion 3's `user` row. `make lint` is green after `ruff format`.

   `lint`: lint: green (0.1 s)
