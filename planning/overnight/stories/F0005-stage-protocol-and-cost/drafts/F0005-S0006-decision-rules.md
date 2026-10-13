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

Types: `Blocked` and `WorkItemState` from `factory.domain.work_item`, `FormFinding` from `factory.domain.story_form`, `PipelineDefinition` from `factory.domain.pipeline_definition`. `StageMove` is frozen and forbids unknown keys. A decision is "forward" when it equals `next[0]` of the state's stage, and a "rework" when it is another entry of `next`; this is the one rule for counting rounds (FEATURE decision 26), whatever the position of the stage the rework names in the pipeline definition. The interface sheet's `PipelineDefinition.position` is not used to count rounds.

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
16. `StageMove` refuses what its types refuse, on both sides: `rule` 1, 2, 3, 4, 6 and 7 and `round` 0 are accepted, `rule` 5 and `round` -1 raise `ValidationError`, and an unknown key raises `ValidationError` (built through a variable typed `type[BaseModel]`).
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
