---
stage: demo
pr: 63
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The decision rules: questions, rework rounds and caps

## Assignment (as of log entry 1)

Build v1's decision rules 1, 2, 3, 4, 6 and 7 as one pure function over the pipeline definition, the work item's state and the agent's decision: a forward decision while the form has findings after the run (S0007 passes them) becomes a question to the human; a `question` blocks the work item; a rework (a decision other than the first of `next`) counts a round against the stage's `round_cap` and, past it, asks the human instead of looping; a rework at a stage with no `round_cap` simply moves; a forward decision with no findings moves to `next[0]`, with its checks still to be run by S0007 (rule 5, the red check, is S0007's). Rules are tried in the order 1, 2, 3, 4, 6, 7 as v1 numbers them. The function decides stage, `blocked`, `round` and the text of a question the factory itself adds to the journal; it never touches `attempts` or `crashes`; S0007 resets `crashes` on a forward move (a rework and a stall are counted apart, kept thing 14). The factory's own question texts for the findings and the round cap are built here too. Covers kept things 1 (code decides what the decision means), 10 (a question always blocks) and 14.

## Interface

`src/factory/domain/decisions.py` (grown by this story)

```python
class StageMove(BaseModel):
    rule: Literal[1, 2, 3, 4, 6, 7]
    stage: Name
    blocked: Blocked | None
    round: NonNegativeInt
    question: str | None

def decide(
    definition: PipelineDefinition,
    state: WorkItemState,
    decision: str,
    findings: Sequence[FormFinding] = (),
) -> StageMove: ...
```

`src/factory/domain/post_texts.py` (grown by this story)

```python
def round_cap_question(rounds: int, cap: int) -> str: ...
def findings_question(findings: Sequence[FormFinding]) -> str: ...
```

Types: `Blocked` and `WorkItemState` from `factory.domain.work_item`, `FormFinding` from `factory.domain.story_form`, `PipelineDefinition` from `factory.domain.pipeline_definition`. `StageMove` is frozen and forbids unknown keys. A decision is "forward" when it equals `next[0]` of the state's stage, and a "rework" when it is another entry of `next`; this is the one rule for counting rounds (FEATURE decision 26), whatever the position of the stage the rework names in the pipeline definition. The interface sheet's `PipelineDefinition.position` is not used to count rounds. `post_texts` imports `StallReason` only under `TYPE_CHECKING` (with `from __future__ import annotations`, as `factory.domain.journal` does), because `decisions` now imports `post_texts`.

- The state's stage is looked up in `definition.stages`; a stage that is not there raises `ValueError` naming it. A decision that is neither in the stage's `next` nor `question` raises `ValueError` naming the decision.
- Rule 1: a forward decision with a non-empty `findings` gives stage unchanged, `blocked="question"`, `round` unchanged, `question=findings_question(findings)`.
- Rule 2: the decision `question` gives stage unchanged, `blocked="question"`, `round` unchanged, `question=None` (the agent's own entry is the question). Findings do not matter.
- Rule 3: a rework at a stage with `round_cap`, where `state.round + 1 <= round_cap`, gives `stage=<the decision>`, `round=state.round + 1`, `blocked=None`, `question=None`.
- Rule 4: a rework at a stage with `round_cap`, where `state.round + 1 > round_cap`, gives stage unchanged, `round=state.round + 1`, `blocked="round_cap"`, `question=round_cap_question(state.round + 1, round_cap)`.
- Rule 6: a forward decision with no findings gives `stage=next[0]`, `blocked=None`, `round` unchanged, `question=None`. Whether its checks are green is decided by S0007; this function only says the move.
- Rule 7: a rework at a stage without `round_cap` gives `stage=<the decision>`, `round` unchanged, `blocked=None`, `question=None`.
- `findings` matter only to a forward decision.
- `round_cap_question(rounds, cap)` returns `This work item has now been sent back <rounds> times, more than <cap>. What should happen? Answer with a comment; close the pull request to discard the work item.`
- `findings_question(findings)` returns `The work item's form has findings, so the stage cannot move forward: <1. m1 2. m2>. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.` where the numbered messages are numbered from 1 and joined by one space.

Tests: `tests/domain/test_decision_rules.py` and `tests/domain/test_question_texts.py` (both new, so that the modules of S0004 and of F0003 stay as they are). `StageMove` refuses what its types refuse (a `rule` outside 1, 2, 3, 4, 6 and 7, a negative `round`, an unknown key), tested on both sides (criterion 16). The pipeline definition is the fixture's: `doing` has `next` `review`, `tests` and no `round_cap`; `review` has `next` `docs`, `doing` and `round_cap` 3.

## Acceptance criteria

1. A forward decision with no findings (`docs` at stage `review`) returns rule 6 with `stage="docs"`, `blocked=None`, the state's `round` and `question=None`.
2. A forward decision with findings (`review` at stage `doing`, one finding) returns rule 1 with the stage unchanged, `blocked="question"`, the state's `round` and `question` equal to `findings_question` of the findings.
3. The decision `question` returns rule 2 with the stage unchanged, `blocked="question"`, the state's `round` and `question=None`.
4. The decision `question` with findings still returns rule 2 with `question=None`: findings turn only a forward decision into a question.
5. A rework at a stage with a `round_cap` (`doing` at stage `review`, `round_cap` 3) with the state's round 0 returns rule 3 with `stage="doing"`, `round=1`, `blocked=None` and `question=None`.
6. The cap is a limit tested on both sides: with `round_cap` 3 the states with round 0, 1 and 2 give rule 3 (the new round is at most 3), and the state with round 3 gives rule 4.
7. Rule 4 for the state with round 3 at stage `review` returns the stage unchanged, `round=4`, `blocked="round_cap"` and `question` equal to `round_cap_question(4, 3)`.
8. A rework at a stage without `round_cap` (`tests` at stage `doing`) returns rule 7 with `stage="tests"`, the state's `round` and `blocked=None`, `question=None`.
9. Findings do not change a rework: `doing` at stage `review` with findings returns rule 3, as without them.
10. A state whose `blocked` is `question` gives `blocked=None` for rules 3, 6 and 7: the move clears it.
11. A decision that is not in the stage's `next` and is not `question` raises `ValueError` whose message names the decision.
12. A state whose stage is not in the pipeline definition raises `ValueError` whose message names the stage.
13. `StageMove` has exactly the fields `rule`, `stage`, `blocked`, `round` and `question`: it says nothing about `attempts` or `crashes`, which the result commit handles (S0007).
14. `round_cap_question(4, 3)` returns exactly `This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment; close the pull request to discard the work item.`
15. `findings_question` for two findings with messages `a` and `b` returns exactly `The work item's form has findings, so the stage cannot move forward: 1. a 2. b. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.`
16. `StageMove` refuses what its types refuse, on both sides: `rule` 1, 2, 3, 4, 6 and 7 and `round` 0 are accepted, `rule` 5 and `round` -1 raise `ValidationError`; assigning to `stage` (through `setattr`, the field's name in a variable) raises `ValidationError`; and an unknown key raises `ValidationError` (built through a variable typed `type[BaseModel]`).
17. make check stays green.
18. docs: `docs/project-guide.md` lists the decision rules in their order (1, 2, 3, 4, 6, 7 here, 5 in the checks) with what each does to the stage, `blocked` and `round`, and says that a rework counts rounds and a stall counts attempts, apart; `docs/operator-guide.md` explains the two questions the factory asks by itself (the form findings, the round cap) and the answers it accepts.

## Demo

```bash
uv run python -c "
from factory.domain.decisions import decide
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemState
definition = PipelineDefinition(contract='1.0', roles={'reviewer': RoleDefinition(write_paths=['{work_item}']), 'coder': RoleDefinition(write_paths=['src/*'])}, stages={'review': StageDefinition(role='reviewer', next=['docs', 'doing'], round_cap=2), 'docs': StageDefinition(role='reviewer', next=['done']), 'doing': StageDefinition(role='coder', next=['review']), 'done': StageDefinition()})
for rounds in (0, 1, 2):
    move = decide(definition, WorkItemState(stage='review', round=rounds), 'doing')
    print(rounds, move.rule, move.stage, move.round, move.blocked)
print(move.question)
print(decide(definition, WorkItemState(stage='review'), 'docs').rule)
print(decide(definition, WorkItemState(stage='review'), 'question').blocked)
"
```
Expect: 6 lines. Lines 1 to 3 are `0 3 doing 1 None`, `1 3 doing 2 None` and `2 4 review 3 round_cap`. Line 4 is `This work item has now been sent back 3 times, more than 2. What should happen? Answer with a comment; close the pull request to discard the work item.` Line 5 is `6`. Line 6 is `question`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `decide`, `StageMove`, `round_cap_question` and `findings_question` are named with modules and signatures. The types come from existing modules. The TYPE_CHECKING import of `StallReason` is specified. The "forward = next[0], rework = other entry" rule is explicit.
   - Criteria: each is testable by one test function. Every rule has its failing side: rule 4 covers the cap on both sides (criterion 6, rounds 0 to 3). Unknown decision (11) and unknown stage (12) raise ValueError. Rule 2 with findings (4) and findings with a rework (9) are covered. `blocked` clearing is covered (10). Both texts are exact (14, 15). The `StageMove` limits are tested on both sides (16).
   - Demo: the command is runnable and matches the Interface. I traced the output. Rounds 0 and 1 give rule 3. Round 2 gives rule 4, stage review, round 3 and `round_cap`. The question text for 3 and 2 follows the template. The last two lines are 6 and `question`, six lines in all. Each `Expect:` line is checkable.
   - Architecture: the code is pure domain, with no I/O. `post_texts` and `decisions` stay in `factory.domain`. The import direction is stated, so there is no layer problem.
   - Scope: within F0005 (decision rules 1 to 4, 6 and 7). Rule 5 and `crashes` are left to S0007, and decisions 16, 17 and 26 are respected. Nothing is out of scope.
3. tester: Wrote the tests for the decision rules and the factory's own question texts. In `tests/domain/test_decision_rules.py`, a local fixture `definition` builds the pipeline: `doing` has next review, tests and no round_cap; `review` has next docs, doing and round_cap 3. Its other stages are tests, docs and done.
   - criterion 1: tests/domain/test_decision_rules.py::test_a_forward_decision_without_findings_moves_to_the_first_next_stage
   - criterion 2: tests/domain/test_decision_rules.py::test_a_forward_decision_with_findings_becomes_a_question
   - criterion 3: tests/domain/test_decision_rules.py::test_the_decision_question_blocks_the_work_item_at_its_stage
   - criterion 4: tests/domain/test_decision_rules.py::test_findings_do_not_add_a_question_to_the_decision_question
   - criterion 5: tests/domain/test_decision_rules.py::test_a_rework_within_the_round_cap_moves_and_counts_a_round
   - criterion 6: tests/domain/test_decision_rules.py::test_a_rework_past_the_round_cap_asks_the_human (parametrized: rounds 0, 1 and 2 give rule 3; round 3 gives rule 4; the new round is rounds + 1)
   - criterion 7: tests/domain/test_decision_rules.py::test_a_rework_past_the_round_cap_stays_blocked_with_the_round_cap_question
   - criterion 8: tests/domain/test_decision_rules.py::test_a_rework_at_a_stage_without_round_cap_moves_without_counting
   - criterion 9: tests/domain/test_decision_rules.py::test_findings_do_not_change_a_rework
   - criterion 10: tests/domain/test_decision_rules.py::test_a_move_clears_a_blocked_question (parametrized over rules 3, 6 and 7)
   - criterion 11: tests/domain/test_decision_rules.py::test_a_decision_outside_next_is_refused_by_name (decision `done` at stage `review`)
   - criterion 12: tests/domain/test_decision_rules.py::test_a_stage_outside_the_pipeline_definition_is_refused_by_name
   - criterion 13: tests/domain/test_decision_rules.py::test_a_stage_move_has_no_attempts_or_crashes
   - criterion 14: tests/domain/test_question_texts.py::test_the_round_cap_question_names_the_rounds_and_the_cap
   - criterion 15: tests/domain/test_question_texts.py::test_the_findings_question_numbers_the_findings_messages
   - criterion 16: tests/domain/test_decision_rules.py::test_a_stage_move_accepts_each_rule (rules 1, 2, 3, 4, 6 and 7 with round 0), ::test_a_stage_move_refuses_what_its_types_refuse (rule 5, round -1 and an unknown key, each built through `type[BaseModel]`) and ::test_a_stage_move_is_frozen (setattr on `stage`)
   - criteria 17 and 18: not test criteria (make check, docs).

   Files created: tests/domain/test_decision_rules.py and tests/domain/test_question_texts.py.

   `make test` stopped at collection with 2 errors, one for each new file. The test runner could not import `StageMove` and `decide` from `factory.domain.decisions`, or `findings_question` and `round_cap_question` from `factory.domain.post_texts`. `make lint` is green. Nothing open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: I built the decision rules. All tests pass and `make check` is green. The demo prints the six expected lines.
      - `src/factory/domain/decisions.py`: `StageMove` (frozen, `extra="forbid"`) and `decide`. `decide` looks up the stage and raises `ValueError` naming an unknown stage or a decision outside `next`/`question`. It then tries the rules in order 1, 2, 6, 7, 3/4. Each rule's conditions exclude the others, so this is the same result as v1's order 1, 2, 3, 4, 6, 7. Two private helpers do the work: `_stay` (rules 1 and 2) and `_move` (rules 3, 6 and 7, which always clear `blocked`). It never touches `attempts` or `crashes`.
      - `src/factory/domain/post_texts.py`: `round_cap_question` and `findings_question`. The module now uses `from __future__ import annotations` and imports `StallReason` and `FormFinding` only under `TYPE_CHECKING`, as the Interface says. This breaks the import cycle now that `decisions` imports `post_texts`.
      - Main decision: "forward" is `stage.next[:1] == [decision]` and every other entry of `next` is a rework. Rounds are counted from the order of `next` alone, as FEATURE decision 26 says. I rejected comparing stage positions in the pipeline definition (`PipelineDefinition.position`), which the Interface rules out.
      - Refactor pass: after the first lint run I made `_move` take no state and renamed its `round` parameter to `rounds`, so it no longer shadows the builtin. That change is in the same commit (7b2d1fb). The final diff needed nothing further, so there is no separate refactor commit.
      - Open: docs criterion 18 is for the documenter. Nothing else noticed.

   `make check`: check: green
5. reviewer: No findings.

   - Acceptance criteria: criteria 1 to 16 each have a test in `tests/domain/test_decision_rules.py` or `tests/domain/test_question_texts.py`, and each test checks what its criterion says. The round cap is tested on both sides: rounds 0 to 2 give rule 3 and round 3 gives rule 4. `round` is tested with -1 and 0, and `rule` with 5 and with each allowed value. An unknown key goes through a variable typed `type[BaseModel]`, and the frozen test uses `setattr` with the field name in a variable. Both `ValueError` sides are tested (unknown decision, unknown stage). The coder's entry says `make check` was green.
   - Rule order: `decide` in `src/factory/domain/decisions.py` tries the rules as 1, 2, 6, 7, 3/4, not 1, 2, 3, 4, 6, 7. I checked the conditions, including the edge case where `question` is an entry of `next`. They exclude each other, so the result is the same as v1's order.
   - Architecture: everything is pure `factory.domain` code. `post_texts` imports `StallReason` and `FormFinding` only under `TYPE_CHECKING`, with postponed annotations, so the cycle with `decisions` is broken as the Interface says. There is no `Any` and no `dict[str, Any]`.
   - Security: nothing relevant. No suppression markers were added.
   - Quality: names and docstrings are fine. Rules 1 to 3, 6 and 7 build their result in the private helpers `_stay` and `_move`; rule 4 builds its own. The one comment explains why ("forward is next[0] ... wherever it points").
   - Ticket hygiene: the log gives the main decision (forward is `next[0]`) and what was rejected (`PipelineDefinition.position`). `Assignment` matches what was built, and the docs criterion (18) still says what the documenter must write.
   - Out of scope: `git diff main...HEAD` also lists changes under `planning/`, `docs/runs/` and `factory/features/F0007-*`. They come from the human's commit c3044cd, which is on `origin/main` and reached this branch through the merge 76fa9ee; the local `main` is behind `origin/main`. They are not the ticket's work, and I did not review them.
6. documenter: wrote the documentation for criterion 18. `make check` is green.
   - `docs/project-guide.md`: new section "The decision rules", placed before "Kill points". It has the forward/rework rule, the table of rules 1, 2, 3, 4, 6 and 7 (with 5 marked as the checks') and what each does to stage, `blocked`, `round` and `question`. It says that rounds and attempts are counted apart and that `decide` never touches `attempts` or `crashes`. It also names the two question texts and the `TYPE_CHECKING` import in `post_texts`.
   - `docs/operator-guide.md`: new section "The factory's own questions", before the `pipeline_definition_invalid` stop. It gives the exact texts of the form-findings question and the round-cap question, what the stage and round do while blocked, and which answers are accepted: a comment, or closing the pull request to discard the work item. It also says a stage without `round_cap` never asks.
   - Cross-read against the diff: the project guide's pipeline-definition section (`next[0]` forward, `round_cap`), its state table (`blocked` values), its "After the agent run" section and the operator guide's stall section. All are current.
   - Not touched: nothing stale found. I did not run the demo again, but the text I wrote follows the code and the reviewer's trace.
   - Code vs Interface: no findings.

   `make check`: check: green
