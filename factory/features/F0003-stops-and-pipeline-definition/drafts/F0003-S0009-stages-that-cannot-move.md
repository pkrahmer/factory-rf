# Stages that cannot move are refused at load

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

S0007 refuses at load "a definition that is well formed but cannot work", so that the fault is not found when a stage first reaches it. Two shapes of stage still pass, and a work item that enters either would sit there with no stop to say why:

- A stage other than `done` with an empty `next`. Its agent's forward outcome has nowhere to go, and neither has the human's approval.
- A stage other than `done` with neither a role nor `approval: true`. No agent runs there and the human does not decide there.

This story adds two rules to the validator of `PipelineDefinition`, after S0007's nine. Each refusal is then the existing `PipelineDefinitionInvalid` and, at load, the existing `pipeline_definition_invalid` stop. Covers R30 and keeps kept things 7 and 12. The acceptance of F0003 found the gap (section 2 probes).

Decisions for the human while refining:

- Is either shape ever meant? For example, a stage the factory itself works in with no agent: the name `factory` is reserved, but no such stage kind exists in the schema. This draft assumes neither is meant.
- The two rules run only when the definition has a stage named `done`. Without one, it is unclear which stage was meant as the end, so its faults would be noise. This also keeps S0007's test `test_a_definition_without_a_done_stage_is_refused` valid as it stands: its text renames `done` to `finished`, and `finished: {}` would otherwise add two faults to the one it expects. The alternative is to apply the rules always and change that test, which needs your approval (R9).

## Interface

`src/factory/domain/pipeline_definition.py` (adds to S0007's validator; the rule numbers continue S0007's)

Rules and their faults (`<s>` is a stage):

10. When `stages` holds a stage named `DONE_STAGE`, every other stage has at least one name in `next`. Otherwise the fault is `stage <s>: next is empty`, in the order of the stages.
11. When `stages` holds a stage named `DONE_STAGE`, every other stage has a role or `approval: true`. Otherwise the fault is `stage <s>: has neither a role nor approval`, in the order of the stages.

Rule 10's faults come before rule 11's, and both come after the faults of rules 1 to 9, joined by `; ` as S0007 joins them.

Tests: a new file `tests/adapters/test_pipeline_stage_moves.py`, through `RuamelPipelineDefinitionReader`, every case built on `PIPELINE_YAML` by text replacement. One case in a new file `tests/application/test_pipeline_loading_stage_moves.py` uses S0006's fixtures. No existing test changes.

## Acceptance criteria

1. `PIPELINE_YAML` still parses. Its stage `acceptance`, which no `next` names, is accepted: this story adds no rule on reachability.
2. A stage `limbo: {next: [done]}` added before `done` is refused with the fault `stage limbo: has neither a role nor approval`. `limbo: {role: coder, next: [done]}` is accepted, and so is `limbo: {approval: true, next: [done]}`.
3. The stage `doing` with `next: []` is refused with the fault `stage doing: next is empty`. With `next: [review]` it is accepted.
4. The stage `approval` with `next: []` is refused with the fault `stage approval: next is empty`.
5. With two faults of each rule (`doing` and `review` with `next: []`, and stages `a: {next: [done]}` and `b: {next: [done]}` added before `done`), the fault is `stage doing: next is empty; stage review: next is empty; stage a: has neither a role nor approval; stage b: has neither a role nor approval`.
6. A fault of S0007's rules comes first: `next: [review, ship]` in `doing` together with `limbo: {next: [done]}` gives `stage doing: next names unknown stage ship; stage limbo: has neither a role nor approval`.
7. Without a stage named `done` (every `done` renamed `finished`), the fault is exactly `stages must hold a stage named done`. Neither new rule adds a fault for `finished`.
8. Loaded through `PipelineLoader.load` at `origin/main`, a stage `limbo: {next: [done]}` is a reported stop. `load` raises `PipelineDefinitionInvalid`, and the health status holds one stop `pipeline_definition_invalid` with the `detail` `stage limbo: has neither a role nor approval`.
9. `make check` stays green.
10. docs: `docs/project-guide.md`, "The rules of the definition", lists rules 10 and 11 with their faults and says they apply only when the stage `done` exists. The operator guide's row for faults of the rules still points there.

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
