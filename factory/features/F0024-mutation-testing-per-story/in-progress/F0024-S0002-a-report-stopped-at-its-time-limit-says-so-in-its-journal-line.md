---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 271
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T16:26:16.045793Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T16:26:16.051646Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T16:26:38.909346Z'
  stage: intake
  run: b73d88c57c5245d18769af5ed9478863
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T16:26:59.253210Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T16:29:01.484769Z'
  stage: tests
  run: a22d91aac353454295af6500799cc056
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T16:29:22.644247Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T16:31:13.590887Z'
  stage: doing
  run: a1dace531ebc4bd5a9b51d8ae44c3d91
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T16:31:34.354556Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T16:31:58.884435Z'
  stage: review
  run: ba7af0cbbe85499e942140dbc120ce57
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T16:32:19.414570Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T16:32:47.224336Z'
  stage: docs
  run: da76bd34d0834bb1a8f3ac583457f6ae
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T16:33:07.592279Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T16:33:22.521156Z'
  stage: smoke-test
  run: 84cd9dc757644b3d9c51ff93a9546055
---

# A report stopped at its time limit says so in its journal line

## Description

After a stage's agent the factory adds one line per green check and per report to the agent's journal entry: `` `<command>`: <last line of its output> ``. A command that reaches its time limit is killed with its process group. Its last line is then whatever it printed last, for example a progress line of mutmut, and the journal line does not say that the command was stopped. The records say it (`time_limit` in `project-commands.jsonl`), but the reviewer and the human read the journal. With `mutants` as a report of the doing stage (the feature's change 2), a run killed at its 10 minutes would read like an ordinary result. This story makes `command_line` (F0023-S0002) add ` (stopped at its time limit after <seconds> s)` to the line of a result whose status is `time_limit`. A passed line, a reused line and a failed line stay exactly as they are: a failed report's own last line already says what it is. Nothing else changes. The stall of a red check keeps its detail, the records keep their fields, and no status is added.

## Interface

`factory.domain.checks` (`domain`):

```python
def command_line(result: CheckResult) -> str: ...
```

- For a result whose `status` is `time_limit`: `` `<command>`: <last_line> (stopped at its time limit after <s> s) ``, where `<s>` is `int(result.duration.total_seconds())`, the whole seconds rounded down. When `last_line` is empty it is `` `<command>`: (stopped at its time limit after <s> s) ``.
- For `passed` and `failed` results the line is the one F0023-S0002 gives (`` `<command>`: <last_line> ``, followed by the reuse note for a reused result). A reused result is always `passed` (F0023), so the two notes never meet.

`factory.application.stage` (`application`): unchanged. `StageFinisher` already writes every green check and every report through `command_line`, so a time-limited report's line is the new one.

Unchanged: `CheckResult` and its statuses, `CommandRecord`, `ResultRecord`, `MakeProjectCommands`, the stall detail of a red check, and every line of a passed or failed command.

Tests (the tester writes them): `tests/domain/test_command_line_time_limit.py` and `tests/application/test_stage_time_limited_report.py`. The stage test uses `open_story`, `stage_makefile`, `completed`, `run_stage` and `branch_head` of `tests/stage_run_support.py` (the stage `tests` of `PIPELINE_YAML`: check `lint`, report `test`), `ScriptedRun` of the fake agent runtime, and boundaries built as `dataclasses.replace(boundaries, project_commands=...)`. Their project commands are a `ProjectCommands` subclass in the test module: it returns, for `test`, `CheckResult(command="test", status="time_limit", exit_status=None, duration=timedelta(seconds=600.7), last_line="1718/1858 mutants", output_tail="1718/1858 mutants")` and hands every other command to the fixture's `boundaries.project_commands`. No earlier test changes: F0023-S0002's `tests/domain/test_command_line.py` and `tests/application/test_stage_finish.py` stay as they are and pass.

## Acceptance criteria

1. `command_line` (rows of one parametrized test, results of the command `mutants`): status `time_limit` (exit status `None`), last line `1718/1858 mutants`, duration 600.7 s gives `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``. The same with duration 599.999 s gives `... after 599 s)`. The same with an empty last line gives `` `mutants`: (stopped at its time limit after 600 s) ``. Status `passed` (exit 0), last line `mutants: 3 killed`, gives `` `mutants`: mutants: 3 killed ``. Status `failed` (exit 1), last line `mutants: partial, 3 killed`, gives `` `mutants`: mutants: partial, 3 killed ``.
2. The stage (one test): a story at the stage `tests` whose tester ends with `doing`, with project commands whose `test` returns the `time_limit` result of the Interface and whose `lint` runs `stage_makefile`'s target. `run_stage` moves the work item to `doing` (rule 6), and the tester's entry in the work item's text at `branch_head` ends with the two lines `` `lint`: lint done `` and `` `test`: 1718/1858 mutants (stopped at its time limit after 600 s) ``.
3. `make check` stays green.
4. docs: `docs/operator-guide.md`, *What a stage run shows*, point 3: one sentence after the example. A report stopped at its time limit gets the line with ` (stopped at its time limit after <seconds> s)` at its end, for example `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``. Its last line is then only what it printed last, and the records hold `time_limit`. `docs/project-guide/processes-and-checks.md`, *Project commands*: `command_line`'s rule for a `time_limit` result. `docs/decisions.md`: an entry *The journal line of a command stopped at its time limit says so*, dated with the story, with the feature's decision 10 and the rejected alternatives: a suffix for failed results too (a failed report's own line says it, and an existing test pins one) and a gentler stop in the process module.

## Smoke test

```bash
uv run -q python - <<'EOF'
from datetime import timedelta
from factory.domain.checks import CheckResult, command_line

stopped = CheckResult(command="mutants", status="time_limit", exit_status=None, duration=timedelta(seconds=600.7), last_line="1718/1858 mutants", output_tail="")
silent = stopped.model_copy(update={"last_line": ""})
failed = CheckResult(command="mutants", status="failed", exit_status=1, duration=timedelta(seconds=540), last_line="mutants: partial, 3 killed", output_tail="")
print(command_line(stopped))
print(command_line(silent))
print(command_line(failed))
EOF
```
Expect: three lines, `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``, `` `mutants`: (stopped at its time limit after 600 s) ``, `` `mutants`: mutants: partial, 3 killed ``

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: `factory.domain.checks.command_line(result: CheckResult) -> str` exists (checks.py:88) and `CheckResult` has `duration: timedelta`. The signature, the `time_limit` format (whole seconds rounded down, the empty last line form) and the unchanged passed/failed lines are concrete. `application.stage` is declared unchanged.
   Criteria: Criterion 1 covers every Interface clause in parametrized rows: the time_limit line, rounding down (599.999 gives 599), the empty last line, and the passed and failed lines unchanged (the failing side). Criterion 2 is one stage test through `StageFinisher` with the named helpers. Each is testable by one test function. The reuse note is not tested alongside the suffix, which the Interface justifies because a reused result is always passed. Criteria 3 and 4 are the two closing ones.
   Smoke test: The script is runnable with `uv run -q python`, using the existing `CheckResult` fields. The `Expect:` line names three exact lines that can be compared with the output.
   Architecture: The change sits in `factory.domain.checks`, which is pure (no I/O). The stage test uses a `ProjectCommands` subclass, as CLAUDE.md requires, and no layer is crossed.
   Scope: It matches feature decision 10 and the scope line for `checks.py` (S0002). It does not touch the Out of scope items (no new status, no gentler stop). The earlier tests stay as they are (decision 15).
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 and 2. They are red now because the implementation is missing.
   criterion 1: tests/domain/test_command_line_time_limit.py::test_only_a_command_stopped_at_its_time_limit_gets_the_stop_note (one parametrized test with five rows: time-limit 600.7 s gives 600 s, rounded-down 599.999 s gives 599 s, empty-last-line, passed unchanged, failed unchanged)
   criterion 2: tests/application/test_stage_time_limited_report.py::test_a_report_stopped_at_its_time_limit_says_so_in_the_entry (a `StoppedTestCommands(ProjectCommands)` subclass in the module returns the Interface's `time_limit` result for `test` and hands every other command to the fixture's `boundaries.project_commands`; the test builds the boundaries with `dataclasses.replace` and uses `open_story`, `stage_makefile`, `completed`, `run_stage`, `branch_head` and `ScriptedRun`; it asserts rule 6, next stage `doing`, and that the tester's entry at `branch_head` ends with the `lint` and `test` lines)
   criterion 3 (`make check` stays green) and criterion 4 (docs) are not test criteria.
   Files created: tests/domain/test_command_line_time_limit.py, tests/application/test_stage_time_limited_report.py. No earlier test was changed.
   Every module imported: `command_line` and `CheckResult` already exist, so nothing failed at collection. `make test` (one run) fails on the three time_limit rows of the domain test and on the stage test. The passed and failed rows pass, as they should, because those lines are unchanged. `make lint` is green after `ruff format` on the stage test file. I skipped the type check as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/domain/test_command_line_time_limit.py::test_only_a_command_stopped_at_its_time_limit_gets_the_stop_note[empty-last-line]
6. factory: started doing as self.
7. coder: Built `command_line` in `src/factory/domain/checks.py`. For a result whose status is `time_limit`, the line gets ` (stopped at its time limit after <s> s)` at its end, where `<s>` is `int(result.duration.total_seconds())`. When the last line is empty, the note follows `` `<command>`: `` directly, with no double space. Passed, failed and reused lines go through the same code as before. Nothing outside `checks.py` changed: `StageFinisher` already writes every check and report through `command_line`.
   Main choice: the stop note is an early return inside `command_line`, ahead of the reuse note. A reused result is always `passed`, so the two notes never meet. Rejected: a separate helper for each note, which would add structure that one extra branch does not need.
   Refactor: I read the diff and found nothing to change.
   `make check`: green. The two new tests by the tester pass, and so do the earlier `tests/domain/test_command_line.py` and `tests/application/test_stage_finish.py`.
   Noticed, not touched: the docs (criterion 4) are the documenter's job.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   Read the work item, and the diff `git diff main...HEAD -- . ':!factory'` (`src/factory/domain/checks.py` and two new test modules).
   - Acceptance criteria: criterion 1 is `tests/domain/test_command_line_time_limit.py::test_only_a_command_stopped_at_its_time_limit_gets_the_stop_note`, one parametrized test with five rows. It covers the time-limit line, the rounding down at 600.7 s and 599.999 s, the empty last line, and the unchanged passed and failed lines. Criterion 2 is `tests/application/test_stage_time_limited_report.py::test_a_report_stopped_at_its_time_limit_says_so_in_the_entry`. It goes through `run_stage` with a `ProjectCommands` subclass that hands every other command to the fixture's commands, as the Interface asks, and checks rule 6, `doing` and the last two lines of the tester's entry at `branch_head`. Per the coder's entry, `make check` was green after the coder.
   - Code: `command_line` returns early for `time_limit`. When `last_line` is empty, the base line `` `cmd`: `` already ends in a space, so the empty-line form gives exactly `` `mutants`: (stopped at its time limit after 600 s) ``. The passed, failed and reused paths are unchanged. The docstring is updated. The function stays in `factory.domain` with no I/O, so the architecture holds.
   - Security: no suppression markers, no new inputs.
   - `make duplicates` reports 5 new findings: four similar-code findings between `claude_runtime` and `opencode_runtime`, and `ManualWaiter` in `clock.py`. None of them is in a file this diff changes.
   - Hygiene: the journal names the main choice (an early return in `command_line`) and what was rejected (a helper per note). The description matches what was built, and the docs criterion still describes what the reader needs.

   Earlier tests: none. The diff only adds test files (status `A`).
10. factory: started docs as self.
11. documenter: No findings. The code matches the Interface and the criteria. I ran the story's smoke script: the `time_limit` line and the empty-last-line form print exactly as expected. I did not run the failed row. Only documents changed, so I did not run `make check`; the factory's checks decide.

    Files changed:
    - `docs/operator-guide.md`: in *What a stage run shows*, point 3, I added the sentence about a report stopped at its time limit, with the `mutants` example and a note that the records hold `time_limit`. In the reports bullet (line ~736), "the line has the same form either way" was no longer true, so it now names the stop note as the exception.
    - `docs/project-guide/processes-and-checks.md`: *Project commands* now states `command_line`'s rule for a `time_limit` result. The seconds are `int(duration.total_seconds())`. With an empty last line the note follows `` `<command>`: `` directly. A reused result is always `passed`, so the two notes never meet. It also names the two new test modules.
    - `docs/project-guide/stages.md`: step 4 of the stage run, the line about `command_line`, now mentions the stop note. This file was not named in the docs criterion, but it described the same line.
    - `docs/decisions.md`: new entry *The journal line of a command stopped at its time limit says so*, dated 2026-10-19, with feature decision 10 and the rejected alternatives: the suffix for failed results too, and a gentler stop in the process module.

    Cross-read and found current: `README.md`, and the rest of `docs/operator-guide.md` and `docs/project-guide/processes-and-checks.md` (the *known results* text and the `check_mutants` report text).

    Stale text I noticed but did not touch: none.

    `check`: check: green (not run again: passed on tree 981e00c0d960 at 2026-10-19T16:30:25Z)
    `secrets`: secrets: green (1.6 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed. No findings.

    I ran the one command under `## Smoke test` exactly as written, from the repository root (`uv run -q python -` with the heredoc). It exited with status 0.

    ```
    `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s)
    `mutants`: (stopped at its time limit after 600 s)
    `mutants`: mutants: partial, 3 killed
    ```

    Expect: met. It printed three lines, each matching the `Expect:` line exactly:
    - The `time_limit` result at 600.7 s ends with ` (stopped at its time limit after 600 s)`, so the seconds are rounded down.
    - The empty last line gives `` `mutants`: `` followed directly by the note, with no double space.
    - The failed result's line is unchanged and has no suffix.

    Criteria check: the output agrees with criterion 1's time-limit row, empty-last-line row and failed row. The smoke test does not touch criterion 2 (the stage test), criterion 3 (`make check`) or criterion 4 (docs), and nothing in its output contradicts them. I fixed nothing.
