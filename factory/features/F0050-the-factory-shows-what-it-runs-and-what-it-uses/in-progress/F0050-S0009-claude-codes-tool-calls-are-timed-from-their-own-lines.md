---
stage: tests
blocked: null
round: 1
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
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T21:21:50.327205Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-04T21:25:48.287634Z'
  stage: doing
  run: e09c1a3a5f01482dabf4a2eb2a92f708
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-04T21:25:54.413769Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-04T21:27:10.021323Z'
  stage: review
  run: 209f4111d5fe48e4ae69c4b8808ff2cc
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-04T21:27:16.019550Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-04T21:27:34.216511Z'
  stage: doing
  run: 0b97efeb0c174193ab4416e97c01375e
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
7. Two `user` lines with a `tool_result` for the same `tool_use_id`, the first with a timestamp and the second with a different one or `null`, give `seconds` from the first `user` line's timestamp; and when only the second one has `is_error`, the call is not failed. Rows: second line later, second line `null`, second line failed.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, *The tool calls on the cost records*: the `seconds` row says the times come from the `assistant` line of the call and the `user` line of its result, and that other lines of the session file are not read. `docs/decisions.md`: none (the rule refines S0006's entry). `README.md` and the project guide: none.

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
9. factory: started doing as vm.
10. coder: I changed `claude_tool_uses` in `src/factory/domain/tool_uses.py`. Its signature is unchanged. It now takes a `tool_use` item only from a line whose `type` is `assistant` and a `tool_result` item only from a line whose `type` is `user`. A line of any other type, or with no `type`, adds no call and no result and changes no time. When two lines of the right type carry the same id, `dict.setdefault` keeps the first, for uses and results alike. I updated the function's docstring to say this.

    Checks: `make check` is green (lint, types, layers, sast, secrets, licenses, test). All rows of `tests/domain/test_tool_uses_replayed_lines.py` pass, and so do S0006's rows in `tests/domain/test_tool_uses.py`, unchanged (criterion 4).

    Main choice: I filter each item by its line's `type` inside the existing loop. I rejected two alternatives:
    - Dropping non-`assistant`/`user` lines before the loop. It would put the type rule in a second place, away from the item kinds it pairs with.
    - Letting a later line of the right type win. The Interface says the first time stays.

    Applying first-wins to results as well as uses goes slightly beyond what the Interface spells out. It follows the same reasoning (a replay must not erase a time) and no criterion conflicts with it.

    Noticed, not touched:
    - A malformed `tool_use` or `tool_result` item (missing `id` or `name`) on a line of another type no longer makes the whole transcript unreadable (`None`). The item is now skipped, because those lines are no longer read. This matches the Interface ("a line of another type adds no call"), and no test pins either behaviour.
    - The docs criterion (8) is for the documenter.

    Refactor: I read the diff and found nothing to change.

    `check`: check: green
    `duplicates`: duplicates: 4 new, 41 known, 2 gone
11. factory: started review as vm.
12. reviewer: Review of round 0. In scope: `src/factory/domain/tool_uses.py` and the new `tests/domain/test_tool_uses_replayed_lines.py`. I read both against the Interface and criteria 1 to 6. The code takes a `tool_use` only from an `assistant` line and a `tool_result` only from a `user` line, and keeps the first of two copies of an id through `setdefault`. Each criterion's rows test what its name says. The factory's `make check` after the coder was green (journal 10).

    Findings:
    1. criterion 7 added: it needs its test. Location: `src/factory/domain/tool_uses.py:45-47` (`results.setdefault(...)`). The Interface says "when the same id appears on two lines of the right type, the first one's time stays". The diff applies that rule to `tool_result` items on two `user` lines as well, which changes S0006's behaviour from last-wins to first-wins, but criterion 5 only covers `assistant` lines. The new criterion 7: two `user` lines with a `tool_result` for the same `tool_use_id` give `seconds` from the first one's timestamp, and an `is_error` on the second one only does not mark the call failed. Rows: second line later, second line `null`, second line failed. Fix: the tester adds one parametrized test with these rows to `tests/domain/test_tool_uses_replayed_lines.py`. No change under `src/` is needed. The closing criteria are renumbered to 8 (`make check`) and 9 (docs).

    Checked, no finding:
    - Architecture: the change stays in `factory.domain`, with no I/O and no new import.
    - Security: no marker, no secret, no command built from strings.
    - Quality: `line_type` is a clear name, and the function's docstring states the new rule. The test module's `_line`, `_use` and `_result` look like `tool_use_support._claude_line`, but they are not copies. They write `"timestamp": null` explicitly and can leave out `type`, both of which criteria 1 and 2 need, and the shared helper does neither.
    - `make duplicates` (run by me as a record) reports 4 new findings, all in `claude_runtime`/`opencode_runtime` and `cost_records.py`, outside this diff.
    - Work item hygiene: the Description matches what was built, journal 10 names the main choice and the alternatives rejected, and the docs criterion (now 9) still fits.

    Not reported, by judgment: the Interface also names a line with no `type` for results, and criteria 3 and 6 have no such row. The code handles it (`line_type == "user"`), and the failing side of the rule is tested through the `api-request-blob` and `attachment` rows.

    Earlier tests: none changed. The diff only adds `tests/domain/test_tool_uses_replayed_lines.py` (status `A`).
13. factory: started doing as vm.
14. coder: Round 1. I changed no code. The reviewer's only finding (journal 12) added criterion 7, and that criterion needs only its test.

    Criterion 7: two `user` lines carry a `tool_result` for the same `tool_use_id`. The first has a timestamp; the second has a different timestamp or `null`. `seconds` must come from the first `user` line's timestamp. When only the second line has `is_error`, the call is not failed. Rows: second line later, second line `null`, second line failed.

    The test is one parametrized test with those three rows, added to `tests/domain/test_tool_uses_replayed_lines.py`. That module has no such test yet: its five tests cover criteria 1, 2, 3, 5 and 6.

    `src/factory/domain/tool_uses.py` already keeps the first result through `results.setdefault(...)`, which is the code from round 0 (journal 10). The new test should pass against it without any code change. If it fails, the work item comes back to me.

    The Description already lists criterion 7 and the renumbered closing criteria (8 is `make check`, 9 is docs), so I did not rewrite it. `make check` was green after round 0 (journal 10), and nothing has changed since.
