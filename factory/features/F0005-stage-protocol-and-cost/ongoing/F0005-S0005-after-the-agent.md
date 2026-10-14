---
stage: accept
pr: 62
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# After the agent: the branch, the undo, the entry, the form again

## Assignment (as of log entry 7)

Build what the factory does with an agent run's outcome before it decides anything: it believes what it observes, not what the agent reports (kept thing 8). It tests that the checkout is still on the work item's branch, turns every result it cannot keep into a stall (the service of S0004), applies the undo and the restore of F0004 so that the agent's changes outside its write paths and to the state and journal are gone, writes the agent's entry with speaker and kind decided by code (the agent's text with a leading name removed), adds a paragraph naming what was undone, and checks the story form again so that only a finding that was not there before the run stalls. The entry is built here and appended by the stage's result commit (S0007); only in the form-stall case it is appended here, above the stall. Covers GH2.5 as the stage protocol applies it (a run that died or reached its `time_limit` becomes a stall through the service of S0004) and the undo and restore for the runs that complete; keeps kept things 1 (code writes speaker and kind), 4 (state and journal restored), 5 (the form is checked before and after) and 8.

## Interface

`src/factory/domain/decisions.py` (grown by this story; its tests are in a module of their own)

```python
def agent_entry(
    *, role: str, stage: str, decision: str, text: str, undone: Sequence[str]
) -> NewEntry | None: ...
```

`src/factory/application/stage.py` (grown by this story)

```python
class AgentAftermath(BaseModel):
    started: StartedStage
    request: AgentRunRequest
    result: AgentRunResult
    decision: str
    document: WorkItemDocument
    entry: NewEntry
    undo: UndoReport
    form_findings: list[FormFinding]

class AfterAgent:
    def __init__(
        self, boundaries: Boundaries, instance: str, definition: PipelineDefinition
    ) -> None: ...
    def process(self, launched: LaunchedStage) -> AgentAftermath | StallResult: ...
```

Types: `NewEntry` from `factory.domain.journal`, `UndoReport` from `factory.application.undo`, `StallResult` from `factory.application.stalls`, `cost_records_path` from `factory.domain.paths`. `AgentAftermath` is frozen and forbids unknown keys. `AgentAftermath.document` is the work item after the undo and the restore: the stage-start state (claim included) and journal, with the agent's changes to the rest of the body kept when the stage's role may write the work item (otherwise the undo has put the whole file back and lists it in `reverted`, F0004-S0005 c12); the entry is not yet in it.

- `agent_entry` returns `NewEntry(speaker=role, kind=..., text=..., on=None)`. `kind` is `question` when `decision == QUESTION`, else `result`. The text is `text` stripped, with one leading `<role>:` or `<stage>:` removed (the role first; the colon directly after the name; whitespace after it dropped) and stripped again. When the result is blank it returns `None`. When `undone` is not empty, the text ends with a blank line and `The factory undid changes outside the write paths: <the paths sorted and joined by ", ">.`
- `AfterAgent.process` does these steps in this order and stops at the first that stalls: (1) the checkout's branch (`Git.status().branch`) must be `started.branch`, else stall `left_branch`; (2) a result that is not `ok` stalls with `stall_reason_of(result)`, its detail the first permission denial as `denied: <tool>: <detail>` when there is one (the first of several); (3) a decision that is not in `request.allowed_decisions` stalls with `decision_not_allowed`, its detail `decision '<decision>' is not one of <the allowed decisions joined by ", ">`; (4) `UndoService.undo(stage_start, path)`, then the work item file is read back; (5) `agent_entry` with `undone` the sorted reverted and deleted paths of the report, leaving out `cost_records_path(started.path)` (the factory rewrites that file itself after the undo, S0008, so it is no change worth telling the agent about); a `None` result stalls with `no_result` and the detail `the entry is empty`; (6) `StoryFormChecker.findings(document)`; a finding that is new stalls with `form_invalid`, its detail the messages of the new findings joined by `; ` (in the order of the findings after the run), and the document passed to the stall holds the agent's entry appended, so the entry stays above the stall entry.
- A finding is new when its message, with every run of digits replaced by `#`, occurs more often among the findings after the run than among `started.findings`; the messages embed line numbers (`the code block opened at line 12 is not followed by an "Expect:" line`), which move when the agent adds a paragraph above. Of equal messages the first ones are taken as old and the later ones as new.
- Every stall goes through `StallService.stall` with `StallContext(work_item, stage, branch, path, stage_start=started.stage_start, document=<see above or None>, pull_request=started.pull_request)`, and the stage's `attempts` rises once per `process`, never twice.
- `AgentAftermath.form_findings` holds every finding after the run, new or old.

Tests: `tests/domain/test_agent_entry.py` (new, so that S0004's `tests/domain/test_decisions.py` stays as it is), `tests/application/test_after_agent.py`. The latter starts stages with `StageLauncher` and the fake agent runtime; `ScriptedRun.writes` tampers with the work item file, writes outside the write paths and breaks the form; a subclass of `ObservingRuntime` in this story's own test module switches the branch; `tests/observing_runtime.py` stays as S0003 wrote it. Criteria 8, 14, 16, 17 and 18, in which the agent edits the work item's body, run at a stage whose role may write the work item (`review`, role `reviewer`, write paths `{work_item}` in the fixture's pipeline definition); at `tests` the undo puts the whole file back. Unless a criterion breaks the form, the work items are complete stories (every section of the fixture's form, criteria ending with `make check` … `green` and `docs:`, a smoke-test block followed by `Expect:`), because the fixture's backlog story `# First story` has findings.

## Acceptance criteria

1. For a completed result with an allowed decision, `process` returns an `AgentAftermath` whose `decision` is the result's decision, whose `result` is the runtime's result and whose `started` is the launched stage's.
2. When the checkout is not on the work item's branch after the run, `process` returns a `StallResult` with reason `left_branch`.
3. For a result that ended `died`, `time_limit`, `budget` or `no_result`, `process` returns a `StallResult` with the same reason, and `attempts` rose by exactly one.
4. When a result that ended `died` carries a permission denial for tool `Bash` with detail `git push origin main`, the stall note contains `denied: Bash: git push origin main`; with a second denial for tool `Edit`, the note names the first and not the second.
5. A decision that is not allowed (`review` at a stage whose `next` is `doing`) stalls with `decision_not_allowed`; the journal entry of the stall names the decision and the allowed decisions.
6. A file the agent wrote outside its write paths is gone from the work tree after `process`, and `AgentAftermath.undo` lists it under `reverted` or `deleted`.
7. An agent that rewrote the work item file's state and journal (another `stage`, `attempts` and `claim`, a changed journal) leaves `AgentAftermath.document` with the stage-start state, claim included, and the stage-start journal records.
8. An agent's own edit inside the work item file's body (a paragraph added under a section) is kept in `AgentAftermath.document` and in the work tree at a stage whose role may write the work item (`review`); at a stage whose role may not (`tests`) the edit is gone from `AgentAftermath.document` and from the work tree, and the work item's path is in `AgentAftermath.undo.reverted`.
9. `AgentAftermath.entry` has speaker equal to the stage's role, kind `result` and the agent's text for a decision that is not `question`.
10. For the decision `question` the entry's kind is `question` and its speaker is the role.
11. A leading `<role>:` and a leading `<stage>:` in the agent's text are removed once (`tester: wrote tests` gives `wrote tests`), whitespace after the colon dropped; the same words in the middle of the text, and a name without a colon, stay.
12. When the undo reverted or deleted paths, the entry text ends with a blank line and `The factory undid changes outside the write paths: <paths sorted, joined by ", ">.`; when nothing was undone the text has no such paragraph.
13. An entry that is blank after the prefix is removed (`"tester: "`) stalls with `no_result` and the detail `the entry is empty`.
14. When the agent breaks the story form (its `## Acceptance criteria` section is deleted), `process` returns a `StallResult` with reason `form_invalid`, and in the pushed journal the agent's record (the role, kind `result`) comes directly before the `factory` stall record.
15. A form finding that exists before and after the run does not stall (`process` returns an `AgentAftermath` and `form_findings` lists it), and a finding the agent fixed does not stall either.
16. A finding whose message carries a line number does not stall when only the number changed: a smoke-test code block without `Expect:` exists before the run, the agent adds a paragraph above it, and `process` returns an `AgentAftermath`.
17. A second finding of the same kind is new: the agent adds a second smoke-test code block without `Expect:` to a story that had one, and `process` returns a `StallResult` with reason `form_invalid`, and the note of the stall contains the message of the added second block (with its line number) and not the message of the original block.
18. The note of a `form_invalid` stall holds the messages of the new findings joined by `; `: the agent adds two new findings (it deletes the criteria section and the smoke test section) and the note contains both messages with `; ` between them, the old finding's message not among them.
19. `AgentAftermath.form_findings` lists all findings after the run, and a stage that ends clean has an empty list.
20. The own work item's cost-record file is not an undone path: an agent that overwrote the sidecar at `cost_records_path(path)` and wrote `src/b.py` outside its write paths gets an entry whose paragraph names `src/b.py` and not the sidecar; an agent that wrote only the sidecar gets an entry without the paragraph.
21. `AgentAftermath` is frozen and forbids unknown keys: assigning to `decision` (through `setattr`, the field's name in a variable) and building it with an unknown field raise `ValidationError`.
22. make check stays green.
23. docs: `docs/project-guide.md` describes what the factory does after an agent run, in order (branch test, stall on a result it cannot keep, undo and restore, the entry written by code with its prefix removed, the form checked again so that only a new finding stalls, new meaning more often than before once digits are masked), and that the agent's state and journal edits are always discarded and the own cost-record file is not named in the entry.

## Demo

```bash
uv run python -c "
from factory.domain.decisions import agent_entry
entry = agent_entry(role='tester', stage='tests', decision='doing', text='tester: wrote the tests', undone=['src/b.py', 'README.md'])
print(entry.speaker, entry.kind)
print(entry.text)
print(agent_entry(role='tester', stage='tests', decision='question', text='tester:   ', undone=[]))
"
```
Expect: 5 lines. Line 1 is `tester result`. Lines 2 to 4 are `wrote the tests`, an empty line, and `The factory undid changes outside the write paths: README.md, src/b.py.` Line 5 is `None`.

```bash
uv run pytest tests/application/test_after_agent.py
```
Expect: the last line reports `passed` and the output contains neither `failed` nor `error`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `agent_entry`, `AgentAftermath` and `AfterAgent.process` are named with module paths and signatures. The six steps, their order, their stall reasons and details, and the "new finding" rule are stated precisely. The interface comments on kind, prefix removal, the paragraph and the cost-record exclusion are all behaviours with criteria.
   - Criteria: each is testable by one test function. Every rule has its failing side: left branch (2), non-ok results (3, 4), disallowed decision (5), blank entry (13), new finding stalls against old or fixed finding not stalling (14, 15, 16, 17, 18), the paragraph present and absent (12, 20), frozen and unknown keys (21). Criterion 8 covers both the role that may write the work item and the role that may not.
   - Demo: both commands are runnable. The first Expect has five lines, which matches what the code would print (`tester result`, `wrote the tests`, an empty line, the paragraph, `None`). The second Expect is checkable against pytest output.
   - Architecture: `agent_entry` is pure and sits in the domain. `AfterAgent` is in the application layer and uses the S0004 stall service, the F0004 undo service and the form checker, all through interfaces. It adds no dependency and no top-level package.
   - Scope: this is the feature's "After the agent" item. It covers decisions 13, 14, 15, 27 and 28 and stays out of the decision rules (S0006) and the result commit (S0007).
3. tester: Wrote red tests for every criterion except 22 and 23. One `make test` run fails with 2 collection errors, both from missing names: `agent_entry` in `factory.domain.decisions` and `AfterAgent`/`AgentAftermath` in `factory.application.stage`. `make lint` is green. The type check was skipped as the stage says.

   Files created: `tests/domain/test_agent_entry.py`, `tests/application/test_after_agent.py`.

   Criterion → test:
   - criterion 1: tests/application/test_after_agent.py::test_a_completed_run_with_an_allowed_decision_gives_its_aftermath
   - criterion 2: tests/application/test_after_agent.py::test_a_checkout_left_on_another_branch_stalls_as_left_branch (the module's own `SwitchingRuntime(ObservingRuntime)`)
   - criterion 3: tests/application/test_after_agent.py::test_a_run_that_did_not_complete_stalls_with_its_reason_and_one_attempt_more (died, time_limit, budget, no_result)
   - criterion 4: tests/application/test_after_agent.py::test_the_stall_note_names_the_first_permission_denial (one denial; two denials)
   - criterion 5: tests/application/test_after_agent.py::test_a_decision_that_is_not_allowed_stalls_naming_it_and_the_allowed_ones
   - criterion 6: tests/application/test_after_agent.py::test_a_file_written_outside_the_write_paths_is_undone_and_reported
   - criterion 7: tests/application/test_after_agent.py::test_the_agents_state_and_journal_edits_give_way_to_the_stage_start (at review)
   - criterion 8: tests/application/test_after_agent.py::test_a_body_edit_is_kept_only_where_the_role_may_write_the_work_item (review kept; tests reverted)
   - criterion 9: tests/application/test_after_agent.py::test_the_entry_is_the_roles_result_with_the_agents_text; tests/domain/test_agent_entry.py::test_a_result_entry_is_spoken_by_the_role_with_the_agents_text
   - criterion 10: tests/application/test_after_agent.py::test_a_question_gives_a_question_entry_spoken_by_the_role; tests/domain/test_agent_entry.py::test_a_question_entry_has_kind_question_and_the_role_as_speaker
   - criterion 11: tests/domain/test_agent_entry.py::test_a_leading_role_or_stage_name_is_removed_once; tests/application/test_after_agent.py::test_the_entry_loses_a_leading_role_or_stage_name
   - criterion 12: tests/domain/test_agent_entry.py::test_undone_paths_end_the_text_with_a_paragraph_sorted_and_joined and ::test_nothing_undone_adds_no_paragraph; tests/application/test_after_agent.py::test_undone_paths_are_named_in_a_last_paragraph_of_the_entry
   - criterion 13: tests/domain/test_agent_entry.py::test_a_blank_text_after_the_prefix_gives_no_entry; tests/application/test_after_agent.py::test_an_entry_blank_after_the_prefix_stalls_as_no_result
   - criterion 14: tests/application/test_after_agent.py::test_a_broken_form_stalls_with_the_agents_entry_right_above_the_stall (also checks attempts +1)
   - criterion 15: tests/application/test_after_agent.py::test_a_finding_present_before_and_after_the_run_does_not_stall and ::test_a_finding_the_agent_fixed_does_not_stall
   - criterion 16: tests/application/test_after_agent.py::test_a_finding_whose_line_number_moved_does_not_stall
   - criterion 17: tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls
   - criterion 18: tests/application/test_after_agent.py::test_the_form_stall_note_joins_only_the_new_findings (the old finding is a missing `## Interface`)
   - criterion 19: tests/application/test_after_agent.py::test_the_aftermath_lists_every_finding_after_the_run (clean; with a finding)
   - criterion 20: tests/application/test_after_agent.py::test_the_own_cost_record_file_is_not_named_as_undone (with an outside file; sidecar only)
   - criterion 21: tests/application/test_after_agent.py::test_the_aftermath_is_frozen_and_forbids_unknown_keys
   - criteria 22 and 23 are not test criteria: `make check` and the docs.

   Notes for the coder:
   - In the agent-edit tests the agent writes the work item file with a state of its own choosing: the branch body plus a different state, without the stage-start claim. The tests rely on the undo and restore putting the stage-start state and journal back.
   - The domain test expects `None` for a blank text even when `undone` is not empty. This follows the Interface, where the blank check comes before the paragraph.
   - Criterion 5 builds the allowed list from `request.allowed_decisions` joined by ", ".

   Modules the test runner could not import: `factory.domain.decisions.agent_entry`, `factory.application.stage.AfterAgent` and `AgentAftermath`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Implemented the code that runs after the agent. `make check` is green and coverage is 99.47 %. All tests in `tests/domain/test_agent_entry.py` and `tests/application/test_after_agent.py` pass, and no test was touched.

   Built:
   - `src/factory/domain/decisions.py`: `agent_entry`. It strips the text, removes one leading `<role>:` or else `<stage>:` (role first, so `tester: tests: x` gives `tests: x`), strips again and returns `None` when the text is blank. When `undone` is not empty it adds the sorted paragraph. The kind is `question` exactly when the decision is `QUESTION`.
   - `src/factory/application/stage.py`: `AgentAftermath` (frozen, extra forbidden) and `AfterAgent.process`. The six steps run in the Interface's order: branch through `Git.status()`, then `stall_reason_of` with the first permission denial as detail, then the allowed decisions, then `UndoService.undo` and a read-back of the work item, then the entry with `cost_records_path(path)` left out of the undone paths, then `StoryFormChecker`.
     - New findings come from a `Counter` of messages with every run of digits masked as `#`. The earlier equal findings use up the old count, so the later ones are new.
     - Every stall goes through `StallService.stall` with the started stage's context, so attempts rise exactly once. Only the `form_invalid` stall passes a document, the undone work item with the agent's entry appended, so that entry sits directly above the stall entry. The other stalls pass `None` and let the stall service read the file after its own undo.
   - Commits: 48b1e27 (feat) and beecd7f (refactor: a private helper's docstring became a comment, per the docstring rule).

   Main design decision: the stall paths reuse `StallService` unchanged. Its own undo handles the left-branch case (reset and re-checkout), and running it again after this story's undo does nothing new. Rejected: a separate stall path for the late steps that skips the second undo. It would have duplicated the commit, push and note logic.

   Noticed but not touched:
   - `AfterAgent._entry` raises `ValueError` for a stage without a role. A stage without a role cannot have been launched, so that line is uncovered.
   - The `decision is None` check exists only to satisfy the type checker, because `AgentRunResult`'s validator already guarantees a decision when the run completed.

   Docs (criterion 23) are left for the documenter.

   `make check`: check: green
5. reviewer: Sent back to doing with one finding. It is a gap in the story's criteria, not a fault in the code.

   1. `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls` (criterion 17) has a gap.
      - **Rule:** the Interface says that among equal masked messages, the first ones count as old and the later ones as new.
      - **Gap:** no test checks this. The test asserts only `stalled.reason == "form_invalid"`, and no criterion says which of the two equal findings the stall note names. If the code took the first code block as the new one, every test would still pass.
      - **Fix:** this needs a story criterion first, so the coder should ask the human (R8/R9) to add one. The proposed criterion: in criterion 17's case, the note of the `form_invalid` stall contains the message of the added second block (its line number) and not the message of the original block. With the human's answer, the tester then extends criterion 17's test to check it.

   Checked and found sound:
   - **`agent_entry`:** in `src/factory/domain/decisions.py`, it removes the role prefix before the stage prefix, strips, returns `None` when blank, and adds the sorted paragraph.
   - **The six steps:** `AfterAgent.process` in `src/factory/application/stage.py` runs them in the Interface's order with its reasons and details, and passes every stall through `StallService.stall`. Only the `form_invalid` stall carries a document, the one with the agent's entry appended. Running the stall service's undo a second time does nothing new, so attempts rise once.
   - **New findings:** the masked `Counter` takes the earlier equal findings as the old ones.
   - **Cost records:** the cost-record file is left out of the undone paths.
   - **The model:** `AgentAftermath` is frozen and forbids unknown keys.
   - **Tests:** every other criterion from 1 to 21 has a test that checks what the criterion says, in the domain test module and in the application test module.
   - **Architecture:** the layers hold, all four interfaces are used, there is no new dependency and no suppression marker.
   - **Docstrings:** they are present and say what things are.
   - **`make check`:** green, per the coder's entry.
6. coder: Round 1. The reviewer's one finding is a gap in the story's criteria, so I have to ask before anything can change. No code or test was touched in this round.

   The gap: the Interface says that among equal masked messages, the first ones are old and the later ones are new. `_new_findings` in `src/factory/application/stage.py` does this already: a `Counter` of the masked messages from before the run is used up by the earlier findings after the run. But no criterion says which of two equal findings the `form_invalid` note names. `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls` checks only `stalled.reason == "form_invalid"`, so code that called the original block the new one would still pass.

   Question: should criterion 17 be extended to pin this down?
   - (a) Yes, extend it. Proposed wording, added to criterion 17: "… and the note of the stall contains the message of the added second block (with its line number) and not the message of the original block." The tester then adds that assertion to `test_a_second_finding_of_the_same_kind_stalls`, and I rerun the stage. The current code should pass it without a change.
   - (b) No, leave criterion 17 as it is. Then the order rule stays in the Interface with no test for it, and the reviewer's finding is dismissed.

   I recommend (a). It is one sentence in the criteria and one assertion in an existing test, and it closes the one untested side of a rule the Interface states.

   `make check`: green as of the round-0 commits (48b1e27, beecd7f); nothing has changed since.
7. human (pull request comment, 2026-10-14): (a): extend criterion 17 as you worded it ("… and the note of the stall contains the message of the added second block (with its line number) and not the message of the original block."). The tester adds that assertion to `test_a_second_finding_of_the_same_kind_stalls`. End with `tests` and name exactly that change.
8. coder: Round 1. The human chose option (a), so this round goes to the tester for one test change. I did not touch any code or test.

   The change for the tester: in `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls`, keep the existing `reason == "form_invalid"` check and add an assertion that the stall note contains the message of the added second smoke-test block (with its line number) and does not contain the message of the original block.

   Ticket: I added the human's wording to criterion 17 ("… and the note of the stall contains the message of the added second block (with its line number) and not the message of the original block.") and moved the Assignment heading to "as of log entry 7".

   Open: I expect the current `_new_findings` in `src/factory/application/stage.py` to pass the new assertion without a change. It takes the earlier equal findings as old, so the second block's finding counts as new. Once the tester has added the assertion, the next doing stage checks this. `make check`: not run this round; it was green at beecd7f and no code has changed since.
9. tester: Round 1, the test change the human approved in entry 7 and the coder named in entry 8. Only `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls` was changed.

   The change:
   - The test now takes the `hosting` fixture and reads the stall note through `_note`.
   - The existing `reason == "form_invalid"` check stays.
   - The test now checks that the note contains the message of the added second smoke-test block and does not contain `original.message`, the message of the original block.
   - The added block's message is built from the original finding by moving its line number from `original.line` to `original.line + 4`, because the added block opens four lines below the original one. If that replacement ever stopped working, the two checks would contradict each other and the test would fail rather than pass by accident.
   - The old `len(launched.started.findings) == 1` check is now the unpacking `[original] = launched.started.findings`.

   Result: as the coder expected, the current `_new_findings` passes the new assertion. `make test`: test: green (coverage 99.47 %). `make lint`: lint: green.

   `make lint`: lint: green
   `make test`: test: green
10. coder: Round 1. I did not touch any code or test. The current `_new_findings` passes the tester's new assertion at runtime: `make test` is green. But `make check` is red at `make types`, and the error is in the test the tester changed in entry 9:

    `tests/application/test_after_agent.py:681: error: Unsupported operand types for + ("None" and "int")  [operator]`. The left operand is `original.line`, which is typed `int | None` because `FormFinding.line` is `PositiveInt | None`.

    The change for the tester: in `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls`, add `assert original.line is not None` directly after `[original] = launched.started.findings`. mypy then narrows the type before `original.line + 4`, and the assertion itself does not change.

    The code needs no change, because this is a typing fault in the test, not a behaviour gap. The feature and refactor commits are still 48b1e27 and beecd7f. Once the test is fixed, the next doing stage only reruns `make check` and hands on to review.

    `make check`: red. `make lint`: green. `make types`: 1 error, in the test file only.
11. tester: Round 1. I made the test change the coder named in entry 10, and only that change.

    The change: in `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls`, I added `assert original.line is not None` directly after `[original] = launched.started.findings`. It narrows `original.line` from `int | None` to `int`, so mypy accepts `original.line + 4` on the next line. The test's assertions about the stall reason and the note are unchanged.

    I did not run `make types`, because this stage skips the type check. The next doing stage's `make check` covers it.

    `make test`: test: green (coverage 99.47 %). `make lint`: lint: green.

    `make lint`: lint: green
    `make test`: test: green
12. coder: Round 1. `make check` is now green, and I did not change any code or test in this round.

    - The reviewer's one finding, the gap in criterion 17, is closed. The human extended the criterion in entry 7, and the tester added the note assertions in entries 9 and 11 to `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls`.
    - The tester's `assert original.line is not None` fixed the mypy error I reported in entry 10, so `make types` passes.
    - The current `_new_findings` in `src/factory/application/stage.py` passes the new assertion without a change. It counts the earlier of two equal findings (masked messages) as old, so the stall note names the second block and not the original one.

    The code is still the round-0 commits: 48b1e27 (feat) and beecd7f (refactor). There was nothing new to refactor.

    Still open from entry 4: the uncovered line where `AfterAgent._entry` raises for a stage without a role (line 99), and the `decision is None` guard that exists only for the type checker (line 192). Criterion 23 (docs) is left for the documenter.

    `make check`: check: green (coverage 99.47 %)

    `make check`: check: green
13. reviewer: Round 1. No findings, so the story goes on to docs.

    - **Round-0 finding is closed.** Criterion 17 now pins which of two equal findings is new. `tests/application/test_after_agent.py::test_a_second_finding_of_the_same_kind_stalls` builds the added block's message from the original finding with its line number moved by four. I counted the lines in `doubled`: the added block's fence really is four lines below the original. The test asserts that the note contains that message and not `original.message`. In `src/factory/application/stage.py`, `_new_findings` lets the earlier equal findings use up the old count, so this assertion checks the Interface's ordering rule.
    - **Acceptance criteria 1–21:** each has a test that checks what the criterion says, and the refused sides are covered. The criteria and their tests:
      - non-ok results (3, 4), including attempts going up by exactly one on the pushed state;
      - the disallowed decision, with its detail in the journal (5);
      - the body edit kept at `review` and reverted at `tests` (8);
      - prefix removal, with in-the-middle, no-colon and space-before-colon cases (11);
      - the paragraph present and absent (12, 20);
      - a blank entry with and without undone paths (13);
      - the form findings: new, old, fixed, moved line number, second of a kind, and the `; ` join (14–18);
      - frozen and unknown keys (21).
    - **`make check`:** green per the coder's entry 12.
    - **Architecture:** `agent_entry` is pure and sits in `factory.domain.decisions`. `AfterAgent` is in the application layer and reaches git, the reader and the stall and undo services only through `Boundaries`. There is no new dependency and no top-level package.
    - **Security:** there are no suppression markers, secrets or command strings.
    - **Quality:** every public name has its docstring, and the comments say why (masking line numbers, the earlier findings counted as old, the sidecar left out).
      - Left as it is: the role-less `ValueError` in `_entry` and the `decision is None` guard. Both are defensive code the coder explained in entry 4, not dead logic.
      - Left as it is: `agent_entry` sorts `undone` itself, as the Interface asks, even though the caller already sorts.
    - **Ticket hygiene:** the log explains the main decision (reusing `StallService` unchanged, which runs its own undo a second time without effect) and what was rejected. The Assignment matches what was built. Criterion 23 still describes what the documenter must write.
14. documenter: Docs round 1. Changed `docs/project-guide.md`. I added a section "After the agent run" before the kill-points section. It covers criterion 23 in order:
    - the branch test;
    - the stalls for results the factory cannot keep;
    - the undo and restore, including that the agent's state and journal edits are always discarded;
    - `agent_entry` (speaker and kind decided by code, the name prefix removed, the undone paragraph, the cost-record file not named);
    - the form check after the run, where only a new finding stalls, line numbers are masked, and a kind that occurs more often than before counts as new;
    - `AgentAftermath` and its tests.

    I also replaced the last sentence of the undo section, "When it runs and what the entry says about it are F0005's", with a pointer to the new section.

    Cross-read against the diff: the Stalls and Starting-a-stage sections are still true. There is nothing for README or the operator guide, because this story adds nothing the operator sees.

    Findings: none. The code matches the Interface. I wrote no runnable examples. `make check` is green.

    `make check`: check: green
15. demo: Ran both demo commands from the repository root, exactly as written. Both met their `Expect:` lines.

    1. `agent_entry` snippet (exit 0):
    ```
    tester result
    wrote the tests

    The factory undid changes outside the write paths: README.md, src/b.py.
    None
    ```
    Met. It printed 5 lines. Line 1 is `tester result`. Lines 2–4 are the text with the leading `tester:` removed, a blank line, and the undo paragraph with the paths sorted and joined by `, `. Line 5 is `None` for the text that is blank once its prefix is removed.

    2. `uv run pytest tests/application/test_after_agent.py` (exit 0):
    ```
    .................................                                        [100%]
    33 passed in 6.40s
    ```
    Met. The last line reports `passed`, and the output contains neither `failed` nor `error`.

    I checked the output against all acceptance criteria and found no contradictions. It agrees with criteria 9 (speaker and kind), 11 (prefix removed once, whitespace dropped), 12 (undo paragraph, sorted paths) and 13 (an empty entry gives no entry, so the stage stalls). No findings. Nothing is open.
