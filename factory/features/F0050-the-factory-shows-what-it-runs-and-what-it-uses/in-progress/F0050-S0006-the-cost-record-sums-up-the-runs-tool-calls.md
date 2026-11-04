---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 544
comments_read: [6639153913]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T18:50:03.234352Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T18:41:31.680020Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T18:41:31.687184Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T18:41:57.176285Z'
  stage: intake
  run: ace39bc97fb5450a9342fc4e0d35a38d
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T18:49:59.865858Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T18:50:03.234352Z'
  stage: intake
---

# The cost record sums up the run's tool calls

## Description

The transcripts of S0005 stay inside the site, so an evaluation from a distance cannot read them. Most of its questions need no content, though: where a run spent its time and turns, how often it ran commands or read files, how many of its tool calls failed. This story puts a summary without content into every completed cost record, so that the records on GitHub and the Factory Timeline answer those questions: for each tool the run used, the number of calls, the number that failed, and the seconds they took. It holds no command text, no file content, no path and no argument, so it says nothing the record does not already say about the project. It is read from the run's transcript or the runtime's stream, before the transcript is copied or thrown away; it is written whether or not `FACTORY_TRANSCRIPT_DIR` is set.

## Interface

- A new model `ToolUse` in `factory.domain.cost_records`, frozen, unknown keys refused: `tool` (the tool's name as the runtime gives it, for example `Bash`, `Read`, `Edit`, `bash`; at most 64 characters of letters, digits, `_`, `-`, `.` and `:`), `calls` (`NonNegativeInt`), `failed` (`NonNegativeInt`, at most `calls`), `seconds` (a non-negative finite float, or `None` when the runtime gives no times).
- `CostRecord` gets `tools: list[ToolUse] | None = None`, sorted by `tool`, one entry per tool; `None` on a `started` record and when the run's tool calls cannot be read; `[]` for a run with no tool call. The records contract's version follows its rule.
- Each runtime's wrapper reads the calls from what it already has: Claude Code's session transcript (`tool_use` and its `tool_result` with `is_error`), opencode's stream events. A tool's name that breaks the form above is counted under `other`. The coder decides the reading; nothing of a call's input or output leaves the wrapper.

## Acceptance criteria

1. A completed run of each runtime carries `tools` with one entry per tool used, its calls, its failed calls and its seconds. Rows: Claude Code, opencode, a run with no tool call (`[]`).
2. A failed call (Claude Code's `is_error`, opencode's error state) counts in `failed`; `failed` above `calls` is refused by the model.
3. A tool name with a space, a slash, or more than 64 characters is counted under `other`.
4. A record's `tools` holds no text of any call's input or output: rows where a call's input holds a path, a command and a string shaped like a key, none of which appears in the record's JSON.
5. A transcript or stream that cannot be read leaves `tools` as `None` and does not fail the run.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`: in the section on cost records, `tools` and its fields, and that it holds no content. `docs/decisions.md`: one entry with feature decision 6's second half. `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^class ToolUse\(BaseModel\):$' src/factory/domain/cost_records.py
uv run pytest tests/domain tests/adapters -k tool 2>&1 | tail -1
```

Expect: `1`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed). The smoke test is fine: it passes no `-q`, and addopts already sets one. The Interface states several rules that no criterion tests:
   1. `seconds` is `None` when the runtime gives no times. No criterion covers it, on either side. Which runtime gives no times, and should a row check `None` there and a float where times exist? I would add a criterion with one row per case.
   2. `seconds` must be non-negative and finite. No criterion refuses a negative value, NaN or infinity, and none accepts 0. I would add a criterion with rows for -1, NaN and inf (refused) and 0 (accepted).
   3. `tools` is sorted by `tool`, with one entry per tool. No criterion tests the ordering. I would add one with a run whose tools first appear out of alphabetical order.
   4. `tools` is `None` on a `started` record. Criterion 5 covers an unreadable transcript but not the `started` record. I would add a row for it.
   5. A name that breaks the form is counted under `other`. Criterion 3 lists a space, a slash and more than 64 characters. It does not list the exact limit (64 accepted, 65 to `other`) or the accepted characters `_`, `-`, `.` and `:`. Should two bad names merge into a single `other` entry, with their calls and seconds summed? And if a real tool is named `other`, does it merge with them? I would answer yes to both.
   6. The `ToolUse.tool` form (at most 64 characters of the listed set) has no criterion on the model itself. Is a name that breaks the form refused by the model, with `other` produced only by the wrapper? I would say yes and add a row.
   7. Criterion 1 says "one entry per tool used" but does not say that calls and failed calls are summed per tool when a tool is used several times. A row with repeated calls and one failure would show it.
   8. A call with no `tool_result` (an interrupted run) has no stated handling: counted as a call, not failed, with no seconds? Which is meant?
4. 2026-11-04 human: Answers of the human. All eight as you propose, and the seams named now, so that the tester need not ask:

   1. Times come from the transcript. Claude Code's session lines carry a `timestamp`; a call's seconds are its `tool_result` line's time minus its `tool_use` line's time. opencode's event stream gives a tool part's `time.start` and `time.end` where the event holds them. Where a call has no times, its tool's `seconds` is `None`. Rows: one transcript with times (a float) and one without (`None`), for each runtime.
   2. Yes: `-1`, NaN and infinity refused, `0` accepted.
   3. Yes: a row whose tools first appear out of alphabetical order.
   4. Yes: a `started` record with `tools` is refused.
   5. Yes: 64 characters accepted, 65 to `other`; a row with `_`, `-`, `.` and `:` accepted. Two bad names merge into one `other` entry, their calls, failed calls and seconds summed; a tool that is really named `other` merges with them.
   6. Yes: the model refuses a name that breaks the form; only the reading turns such a name into `other`.
   7. Yes: a row with one tool used three times, one of them failed (`calls` 3, `failed` 1).
   8. A call with no `tool_result` counts as a call, not failed, and adds no seconds.

   The seams, for the Interface:
   - `ToolUse` in `factory.domain.cost_records`; `CostRecord.tools: list[ToolUse] | None = None`.
   - Pure functions in a new `factory.domain.tool_uses`: `claude_tool_uses(lines: list[str]) -> list[ToolUse] | None` and `opencode_tool_uses(lines: list[str]) -> list[ToolUse] | None`, each `None` when the lines cannot be read, `[]` for no call. They do the counting, the `other` rule and the sorting. Each runtime wrapper gains `tool_uses(transcript: Transcript) -> list[ToolUse] | None`, calling its function (an abstract operation of `AgentRuntime`, implemented by the fake too; the stand-ins of earlier tests get one that returns `None`, under the same kind of leave as in S0005).
   - The stage reads the run's transcript with `read_transcript` (S0005) whether or not `FACTORY_TRANSCRIPT_DIR` is set, passes it to `tool_uses`, and hands the result to `CostRecorder.complete(..., tools=...)`; it keeps the file only when a store is set.

   Leave for the tester: the pin of `AgentRuntime`'s operations in `tests/application/test_interfaces.py` gains `tool_uses`, and every `AgentRuntime` stand-in of an earlier test gets a `tool_uses` that returns `None`, named in its entry; nothing else in those modules. The contract moves to 4.4 with a criterion, and the `"4.3"` pins of the three contract tests become `"4.4"` under the same leave.
5. factory: started intake as vm.
