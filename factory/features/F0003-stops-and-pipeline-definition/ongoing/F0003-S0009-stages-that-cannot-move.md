---
stage: docs
pr: 50
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Stages that cannot move are refused at load

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

S0007 refuses at load "a definition that is well formed but cannot work", so that the fault is not found when a stage first reaches it. Two shapes of stage still pass, and a work item that enters either would sit there with no stop to say why:

- A stage other than `done` with an empty `next`. Its agent's forward outcome has nowhere to go, and neither has the human's approval.
- A stage other than `done` with neither a role nor `approval: true`. No agent runs there and the human does not decide there.

This story adds two rules to the validator of `PipelineDefinition`, after S0007's nine. Each refusal is then the existing `PipelineDefinitionInvalid` and, at load, the existing `pipeline_definition_invalid` stop. Covers R30 and keeps kept things 7 and 12. The acceptance of F0003 found the gap (section 2 probes).

Decided by the human on 2026-10-14, as the pre-check recommended: neither shape is meant. No kind of stage in the schema lets the factory work without an agent (the name `factory` is reserved, not a stage kind), and a later story that needs one adds it and relaxes rule 11 deliberately. The two rules run only when the definition has a stage named `done`: without one, the end of the pipeline is unknown and S0007's fault `stages must hold a stage named done` is the one that matters. This also keeps S0007's test `test_a_definition_without_a_done_stage_is_refused` as it stands, so no test of another story changes. Rejected: applying the rules always, which would add two faults for `finished: {}` to that test and change it.

## Interface

`src/factory/domain/pipeline_definition.py` (adds to S0007's validator; the rule numbers continue S0007's)

Rules and their faults (`<s>` is a stage):

10. When `stages` holds a stage named `DONE_STAGE`, every other stage has at least one name in `next`. Otherwise the fault is `stage <s>: next is empty`, in the order of the stages.
11. When `stages` holds a stage named `DONE_STAGE`, every other stage has a role or `approval: true`. Otherwise the fault is `stage <s>: has neither a role nor approval`, in the order of the stages.

Rule 10's faults come before rule 11's, and both come after the faults of rules 1 to 9, joined by `; ` as S0007 joins them.

Tests: a new file `tests/adapters/test_pipeline_stage_moves.py`, through `RuamelPipelineDefinitionReader`, every case built on `PIPELINE_YAML` by text replacement. One case in a new file `tests/application/test_pipeline_loading_stage_moves.py` uses S0006's fixtures. No existing test changes.

## Acceptance criteria

1. `PIPELINE_YAML` still parses. Its stage `acceptance`, which no `next` names, is accepted: this story adds no rule on reachability.
2. A stage `limbo: {next: [done]}` added before `done` is refused with the fault `stage limbo: has neither a role nor approval`. `limbo: {role: coder, next: [done]}` is accepted, and so is `limbo: {approval: true, next: [done]}`. A stage `limbo: {}` added before `done` breaks both rules and is refused with the fault `stage limbo: next is empty; stage limbo: has neither a role nor approval`.
3. The stage `doing` with `next: []` is refused with the fault `stage doing: next is empty`. With `next: [review]` it is accepted.
4. The stage `approval` with `next: []` is refused with the fault `stage approval: next is empty`.
5. With two faults of each rule (`doing` and `review` with `next: []`, and stages `a: {next: [done]}` and `b: {next: [done]}` added before `done`), the fault is `stage doing: next is empty; stage review: next is empty; stage a: has neither a role nor approval; stage b: has neither a role nor approval`.
6. A fault of S0007's rules comes first: `next: [review, ship]` in `doing` together with `limbo: {next: [done]}` gives `stage doing: next names unknown stage ship; stage limbo: has neither a role nor approval`.
7. Without a stage named `done` (every `done` renamed `finished`), the fault is exactly `stages must hold a stage named done`. Neither new rule adds a fault for `finished`.
8. Loaded through `PipelineLoader.load` at `origin/main`, a stage `limbo: {next: [done]}` is a reported stop. `load` raises `PipelineDefinitionInvalid`, and the health status holds one stop `pipeline_definition_invalid` with the `detail` `stage limbo: has neither a role nor approval`.
9. `make check` stays green.
10. docs: `docs/project-guide.md`, "The rules of the definition", says the validator applies eleven rules, lists rules 10 and 11 with their faults, and says they apply only when the stage `done` exists. `docs/decisions.md` records that a stage other than `done` must be able to move (a `next`, and a role or approval) and why the two rules wait for `done`. The operator guide's row for faults of the rules still points to the project guide's list.

## Demo

```bash
uv run python -c "
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
TEXT = '''contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
stages:
  doing: {role: coder, next: [gate]}
  gate: {approval: true, next: [done, doing]}
  done: {}
'''
reader = RuamelPipelineDefinitionReader()
print(reader.parse(TEXT).first_stage())
for old, new in [('next: [gate]', 'next: []'), ('gate: {approval: true,', 'gate: {')]:
    try:
        reader.parse(TEXT.replace(old, new))
        print('accepted')
    except PipelineDefinitionInvalid as error:
        print(error.fault)
"
```
Expect: three lines: `doing`, then `stage doing: next is empty`, then `stage gate: has neither a role nor approval`.

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: rules 10 and 11 are in `src/factory/domain/pipeline_definition.py`, continuing S0007's numbering. Each fault text, the order of the stages, and the order of rules (10 before 11, both after 1 to 9) are exact. The condition for applying them (a stage named `DONE_STAGE` exists) is stated.
   - Criteria: each criterion is testable by one function with no further decisions. Each rule has its refused side (criteria 2 to 5) and its accepted side (criteria 1 to 3). Criterion 6 covers the ordering after S0007's faults. Criterion 7 covers the no-`done` case, and criterion 8 covers the load stop.
   - Demo: the script is runnable. Its `Expect:` line gives three exact lines. I checked that `PIPELINE_YAML` in `tests/git_support.py` has `doing`, `review`, `acceptance`, `approval` and `done` as the criteria assume.
   - Architecture: the change is in the domain validator only. The existing error and stop carry the faults, so no layer rule is touched.
   - Scope: the story stays within F0003's load-time validation and is not in "Out of scope".
3. tester: wrote red tests for rules 10 and 11. The cases change `PIPELINE_YAML` by text replacement and parse it through `RuamelPipelineDefinitionReader`.
   - criterion 1: tests/adapters/test_pipeline_stage_moves.py::test_a_stage_no_next_names_is_accepted (it also asserts that no `next` names `acceptance`)
   - criterion 2: tests/adapters/test_pipeline_stage_moves.py::test_a_stage_needs_a_role_or_approval_and_a_next (parametrized: `limbo: {next: [done]}` refused, the role and approval variants accepted, `limbo: {}` refused by both rules)
   - criterion 3: tests/adapters/test_pipeline_stage_moves.py::test_a_stage_with_a_role_and_an_empty_next_is_refused (`[]` refused, `[review]` accepted)
   - criterion 4: tests/adapters/test_pipeline_stage_moves.py::test_an_approval_stage_with_an_empty_next_is_refused
   - criterion 5: tests/adapters/test_pipeline_stage_moves.py::test_empty_nexts_come_before_stages_without_role_or_approval_in_stage_order
   - criterion 6: tests/adapters/test_pipeline_stage_moves.py::test_a_fault_of_the_earlier_rules_comes_before_a_stage_that_cannot_move
   - criterion 7: tests/adapters/test_pipeline_stage_moves.py::test_without_a_done_stage_no_stage_is_refused_for_not_moving
   - criterion 8: tests/application/test_pipeline_loading_stage_moves.py::test_a_stage_without_role_or_approval_is_one_reported_stop (uses S0006's fixtures `boundaries`, `agent_home`, `human` and `checkout`)

   Files created: tests/adapters/test_pipeline_stage_moves.py, tests/application/test_pipeline_loading_stage_moves.py. No existing test was changed.

   `make test`: every module imports, since the modules under test already exist. The 7 failing tests fail on a wrong result: each case that should be refused is still accepted. The cases that should be accepted already pass, and so does criterion 7. `make lint` is green. The type check was not run in this stage.

   `make lint`: lint: green
   `make test`: FAILED tests/application/test_pipeline_loading_stage_moves.py::test_a_stage_without_role_or_approval_is_one_reported_stop
4. coder: rules 10 and 11 are in `src/factory/domain/pipeline_definition.py` (commit 46fd728). `make check` is green and every test from the tester passes.
   - `_empty_next_faults` (rule 10) and `_unworked_stage_faults` (rule 11) come at the end of `_RULES`, after S0007's rules. That ordering puts rule 10's faults before rule 11's, and both after rules 1 to 9, each in the order of the stages.
   - Both rules go through one helper, `_moving_stages`. It returns every stage except `done`, and returns nothing when there is no `done`. That way the "rules wait for done" condition is written in one place.
   - Rejected: checking for `done` inside each rule. It would repeat the same condition twice.
   - Refactor: I read the diff and found nothing to change. No separate refactor commit.
   - Not touched: the docs criterion, which belongs to the documenter.

   `make check`: check: green
5. reviewer: no findings.
   - Acceptance criteria: criteria 1 to 8 each have a test that checks what the criterion says. Both rules are tested on their refused side and their accepted side: `limbo` with a role or with approval is accepted, `doing` with `[review]` is accepted, and an empty `next` is refused for both a role stage and an approval stage. The `done`-exists condition is tested on its other side by `test_without_a_done_stage_no_stage_is_refused_for_not_moving`. In `tests/git_support.py`, `done` appears only in the `approval` stage's `next` and in the `done` stage itself, so the global rename in that test does what criterion 7 describes. The tests also check the order of the faults: within a rule they follow the order of the stages (criterion 5), and an earlier rule's fault comes first (criterion 6). Criterion 8 checks both the raised `PipelineDefinitionInvalid` and the single health stop with its `detail`. The coder's entry records `make check` green.
   - Architecture: the change is only in `factory.domain` (`src/factory/domain/pipeline_definition.py`). It adds no I/O and no new imports, and it reuses the existing error and stop.
   - Security: no subprocess, strings or suppression markers were added.
   - Quality: `_moving_stages` holds the "only when `done` exists" condition once. Its comment says why, not what. The rule functions are private, so no docstrings are needed. Rule 11's check `role is None and not approval` matches `StageDefinition` (`role: Name | None`, `approval: bool`).
   - Ticket hygiene: the coder's log names the main decision (one helper for the `done` condition) and what was rejected (checking for `done` inside each rule). Assignment and Interface match the code. The docs criterion still describes what the documenter must write.
