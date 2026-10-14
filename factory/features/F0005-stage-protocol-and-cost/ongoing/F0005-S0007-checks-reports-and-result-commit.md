---
stage: demo
pr: 64
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# Checks, reports and the stage's result commit

## Assignment (as of log entry 1)

Complete the stage protocol. After the agent's outcome has been processed (S0005) and the decision rules have said where the work item goes (S0006), the factory runs the stage's checks in order and stops at the first red, runs the reports after all checks are green and notes each one's last line, appends the agent's entry (and the factory's own question, when the rules add one) to the journal, writes the new state, and commits and pushes the result as one commit: the stage's result is a pushed commit (R19). A red check is a stall (rule 5) whose note carries the last 15 lines of its output. After the push the labels are written as a projection of the stage, never read back. `StageRunner.run` is the one entry point that runs every step in the same order: prepare, claim, agent run, after the agent, decision, checks and reports, result commit. Covers R19 (the stage's result is a pushed commit), and R23's reset of the crash counter on a forward move; keeps kept things 5 (the same steps in the same order), 8 (green means the factory ran the check and read its exit status) and 14 (a stall, a rework and a question are counted apart). The hand-over at the approval, the cost table and the pull request's draft flag are F0007's.

## Interface

`src/factory/domain/labels.py`

```python
def labels_for(state: WorkItemState) -> list[str]: ...
```

`src/factory/application/stage.py` (grown by this story)

```python
STALL_TAIL_LINES = 15

class StageReport(BaseModel):
    work_item: WorkItemId
    stage: Name
    next_stage: Name
    rule: Literal[1, 2, 3, 4, 5, 6, 7] | None
    commit: CommitId
    pull_request: PositiveInt
    stall: StallResult | None

class StageFinisher:
    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None: ...
    def finish(self, aftermath: AgentAftermath) -> StageReport: ...

class StageRunner:
    def __init__(
        self,
        boundaries: Boundaries,
        instance: str,
        definition: PipelineDefinition,
        environment: Mapping[str, str],
    ) -> None: ...
    def run(self, work_item: WorkItemId, path: str) -> StageReport: ...
```

Types: `Mapping` from `collections.abc`, `StageMove` and `decide` from `factory.domain.decisions`, `StallResult` and `StallService` from `factory.application.stalls`, `CheckResult` from `factory.domain.checks`. `StageReport` is frozen and forbids unknown keys. `rule` is the decision rule applied (5 is the red check) and `None` when the stage stalled before a decision; `stall` is set exactly when the stage stalled; `next_stage` equals `stage` for a stall and for any move that keeps the stage (rules 1, 2 and 4).

- `labels_for(state)` returns `[LABEL_PREFIX + state.stage]`, for example `["stage:review"]`.
- `StageFinisher.finish` does these steps in this order. (1) `decide(definition, state, aftermath.decision, aftermath.form_findings)` with the state of `aftermath.document`: the findings after the run, so that a first stage that fixed every finding is not turned into a question. (2) For rule 6 only: each check of the stage's `checks` in order through `ProjectCommands.run(name, time_limit=timedelta(minutes=definition.project_commands[name].time_limit))`; the first result that is not `passed` ends the stage as a stall with reason `check_red` and rule 5, its detail the last `STALL_TAIL_LINES` lines of the result's `output_tail` as the project command reports it (all of them when there are fewer), and later checks and all reports are not run; the document given to the stall holds the agent's entry, with the lines of the green checks so far, appended. (3) For rule 6 only, after every check is green: each report of the stage's `reports` in order; a report that fails holds nothing. (4) The entry's text is the agent's text, then a blank line and one line `` `<command>`: <last_line> `` for each green check and each report (`<command>` is the project command's name, for example `` `check`: 12 passed ``), in the order they ran (no blank line and no lines when none ran). (5) The entry is appended with `append_entry`; when `move.question` is not `None`, `NewEntry(speaker="factory", kind="question", text=move.question)` is appended after it. (6) The new state has `stage`, `blocked` and `round` from the move, `pull_request` set to the number of `started.pull_request`, `claim` released with `ClaimService.release`; `crashes` is 0 for rule 6 and unchanged for every other rule; `attempts`, `comments_read` and `handed_over` are unchanged. (7) The file is written, everything in the work tree is committed in one commit and pushed; any push outcome but `pushed` raises `PushFailed`. (8) After the push `HostingService.set_labels(pull_request, labels_for(new_state))`.
- Rules 1, 2, 3, 4 and 7 run no check and no report.
- `HostingServiceError` from the label write and `PushFailed` from the push propagate unchanged. A label that cannot be written does not undo the pushed result commit.
- `StageRunner.run` builds its `StageLauncher` with the `environment` it was given (nothing is added or scrubbed) and does, in this order: `WorkItemOpening.prepare`; when the result has `merge_conflict`, `StallService.stall` with reason `merge_conflict` and `StallContext(stage_start=None, document=prepared.document, pull_request=None)`; else `StageLauncher.launch`, `AfterAgent.process`, and for an `AgentAftermath` `StageFinisher.finish`. A `StallResult` from any step ends the run with a `StageReport` whose `rule` is `None` and `stall` is that result. The stage that ran is the stage in the state read by `prepare`.
- A run adds exactly one commit of the factory's own on `origin/<branch>`, the result commit or the stall commit: above the stage-start commit when the agent committed nothing, above the agent's last commit when it committed (the agent's commits stay in the history, F0004 decision 15). Everything in the work tree goes into that commit, so a file a check creates is committed unless the project's `.gitignore` covers it; the operator guide says so.

Tests: `tests/domain/test_labels.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stage_run.py`. The checks and reports are real `make` targets: the tests push a `Makefile` to `main` with `human.push_file` whose targets `lint`, `check` and `test` append their names to a file under `tmp_path` (outside the checkout), print lines the test scripts and exit with a status the test sets (every recipe line starts with `@`, so make echoes no command: the output is the lines the test scripts, then make's own error line for a red target). Stages are run with `FakeAgentRuntime` scripted results and `FakeHostingService`. `StageReport` refuses what its types refuse (a `rule` outside 1 to 7, a `pull_request` below 1, an unknown key), tested on both sides (criterion 23). Unless a criterion sets form findings, the work items are complete stories (every section of the fixture's form, criteria ending with `make check` … `green` and `docs:`, a smoke-test block followed by `Expect:`): the fixture's backlog story `# First story` has findings after the run, which turn every forward decision into rule 1.

## Acceptance criteria

1. A forward decision with every check green moves the work item: the pushed file has `stage` equal to `next[0]`, `blocked` `None`, `claim` `None` and `pull_request` equal to the draft's number; the report has rule 6, `stage` the stage that ran, `next_stage` the new stage, and `commit` equal to the head of `origin/<branch>`; and `stall` is `None`.
2. The checks run in the stage's order, each once: for a stage with `checks: [lint, check]` the target log shows `lint` then `check`.
3. The checks see the work tree after the undo: a file the agent wrote outside its write paths does not exist when a check runs.
4. A red check ends the stage as a stall: the stage is unchanged in the pushed state, `attempts` is one higher, `crashes` equals the stage-start state's (a stage-start state with `crashes` 1), the report has rule 5 and `stall.reason == "check_red"`, and the later checks and the reports did not run (they are absent from the target log); the report's `next_stage` equals its `stage`.
5. The stall note of a red check carries the last 15 lines of the check's output as the project command reports it: for a check that prints `line 1` to `line 20` and exits 1 it contains `line 7` to `line 20` and make's own error line, and not `line 6`; for a check that prints `line 1` to `line 10` it contains all ten.
6. After a red check the journal holds the agent's record, whose text ends with the lines of the checks that were green, directly followed by the `factory` stall record: the agent's entry stays above the stall.
7. When every check is green, the stage's reports run in order after the last check, and a failing report does not hold the move.
8. For every green check and every report the agent's entry gains one line `` `<command>`: <last line of its output> `` after a blank line, `<command>` being the project command's name, in the order they ran (for example `` `check`: 12 passed ``); an entry for a stage with neither has no such lines.
9. The decision `question` (rule 2) runs no check and no report; the pushed state has the stage unchanged and `blocked` `question`; the agent's record has kind `question`; the report has rule 2, `next_stage` equal to `stage` and `stall` `None`.
10. A rework within the cap (rule 3) and a rework at a stage without a cap (rule 7) run no check, move to the decision's stage and, for rule 3, add 1 to `round`; `attempts` is unchanged.
11. A forward decision when the form still has findings after the run (rule 1) runs no check, leaves the stage and sets `blocked` to `question`; the journal gains, after the agent's record, a record with speaker `factory` and kind `question` whose text is `findings_question` of the findings after the run.
12. A forward decision at the first stage whose run removed the only form finding moves by rule 6: the checks run, the stage is `next[0]`, `blocked` is `None`, and the journal gains no `factory` question record.
13. A rework past the cap (rule 4) runs no check, leaves the stage, sets `round` to the cap + 1 and `blocked` to `round_cap`, and appends a `factory` record of kind `question` whose text is `round_cap_question`.
14. In a move, `attempts`, `comments_read` and `handed_over` of the pushed state equal those of the stage-start state, and `crashes` is 0 after rule 6 and unchanged after rules 1, 2, 3, 4 and 7 (from a stage-start state with `crashes` 1).
15. After the push the labels of the pull request are `["stage:<new stage>"]` for a move and `["stage:<stage>"]` for a question; `labels_for` returns that list for any state.
16. A label write that fails (`fail_next("set_labels")`) makes `finish` raise `HostingServiceError`, with the result commit already on `origin/<branch>` and no stall recorded.
17. A push of the result commit that is rejected raises `PushFailed` and no label has been written.
18. A run adds exactly one commit of its own for a move, a question and a stall alike: above the stage-start commit when the agent committed nothing, and above the agent's last commit when the agent committed a file inside its write paths; that commit holds a file a check created in the checkout (a target that writes `build/out.txt`), and not one that the project's `.gitignore` covers.
19. `StageRunner.run` for a work item whose branch cannot take the main branch (a conflict) stalls with `merge_conflict` and rule `None`: no claim was pushed, `FakeAgentRuntime.requests()` is empty and `attempts` is one higher.
20. `StageRunner.run` for a died agent run returns a report with `rule` `None`, `stall.reason == "died"` and the commit of the stall.
21. Each check and each report is run with the `time_limit` that the pipeline definition gives its project command: `timedelta(minutes=10)` for `check: {time_limit: 10}` and `timedelta(minutes=5)` for `lint: {time_limit: 5}` (seen through a `ProjectCommands` that records the argument and delegates to `MakeProjectCommands`).
22. The request the agent runtime receives from `StageRunner.run` has an `environment` equal to the mapping given to `StageRunner` (a `PATH` and a `HOME` in the test), and no other entry.
23. `StageReport` refuses what its types refuse, on both sides: `rule` 1 to 7 and `None` are accepted, `rule` 0 and 8 raise `ValidationError`; `pull_request=1` is accepted and `pull_request=0` raises `ValidationError`; `commit="a" * 40` is accepted and `"a" * 39` raises `ValidationError`; assigning to `rule` (through `setattr`, the field's name in a variable) raises `ValidationError`; an unknown key raises `ValidationError` (built through a variable typed `type[BaseModel]`).
24. make check stays green.
25. docs: `docs/project-guide.md` describes the stage protocol from the claim to the result commit as `StageRunner.run` runs it, the checks and reports (order, the red tail of the last 15 lines, reports recorded only), that a forward move resets `crashes` and that labels are a projection never read back; `docs/operator-guide.md` explains what a stall by a red check looks like on the pull request and what to do about it, and that the project's `.gitignore` must cover whatever its checks create, because the result commit holds the whole work tree.

## Demo

```bash
uv run python -c "
from factory.domain.labels import labels_for
from factory.domain.work_item import initial_state
print(labels_for(initial_state('tests')))
"
```
Expect: one line, `['stage:tests']`.

```bash
uv run pytest tests/domain/test_labels.py tests/application/test_stage_finish.py tests/application/test_stage_run.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory/domain/labels.py`, `factory/application/stage.py`: `StageReport`, `StageFinisher`, `StageRunner`, `STALL_TAIL_LINES`). The eight `finish` steps and the `run` order are spelled out. The test Makefile setup is described.
   - Criteria: each is testable by one test function. Every Interface behaviour has a criterion: tail of 15 lines (5), entry lines (8), `crashes` reset (14), labels (15), time limits (21), environment (22), one commit (18). The failing sides are covered: red check (4 to 6), failing report (7), rejected push (17), failed label write (16), merge conflict (19), died run (20), rule 4 cap (13), and the `StageReport` limits on both sides (23). The two closing criteria are in place.
   - Demo: both commands are runnable. Each `Expect:` line can be checked against the output.
   - Architecture: `labels_for` is in the domain; the stage protocol is in the application layer and uses only the boundaries (project commands, hosting service, git). No concrete tool is named.
   - Scope: within the F0005 scope (decision rules, checks and reports, result commit, labels). The hand-over, cost table and draft flag stay with F0007. Nothing in the story is out of scope.
3. tester: Wrote the red tests for every acceptance criterion. `make lint` is green. `make test` stops at collection with 3 errors: `factory.domain.labels`, `STALL_TAIL_LINES`, `StageReport`, `StageFinisher` and `StageRunner` in `factory.application.stage` don't exist yet.

   Criterion → test:
   - criterion 1: tests/application/test_stage_finish.py::test_a_forward_decision_with_green_checks_moves_the_work_item
   - criterion 2: tests/application/test_stage_finish.py::test_the_checks_run_in_the_stages_order_each_once
   - criterion 3: tests/application/test_stage_finish.py::test_the_checks_see_the_work_tree_after_the_undo
   - criterion 4: tests/application/test_stage_finish.py::test_a_red_check_stalls_the_stage_and_runs_nothing_after_it
   - criterion 5: tests/application/test_stage_finish.py::test_the_stall_note_of_a_red_check_carries_the_tail_of_its_output (20 lines and 10 lines; checks make's `Error 1` line and that `line 6` is absent)
   - criterion 6: tests/application/test_stage_finish.py::test_after_a_red_check_the_agents_entry_with_the_green_checks_stays_above_the_stall
   - criterion 7: tests/application/test_stage_finish.py::test_the_reports_run_in_order_after_the_checks_and_a_failing_one_holds_nothing
   - criterion 8: tests/application/test_stage_finish.py::test_each_green_check_and_each_report_adds_its_last_line_to_the_entry, ::test_an_entry_of_a_stage_without_checks_or_reports_gains_no_lines (the review stage)
   - criterion 9: tests/application/test_stage_finish.py::test_a_question_blocks_the_stage_without_running_a_check
   - criterion 10: tests/application/test_stage_finish.py::test_a_rework_moves_to_the_decisions_stage_without_running_a_check (rule 3: docs → doing; rule 7: doing → tests; both stages have checks)
   - criterion 11: tests/application/test_stage_finish.py::test_a_forward_decision_with_findings_after_the_run_asks_the_findings_question
   - criterion 12: tests/application/test_stage_finish.py::test_a_first_stage_that_fixed_the_only_finding_moves_forward
   - criterion 13: tests/application/test_stage_finish.py::test_a_rework_past_the_cap_blocks_the_stage_with_the_round_cap_question
   - criterion 14: tests/application/test_stage_finish.py::test_a_move_keeps_the_counters_and_resets_crashes_only_on_a_forward_move (rules 6, 1, 2, 3, 4, 7)
   - criterion 15: tests/application/test_stage_finish.py::test_the_labels_after_the_push_are_the_new_stages_label, tests/domain/test_labels.py::test_the_labels_are_the_stage_label_of_the_state
   - criterion 16: tests/application/test_stage_finish.py::test_a_failed_label_write_raises_after_the_result_commit_is_pushed
   - criterion 17: tests/application/test_stage_finish.py::test_a_rejected_push_of_the_result_raises_before_any_label_is_written
   - criterion 18: tests/application/test_stage_run.py::test_a_run_adds_exactly_one_commit_of_its_own (move, question and stall from a red check; each with and without an agent commit), ::test_the_result_commit_holds_what_a_check_created_unless_it_is_ignored
   - criterion 19: tests/application/test_stage_run.py::test_a_branch_that_cannot_take_the_main_branch_stalls_before_the_claim
   - criterion 20: tests/application/test_stage_run.py::test_a_died_agent_run_ends_in_a_stall_report
   - criterion 21: tests/application/test_stage_finish.py::test_each_check_and_report_runs_with_its_commands_time_limit
   - criterion 22: tests/application/test_stage_run.py::test_the_agent_runs_with_exactly_the_environment_given_to_the_runner
   - criterion 23: tests/application/test_stage_finish.py::test_a_stage_report_accepts_values_its_types_allow, ::test_a_stage_report_refuses_values_its_types_refuse, ::test_a_stage_report_is_frozen
   - criteria 24 and 25: not tests (make check; documenter).

   Files created: tests/domain/test_labels.py, tests/application/test_stage_finish.py, tests/application/test_stage_run.py.

   Notes for the coder:
   - The finish tests use their own pipeline definition, derived from the fixture's `PIPELINE_YAML`. It adds the project command `coverage` (time_limit 3) and a matching Makefile target, so two reports can be checked for order. Its `tests` stage has `checks: [lint, check]` and `reports: [test, coverage]`, and `intake` has `checks: [lint]`.
   - The criterion-18 "file a check created" assertion is made on a forward move only. A question runs no check, and a stall undoes files outside the write paths.
   - The tests set the work item's state directly to reach rules 3, 4 and 7 and the crashes case: they push the branch file with that state, the same way the after-agent tests do.

   Rejected: a `ProjectCommands` fake for the checks. The criteria call for real make targets, so only criterion 21 wraps `MakeProjectCommands` in a recorder.

   Nothing open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: the tests' own pipeline definition is invalid, so all 28 tests in `tests/application/test_stage_finish.py` fail before they reach the code under test.

   `DEFINITION_YAML` in that file gives the `tests` stage `checks: [lint, check]` and `reports: [test, coverage]`. The tester role keeps its default `time_limit` 40 and `lease_duration` 60. The existing lease rule in `src/factory/domain/pipeline_definition.py` (`_lease_faults`) adds up the role's time limit and the time limits of the stage's project commands: 40 + 5 + 10 + 10 + 3 = 68. That is more than 60, so `pipeline_reader.parse` raises `PipelineDefinitionInvalid: role tester at stage tests: 68 min exceed lease_duration 60 min` in `_definition`.

   The implementation is done and committed as 8b70068:
   - `src/factory/domain/labels.py` holds `labels_for`.
   - `src/factory/application/stage.py` holds `STALL_TAIL_LINES`, `StageReport`, `StageFinisher` and `StageRunner`.

   The 15 tests in `tests/domain/test_labels.py` and `tests/application/test_stage_run.py` pass. I ran a throwaway copy of the finish test file whose only change was `lease_duration: 70` on the tester role, and all 43 of its tests passed. I deleted the copy; it was never committed. `make check` is green apart from these 28 tests (lint, types, layers, sast, secrets, licenses all green).

   The options I see:
   (a) The tester changes `DEFINITION_YAML` so that it parses: give the tester role a longer lease (for example `tester: {write_paths: ["tests/*"], lease_duration: 70}`, or `time_limit: 30`). Time limits, order and coverage stay as they are. I recommend this.
   (b) Relax or remove the lease rule. That changes a decision made in an earlier story and is outside this one's scope, so I would not do it.

   If you choose (a), the next run ends with `tests`, naming that one change in `DEFINITION_YAML`.

   Design (for the review afterwards): a red check reuses `StallService.stall` with the stage-start commit. The document given to it is the undone one with the agent's entry and the green checks' lines appended, so the entry stays above the stall record. The stall detail is the command's name followed by the last 15 lines of `output_tail`. I rejected a separate stall path in the finisher because it would have duplicated the attempt counting and the note.

   Refactor step: not done yet, because the checks are not green.
5. human (pull request comment, 2026-10-14): (a): the tester gives the tester role in `DEFINITION_YAML` `lease_duration: 70`, so the definition parses under F0003's lease rule; time limits, order and coverage stay as they are. End with `tests` and name exactly that change. The lease rule stays.
6. coder: The human chose (a) in entry 5, so this goes back to the tester for one test change. I have not touched any test.

   The change: in `tests/application/test_stage_finish.py`, add one more `.replace` to `DEFINITION_YAML` that gives the tester role `lease_duration: 70`. It turns `  tester: {write_paths: ["tests/*"]}` (that line comes from `PIPELINE_YAML` in `tests/git_support.py`) into `  tester: {write_paths: ["tests/*"], lease_duration: 70}`. Nothing else changes: the time limits, the order of the checks and reports, and the `coverage` command stay as they are. With this change the definition parses under F0003's lease rule, which needs 40 + 5 + 10 + 10 + 3 = 68 minutes, within 70.

   The implementation is unchanged and committed as 8b70068 (`src/factory/domain/labels.py`, `src/factory/application/stage.py`). Before, I ran a throwaway copy of the finish tests with exactly this change, and all of them passed. The refactor step is still to do; I'll do it on the next doing run, once the tests are green with `make check`.
7. tester: Made the one test change the human approved in entry 5 and the coder named in entry 6. In `tests/application/test_stage_finish.py`, `DEFINITION_YAML` now has one more `.replace`. It turns `  tester: {write_paths: ["tests/*"]}` into `  tester: {write_paths: ["tests/*"], lease_duration: 70}`, so the definition parses under F0003's lease rule (40 + 5 + 10 + 10 + 3 = 68 min, within 70). Nothing else changed: the time limits, the order of the checks and reports, and the `coverage` command are as they were.

   `make test` is green: all tests pass, coverage 99.44 %. `make lint` is green.

   Nothing open. The coder's refactor step is still to do.

   `make lint`: lint: green
   `make test`: test: green
8. coder: With the tester's change from entry 7 in place, the tests from entry 3 pass against the implementation in 8b70068, and `make check` is green: lint, types, layers, sast, secrets, licenses and test all pass, with coverage at 99.44 %.

   What I built:
   - `src/factory/domain/labels.py`: `labels_for` returns `[LABEL_PREFIX + state.stage]`.
   - `src/factory/application/stage.py`: `STALL_TAIL_LINES`, `StageReport` (frozen, forbids unknown keys), `StageFinisher` and `StageRunner`.
     - `StageFinisher.finish` follows the eight steps: decide; for rule 6, run the checks and then the reports; append the entry with one `` `<command>`: <last_line> `` line per command that ran; append the factory's question when the move has one; write the moved state; commit and push (`PushFailed` on any outcome but `pushed`); set the labels last.
     - A forward move (rule 6) resets `crashes`.
     - `StageRunner.run` does prepare, then either the merge-conflict stall or launch, after-agent and finish. A stall from any step is reported with rule `None`.

   Main design decision: a red check reuses `StallService.stall` with the stage-start commit, and the stall note is the command's name followed by the last 15 lines of its output. The document passed to it already holds the agent's entry and the green checks' lines, so the entry stays above the stall record. I rejected a separate stall path in the finisher because it would have duplicated the attempt counting and the note.

   Refactor (6e0be8c): I moved the check-and-report loop out of `finish` into `_run_checks_and_reports`. It returns the commands that ran and the first red check, if there is one. Behaviour is unchanged, no test was touched, and `make check` is green.

   Noticed but not touched: `claims.py`, `stalls.py` and now `stage.py` each have their own private `_state_of` helper. Merging them into one would reach beyond this story.

   `make check`: check: green
9. reviewer: no findings.

   Read the diff of `src/factory/application/stage.py`, `src/factory/domain/labels.py`, `tests/domain/test_labels.py`, `tests/application/test_stage_finish.py` and `tests/application/test_stage_run.py` against the criteria and the Interface.
   - Criteria 1 to 23 each have a test that checks what the criterion says. The limits and failing sides are covered: tails of 20 and 10 lines, with make's error line and `line 6` absent. Red check, failing report, rejected push, failed label write, merge conflict and died run are all tested. `StageReport` is tested on both sides of each limit: rule 0/8 against 1–7/None, pull_request 0/1, commit of 39/40 characters, an unknown key, and frozen. The coder's entry 8 reports `make check` green.
   - `StageFinisher.finish` does the eight steps in the Interface's order. A red check goes through `StallService.stall` with the stage-start commit and the document that already holds the entry and the green-check lines. Only rule 6 resets `crashes`. Labels are written after the push, and `PushFailed` and `HostingServiceError` propagate unchanged. `StageRunner.run` handles the merge-conflict stall without launching the agent and reports every stall with rule `None`.
   - Layers hold: the application imports only application and domain, and `labels_for` lives in the domain. Commands run only through `ProjectCommands`. No suppression markers, secrets or string-built shell.
   - Considered and accepted: the red-check stall detail puts the command's name in front of the 15-line tail. It adds information and removes none, and the log (entries 4 and 8) records it as a design decision. The third private `_state_of` copy follows the existing pattern in `claims.py` and `stalls.py`; the coder noted it and left it alone as out of scope.
10. documenter: wrote the docs for the stage protocol. `make check` is green.

    Files changed:
    - `docs/project-guide.md`: added the section "The stage protocol". It covers the order `StageRunner.run` follows, `StageReport`, the eight steps of `StageFinisher.finish`, the red-check tail of 15 lines, reports that are recorded and never enforced, the `crashes` reset on a forward move, labels as a projection that is never read back, and the one result commit that holds the whole work tree. I also replaced three "(F0005-S0007)" forward references with pointers to that section: in "After the agent run", in "The decision rules" and in the rule 5 row of its table.
    - `docs/operator-guide.md`: added the section "A stall by a red check". It describes what the stall note and the journal look like on the pull request, what to do below and at the attempts cap, that reports never hold a move, and that the project's `.gitignore` must cover whatever its checks create.

    Cross-read and found current: the "Stalls" and "Starting a stage" sections of the project guide, and the "A stall: the stall note" and "The factory's own questions" sections of the operator guide. I checked the stall detail (command name, then the tail) against `src/factory/application/stage.py`. The docs did not describe the new classes, so nothing else needed fixing.

    Findings for the coder: none.

    Stale text seen but not touched: none that is unrelated to this story.

    `make check`: check: green
