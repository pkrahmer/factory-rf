---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 544
comments_read: [6639153913]
handed_over: null
claim: null
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
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T18:50:27.794136Z'
  stage: intake
  run: df77186843ba4249801a724a5abc9cae
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T18:50:33.957674Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T18:55:16.018666Z'
  stage: tests
  run: f0c5a8cb6a6345dc91f4d6a99bd59523
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T18:55:24.236964Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-04T19:03:15.007272Z'
  stage: doing
  run: 7c271bba7a244226a7e8ca92f01dde4f
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-04T19:03:21.377347Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-04T19:05:26.410134Z'
  stage: review
  run: 7d177ed71d9142c2864b2593b66a634a
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-04T19:05:32.372023Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-04T19:07:52.281960Z'
  stage: doing
  run: 43de3b1de72448e3a5f64a85db78d542
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-04T19:07:58.513946Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-04T19:09:24.767684Z'
  stage: tests
  run: 12f9345762cb47a186941256eef3a8de
---

# The cost record sums up the run's tool calls

## Description

The transcripts of S0005 stay inside the site, so an evaluation from a distance cannot read them. Most of its questions need no content, though: where a run spent its time and turns, how often it ran commands or read files, how many of its tool calls failed. This story puts a summary without content into every completed cost record, so that the records on GitHub and the Factory Timeline answer those questions: for each tool the run used, the number of calls, the number that failed, and the seconds they took. It holds no command text, no file content, no path and no argument, so it says nothing the record does not already say about the project. It is read from the run's transcript or the runtime's stream, before the transcript is copied or thrown away; it is written whether or not `FACTORY_TRANSCRIPT_DIR` is set.

## Interface

- A new model `ToolUse` in `factory.domain.cost_records`, frozen, unknown keys refused: `tool` (the tool's name as the runtime gives it, for example `Bash`, `Read`, `Edit`, `bash`; at most 64 characters of letters, digits, `_`, `-`, `.` and `:`), `calls` (`NonNegativeInt`), `failed` (`NonNegativeInt`, at most `calls`), `seconds` (a non-negative finite float, or `None` when the runtime gives no times).
- `CostRecord` gets `tools: list[ToolUse] | None = None`, sorted by `tool`, one entry per tool; `None` on a `started` record and when the run's tool calls cannot be read; `[]` for a run with no tool call. The records contract's version follows its rule.
- Each runtime's wrapper reads the calls from what it already has: Claude Code's session transcript (`tool_use` and its `tool_result` with `is_error`), opencode's stream events. A tool's name that breaks the form above is counted under `other`. The coder decides the reading; nothing of a call's input or output leaves the wrapper.
- Pure functions in a new `factory.domain.tool_uses`: `claude_tool_uses(lines: list[str]) -> list[ToolUse] | None` and `opencode_tool_uses(lines: list[str]) -> list[ToolUse] | None`, each `None` when the lines cannot be read, `[]` for no call; they do the counting, the `other` rule and the sorting. Each runtime wrapper gains `tool_uses(transcript: Transcript) -> list[ToolUse] | None` (an abstract operation of `AgentRuntime`, implemented by the fake too). The stage reads the transcript with `read_transcript` (S0005) whether or not `FACTORY_TRANSCRIPT_DIR` is set, passes it to `tool_uses`, and hands the result to `CostRecorder.complete(..., tools=...)`; it keeps the file only when a store is set. A call with no `tool_result` is a call, not failed, with no seconds. The contract moves to 4.4.

## Acceptance criteria

1. A completed run of each runtime carries `tools` with one entry per tool used, its calls, its failed calls and its seconds. Rows: Claude Code, opencode, a run with no tool call (`[]`).
2. A failed call (Claude Code's `is_error`, opencode's error state) counts in `failed`; `failed` above `calls` is refused by the model.
3. A tool name with a space, a slash, or more than 64 characters is counted under `other`.
4. A record's `tools` holds no text of any call's input or output: rows where a call's input holds a path, a command and a string shaped like a key, none of which appears in the record's JSON.
5. A transcript or stream that cannot be read leaves `tools` as `None` and does not fail the run.
6. `seconds` comes from the transcript: Claude Code's `tool_result` line `timestamp` minus its `tool_use` line's; opencode's tool part `time.start` and `time.end`. Rows per runtime: a transcript with times gives a float, one without gives `None`.
7. `ToolUse.seconds` refuses `-1`, NaN and infinity and accepts `0`.
8. `tools` is sorted by `tool`: a row whose tools first appear out of alphabetical order.
9. A `started` record with `tools` is refused.
10. A name of 64 characters is kept and one of 65 is counted under `other`; names with `_`, `-`, `.` and `:` are kept. Two bad names give one `other` entry with calls, failed calls and seconds summed; a tool really named `other` merges with them.
11. `ToolUse` refuses a `tool` that breaks the form; only the reading turns such a name into `other`.
12. A tool used three times, one failed, gives one entry with `calls` 3 and `failed` 1.
13. A call with no `tool_result` counts as a call, not failed, and adds no seconds.
14. `make check` stays green.
15. docs: `docs/operator-guide.md`: in the section on cost records, `tools` and its fields, and that it holds no content. `docs/decisions.md`: one entry with feature decision 6's second half. `README.md` and the project guide: none.

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
6. intake: accepted
   - Interface: concrete. `ToolUse` and `CostRecord.tools` in `factory.domain.cost_records`. Pure `claude_tool_uses` and `opencode_tool_uses` in `factory.domain.tool_uses`, with signatures. `tool_uses(transcript)` is a new abstract operation of `AgentRuntime`. The stage reads the transcript and passes `tools=` to `CostRecorder.complete`. I wrote the human's seams from journal entry 4 into the Interface.
   - Criteria: the human's answers (journal 4, items 1–8) are now written into the story as criteria 6–13, before the two closing ones. They cover the sources of `seconds` (float and `None`, per runtime), the `seconds` limits (-1, NaN, inf refused, 0 accepted), sorting, a `started` record with `tools` refused, the 64/65 limit with `_ - . :` and the merge into `other`, `ToolUse` refusing a bad name, summing repeated calls, and a call with no result. Each is testable by one parametrized test. The failing side of each rule has a row. The original criteria 1–5 are unchanged.
   - Smoke test: runnable. It passes no `-q`, because `addopts` already sets one. Each `Expect:` line is checkable.
   - Architecture: pure parsing sits in domain, the wrappers in adapters, and the abstract operation in application. This fits the four layers and the rule that wrappers are the only code to read tool output. Nothing leaves the wrapper that holds call content.
   - Scope: within the feature's S0006 line. It adds no transcript on GitHub. The leaves for the tester (the interface pin in `tests/application/test_interfaces.py`, the stand-ins' `tool_uses` returning `None`, the contract pins `"4.3"` to `"4.4"`) are in journal 4 and are not in the story file, so the tester must take them from there.
7. factory: started tests as vm.
8. tester: Tests written for every acceptance criterion. Their one run fails at collection, for the right reason: `ImportError: cannot import name 'ToolUse' from 'factory.domain.cost_records'`, raised through `tests/container_support.py`, which `tests/conftest.py` imports. `make lint` is green.

   Criterion → test:
   - criterion 1: `tests/domain/test_tool_uses.py::test_a_run_gives_one_entry_per_tool_with_its_calls_failures_and_seconds` (rows claude-code and opencode, each with two-tools and no-tool-call). Also `tests/adapters/test_runtime_tool_uses.py::test_claude_code_sums_up_the_tool_calls_of_its_session_transcript` and `::test_opencode_sums_up_the_tool_calls_of_its_run_s_stream`, each with a no-tool-call row giving `[]`. Also `tests/application/test_stage_tool_uses.py::test_a_completed_run_s_record_carries_its_tool_calls`, with rows with and without a transcript folder, plus no-tool-call.
   - criterion 2: `tests/domain/test_tool_uses.py::test_a_failed_call_counts_in_failed` (Claude Code's `is_error`, opencode's `status: "error"`) and `tests/domain/test_tool_use_model.py::test_failed_calls_never_exceed_the_calls` (failed equal to calls accepted, failed above calls refused, -1 refused for calls and for failed).
   - criterion 3: `tests/domain/test_tool_uses.py::test_a_tool_name_outside_the_form_is_counted_under_other` (rows: space, slash, 65 characters).
   - criterion 4: `tests/application/test_stage_tool_uses.py::test_a_record_s_tools_hold_no_text_of_a_call_s_input_or_output` (rows: path, command, key-shaped string, each placed in the call's input and in its result). Each checks that none of it appears in the sidecar text on the branch.
   - criterion 5: `tests/domain/test_tool_uses.py::test_lines_that_cannot_be_read_give_no_tools` (a non-JSON line, both runtimes) and `tests/application/test_stage_tool_uses.py::test_tool_calls_that_cannot_be_read_leave_tools_none_and_the_run_goes_on` (rows: unreadable transcript, no transcript kept). In both stage rows the run does not stall, moves to `doing`, and the record has `tools` `None`.
   - criterion 6: `tests/domain/test_tool_uses.py::test_seconds_come_from_the_transcript_s_times` (with-times and without-times rows, per runtime).
   - criterion 7: `tests/domain/test_tool_use_model.py::test_seconds_are_a_non_negative_finite_number_or_none` (0 and `None` accepted; -1, NaN and infinity refused).
   - criterion 8: `tests/domain/test_tool_uses.py::test_tools_are_sorted_by_name_whatever_order_they_first_appear_in`.
   - criterion 9: `tests/domain/test_tool_use_model.py::test_a_started_record_carries_no_tools` (a started record refuses `[]` and a list with entries and accepts `None`; a completed record accepts all three).
   - criterion 10: `tests/domain/test_tool_uses.py::test_a_tool_name_outside_the_form_is_counted_under_other` (rows: 64 characters kept, 65 to `other`, `mcp__files:read-v1.2` kept) and `::test_bad_names_and_a_tool_named_other_merge_into_one_other_entry` (calls, failed calls and seconds summed).
   - criterion 11: `tests/domain/test_tool_use_model.py::test_a_tool_name_outside_the_form_is_refused_by_the_model`.
   - criterion 12: `tests/domain/test_tool_uses.py::test_a_tool_used_three_times_once_failed_sums_into_one_entry`.
   - criterion 13: `tests/domain/test_tool_uses.py::test_a_call_without_a_result_is_a_call_not_failed_and_adds_no_seconds`. An answered Bash call of 1.5 s and an unanswered one give calls 2, failed 0, seconds 1.5. A lone unanswered call has no test: whether its seconds is `None` or `0` is not stated.
   - criteria 14 and 15: not tests.

   Test data: the Claude Code lines use the session form: an `assistant` line holds a `tool_use` content item with `id`, `name` and `input`, and a `user` line holds a `tool_result` with `tool_use_id`, `content` and `is_error`. Each line carries an ISO `timestamp` ending in `Z`, which is left out for the without-times rows. The opencode lines are `tool_use` events with `part.state.status`, `input`, `output` or `error`, and `time.start`/`time.end` in milliseconds, which are left out for the without-times rows. The stage tests run a test-local `ClaudeReadingRuntime(FakeAgentRuntime)` whose `tool_uses` calls a real `ClaudeCodeRuntime.tool_uses`. The test does not depend on how the fake's own `tool_uses` behaves, which the story leaves to the coder.

   Files created: `tests/tool_use_support.py` (`Call`, `claude_lines`, `opencode_lines`, `transcript_of`), `tests/domain/test_tool_use_model.py`, `tests/domain/test_tool_uses.py`, `tests/adapters/test_runtime_tool_uses.py`, `tests/application/test_stage_tool_uses.py`.

   Earlier test files changed under the human's leave in journal entry 4:
   - `tests/application/test_interfaces.py`: `AgentRuntime`'s operations now include `tool_uses`.
   - A `tool_uses` returning `None` was added to the stand-ins in `tests/observing_runtime.py`, `tests/application/test_agent_run_probe.py` (`RefusingRuntime`), `tests/application/test_stage_run.py` (`HeadNotingRuntime`) and `tests/container_support.py` (`WorkspaceRuntime`).
   - The `"4.3"` pins became `"4.4"` in `tests/domain/test_contract.py`, `tests/domain/test_contract_version_4.py` and `tests/domain/test_contract_version_4_2.py`.

   No new test checks the 4.4 contract itself, because no criterion names it.

   Modules and names the test run could not import: `factory.domain.cost_records.ToolUse` (the collection error above, which blocks every test through the conftest) and the module `factory.domain.tool_uses`.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: Implemented the tool-call summary in the cost record; `make check` is green (test: green, 91.6 s). No test changed.

    Built:
    - `src/factory/domain/cost_records.py`: `ToolUse` (frozen, extra forbidden; `tool` against `TOOL_NAME_PATTERN` `^[A-Za-z0-9_.:-]{1,64}$`, `calls`/`failed` `NonNegativeInt`, `seconds` the existing `Duration | None`, an after-validator refusing `failed > calls`); `CostRecord.tools: list[ToolUse] | None = None`, joined to the started-record check so a started record with `tools` (even `[]`) is refused.
    - `src/factory/domain/tool_uses.py` (new): `claude_tool_uses` and `opencode_tool_uses`. Lines are parsed as JSON objects (blank lines skipped, any other unreadable line or a call field of the wrong shape gives `None`); calls become name/failed/seconds only and are summed per tool in `_summed`, which maps a name outside the pattern to `other` (reusing the model's pattern, so the two rules cannot drift) and sorts by name. Claude Code: `tool_use` items matched to `tool_result` by id, `is_error is True` failed, seconds from the two lines' `timestamp`s; an unanswered call is a call, not failed, untimed. opencode: `tool_use` events, `state.status == "error"` failed, seconds from `state.time.start/end` in ms. A tool's seconds is the sum of its timed calls, `None` when none was timed; a negative or non-finite difference gives no time rather than a refused record.
    - `src/factory/domain/transcripts.py`: `transcript_lines` (UTF-8 lines, `None` on bad bytes), shared by both wrappers.
    - `src/factory/application/agent_runtime.py`: abstract `tool_uses`; `claude_runtime.py`, `opencode_runtime.py` call their domain function; `fake_agent_runtime.py` returns `None`.
    - `src/factory/application/transcripts.py`: `SessionTranscripts` split into `read(result) -> SessionTranscript` (the transcript or the reason it is missing) and `keep(work_item, run, read)`, which does nothing without a keeper and otherwise logs and keeps as before; `session_transcripts` now always returns one, with the keeper `None` without a store.
    - `src/factory/application/stage.py`: `_read_transcript` reads once, hands the transcript to `agent_runtime.tool_uses`, keeps it only with a store, and passes `tools=` to `CostRecorder.complete` (`src/factory/application/costs.py`, new keyword-only `tools`).
    - `src/factory/adapters/cost_records_jsonl.py`: `tools` joins the fields left out when `None`, so lines written before the field round-trip unchanged (the earlier writer tests pinned that).
    - `src/factory/domain/contract.py`: 4.4; schemas regenerated with `uv run python -m factory.entry.contract` (minor rise: an added optional field).

    Main decision: the transcript is read once in the stage and both the summary and the keeping work from that read, by splitting `SessionTranscripts` into read and keep. Rejected: calling `read_transcript` a second time for the summary beside the existing keep path (two reads of the same file, two places deciding why a transcript is missing).

    Refactor pass: read the diff; nothing to change.

    Noticed, not touched: `CostRecord` does not itself refuse an unsorted or duplicated `tools` list; the reading guarantees it and no criterion asks the model to. The fake's `tool_uses` always returns `None`; the stage tests use a test-local subclass that reads through the Claude Code wrapper. Docs (operator guide, decisions entry) are the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 4 new, 41 known, 2 gone
11. factory: started review as vm.
12. reviewer: Review of round 0. I read the work item, `git diff main...HEAD -- . ':!factory'` (the generated schemas only for the cost-record change and the version line) and every new and changed test, checking them against criteria 1 to 13 and the Interface. I also ran `make duplicates`. Its 4 new items are not counted as findings: the new claude/opencode similar-code item is the existing `finished_run` item moved down by the added `tool_uses` method (the old item now shows as gone). The three dead-code items are `MachineMeasures` fields that this diff does not touch.

    What holds:
    - Every criterion has a test that checks it.
    - The Interface's limits are tested on both sides: name 64/65 characters, the accepted characters, space and slash, both in the model and in the reading; `calls`/`failed` at -1 and 0; `failed` equal to `calls` and above it; `seconds` at -1, NaN, infinity, 0 and `None`; a started record with `None`, `[]` and a list.
    - The layers hold: parsing is in `factory.domain.tool_uses`, the abstract operation in `AgentRuntime`, and the wrappers only decode and delegate.
    - The contract's minor rise to 4.4 for an added optional field follows the version rule in `docs/decisions.md`.
    - No suppression markers. The journal (entry 10) records `make check` green.
    - The read/keep split of `SessionTranscripts` is explained in the journal, along with the alternative it rejected. The Description and the docs criterion match what was built.

    Findings:
    1. `src/factory/domain/tool_uses.py:118` and `:144`: a transcript of an unexpected shape raises instead of being read or refused.
       - Problem: `answered_at - called_at` raises `TypeError` when one Claude Code line's `timestamp` has an offset and the other has none (`2026-11-04T10:00:00` beside `...Z`). `float(value)` in `_milliseconds` raises `OverflowError` for an opencode `time.start`/`time.end` integer beyond float range. Nothing catches either: not `claude_tool_uses`/`opencode_tool_uses`, not the wrappers' `tool_uses`, not `StageLauncher._read_transcript` (`src/factory/application/stage.py:142`). So a transcript that the agent can rewrite in its own home on the dataset fails the stage. That breaks criterion 5 ("does not fail the run") and the rule that input is validated at the boundary.
       - Fix: in `_timestamp` (`:93`), treat a timestamp without `tzinfo` as no time. In `_milliseconds`, treat a number that does not convert to a finite float as no time, the way `_non_negative` already does.
       - Tests to hand to the tester: a mixed-offset Claude Code row and a huge-`time.end` opencode row, added to `tests/domain/test_tool_uses.py::test_seconds_come_from_the_transcript_s_times` or `::test_lines_that_cannot_be_read_give_no_tools`, whichever outcome the coder picks.
    2. `tests/application/test_stage_tool_uses.py:64-73`: `_sidecar`/`_records` is a second copy of `_records` in `tests/application/test_stage_transcripts.py:60` (show the cost-records file at the branch head, assert it exists, parse it).
       - Fix: the tester moves it to `tests/stage_run_support.py` under the standing leave and both modules use it from there.

    Earlier tests (changed test files that `main` already holds):
    - `tests/application/test_interfaces.py`: the human's leave, journal entry 4 (`tool_uses` added to `AgentRuntime`'s pinned operations).
    - `tests/application/test_agent_run_probe.py`: the human's leave, journal entry 4 (`RefusingRuntime.tool_uses` returns `None`, plus its import).
    - `tests/application/test_stage_run.py`: the human's leave, journal entry 4 (`HeadNotingRuntime.tool_uses` returns `None`, plus its import).
    - `tests/container_support.py`: the human's leave, journal entry 4 (`WorkspaceRuntime.tool_uses` returns `None`, plus its import).
    - `tests/observing_runtime.py`: the human's leave, journal entry 4 (`ObservingRuntime.tool_uses` returns `None`, plus its import).
    - `tests/domain/test_contract.py`: the human's leave, journal entry 4 (`"4.3"` -> `"4.4"`).
    - `tests/domain/test_contract_version_4.py`: the human's leave, journal entry 4 (`"4.3"` -> `"4.4"`, two pins).
    - `tests/domain/test_contract_version_4_2.py`: the human's leave, journal entry 4 (`"4.3"` -> `"4.4"`, two pins).
13. factory: started doing as vm.
14. coder: Round 1: both review findings from entry 12 are addressed. `make check` is green (test: green, 92.0 s). No test changed.

    Finding 1 (code, done) in `src/factory/domain/tool_uses.py`:
    - `_timestamp` now treats a Claude Code `timestamp` without an offset as no time. A mixed-offset pair therefore gives `seconds` `None` instead of raising `TypeError`.
    - `_milliseconds` catches `OverflowError`, so an opencode `time.start` or `time.end` integer beyond float range gives no time.
    - `_added` keeps the earlier total when adding two huge finite times would overflow to infinity. That closes the same crash in the summing step, which would otherwise surface as a `ToolUse` validation error out of `_summed`.
    - The chosen outcome is "no time", not "unreadable": the call still counts and only its seconds are dropped. That matches how a negative or non-finite difference was already handled. I rejected returning `None` for the whole transcript, because one odd time field would then hide every count.
    - I checked both cases by hand: a mixed-offset Claude Code pair gives `[ToolUse(tool='Bash', calls=1, failed=0, seconds=None)]`, and an opencode `time.end` of `10**400` gives `[ToolUse(tool='bash', calls=1, failed=0, seconds=None)]`.

    For the tester, two test changes:
    1. Add two rows to `tests/domain/test_tool_uses.py::test_seconds_come_from_the_transcript_s_times`, each expecting `seconds` `None` and the call still counted (`calls` 1, `failed` 0):
       - a Claude Code call whose `tool_use` line's `timestamp` has no offset (`2026-11-04T10:00:00`) while its `tool_result` line's ends in `Z`;
       - an opencode call whose `time.end` is an integer beyond float range (`10**400`).
    2. Under the standing leave to move a shared test helper:
       - move the duplicated `_records` (show the cost-records sidecar at the branch head, assert it exists, parse it) from `tests/application/test_stage_tool_uses.py` (`_sidecar`/`_records`, lines 64–73) and `tests/application/test_stage_transcripts.py` (`_records`, line 60) into `tests/stage_run_support.py`;
       - change both modules to use it from there.

    Refactor pass: I read the round's diff. I wrote the overflow guard in `_added` explicitly instead of as an `or` expression. Nothing else needed changing.

    Noticed, not touched: the `make duplicates` items the reviewer already judged as not findings.
15. factory: started tests as vm.
16. tester: Round 1, the test changes named in the coder's entry 14 (from the reviewer's entry 12). The one run, `uv run pytest -q tests/domain/test_tool_uses.py tests/application/test_stage_tool_uses.py tests/application/test_stage_transcripts.py`, passes: the code from entry 14 already handles both new rows. `make lint` and `make types` are green.

    1. Two new rows in `tests/domain/test_tool_uses.py::test_seconds_come_from_the_transcript_s_times`. Both expect the call still counted with no seconds, `[ToolUse(calls=1, failed=0, seconds=None)]`:
       - `claude-code-one-timestamp-without-offset`: the `tool_use` line's `timestamp` has its `Z` removed (`2026-11-04T10:00:10.000`), and the `tool_result` line keeps its `Z`.
       - `opencode-end-beyond-float-range`: `state.time.end` is `10**400`.
       - These rows only fit one runtime each, so the test can no longer take the two-runtime `read` fixture and a `seconds` value. Its rows now pair a reading with the expected result. The earlier with-times (2.5) and without-times (`None`) cases are still there as one row per runtime, so the test's name and what it checks are unchanged. It now compares the whole result list rather than `seconds` alone.
       - Two module-private builders write the odd lines: `_claude_without_offset_on_the_call` and `_opencode_end_beyond_float_range`.
    2. The shared helper, moved under the standing leave in `CLAUDE.md` (*Tests*):
       - `tests/stage_run_support.py` now has `pushed_cost_text(boundaries, remote)`, which returns the cost-records file at the head of the branch and asserts it exists, and `pushed_cost_records(boundaries, remote)`, which parses it.
       - `tests/application/test_stage_tool_uses.py` dropped `_sidecar`/`_records` and uses the two shared helpers.
       - `tests/application/test_stage_transcripts.py`, an earlier story's test file, dropped `_records` and uses `pushed_cost_records`. Its now unused imports (`CostRecord`, `cost_records_path`, `PATH`, `branch_head`) went too. Every test there keeps its name and checks the same thing.

    Files changed: `tests/domain/test_tool_uses.py`, `tests/application/test_stage_tool_uses.py`, `tests/application/test_stage_transcripts.py` (earlier story, standing leave), `tests/stage_run_support.py` (shared support, standing leave). No files created. The test run imported every module.

    `lint`: lint: green (0.2 s)
