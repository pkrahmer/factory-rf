---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 577
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-06T00:01:05.722851Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T23:58:10.182605Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T23:58:10.189111Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T23:58:29.338834Z'
  stage: intake
  run: 70ad4fdba1fa413f9684862e51934748
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T23:58:34.411667Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T00:01:00.110800Z'
  stage: tests
  run: a1bd4c27f6fc4b64a9c3caef54b6ff12
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T00:01:05.722851Z'
  stage: doing
---

# An acceptance merged at its review stage says so on every route

## Description

The human may merge an acceptance's pull request while the acceptance reviewer still works, and the operator guide promises that the `done` entry then says `done (pull request merged before approval); cost: ...` (`docs/operator-guide/work-items.md`, *Merged before its approval*). `AcceptanceMerged` asks `is_before_approval(definition, stage)` (`factory.work.domain.acceptance`) for this. Today that function compares the stage's position with the position of the definition's *first* approval stage. The shipped `factory/pipeline.yml` now lists `docs-approval` before `acceptance`, so `is_before_approval(definition, "acceptance")` is `False`, and an early merge of an acceptance gets the ordinary entry, which breaks the guide's promise. This story makes the function follow the stage's forward moves instead: a stage lies before the approval when its chain of first `next` entries reaches an approval stage. The order of the stages in the file then no longer matters. The booking, the merge handling and the pipeline definition stay as they are.

## Interface

- `factory.work.domain.acceptance` (domain), signature unchanged:

  ```python
  def is_before_approval(definition: PipelineDefinition, stage: str) -> bool:
      """Whether `stage` leads to an approval stage by its forward moves."""
  ```

  - A `stage` that is not in `definition.stages` raises `KeyError` (unchanged).
  - A definition without any stage with `approval: true` raises `ValueError` (unchanged).
  - An approval stage gives `False`. A stage without `next` (`done`) gives `False`.
  - Any other stage: follow `next[0]` from `stage`. The result is `True` when the chain reaches an approval stage. It is `False` when the chain reaches a stage without `next` or a stage it has already visited (a loop), without hanging.
- `tests/work/domain/test_acceptance_before_approval_routes.py` (new): the table on a definition of the shipped order and the loop and dead-end cases.
- `tests/work/application/test_acceptance_merged_on_two_routes.py` (new): the early merge in the fake world on a definition of the shipped order.
- An earlier test this story changes: `tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval`, row `acceptance` from `False` to `True`. Feature decision 7 gives the leave for this row.

## Acceptance criteria

1. On a definition with the stages of the shipped `factory/pipeline.yml`, in its order (`intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, `docs-only`, `docs-review`, `docs-approval`, `acceptance`, `approval`, `done`), `is_before_approval` is `True` for `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, `docs-only`, `docs-review` and `acceptance`, and `False` for `docs-approval`, `approval` and `done`. There is one row per stage.
2. On the single-route definition of `tests/work/domain/test_acceptance_before_approval.py`, the results do not change: `acceptance` is `True`, and `approval` and `done` are `False`.
3. A stage whose forward chain loops (`a` with `next: [b]`, `b` with `next: [a]`, beside an approval stage that neither reaches) gives `False`. A stage whose forward chain ends at `done` without an approval stage gives `False`. A stage whose chain reaches the approval stage after three moves gives `True`. Each case is one row of one parametrized test.
4. An unknown stage raises `KeyError`, and a definition without an approval stage raises `ValueError`. Each is one row.
5. In the fake world, on a definition of the shipped order, an acceptance that the human merges while it is at `acceptance` is booked `accepted` with the entry `done (pull request merged before approval); cost: ...`. One merged at `approval` gets the ordinary `done (pull request merged); cost: ...` entry. Each is one row.
6. `make check` stays green.
7. docs: `docs/project-guide/pipeline.md`, *More than one route, more than one approval stage*: `is_before_approval` follows the first `next` of each stage, so the order of the stages in the file does not matter to it; the sentence that every route's stages must be listed before the first approval stage goes. `docs/operator-guide/work-items.md`: none, because it then holds true again. `docs/decisions.md`: one entry. It says that "before the approval" is read from the forward moves, not from the position. The reason is that the docs route lists `docs-approval` before `acceptance`. Rejected: reordering `factory/pipeline.yml` so that every approval stage comes last. That would put a rule into the file's order that nothing checks.

## Smoke test

```bash
uv run python -c "from pathlib import Path; from factory.pipeline.adapters.pipeline_yaml import RuamelPipelineDefinitionReader; from factory.work.domain.acceptance import is_before_approval; d = RuamelPipelineDefinitionReader().parse(Path('factory/pipeline.yml').read_text()); print(is_before_approval(d, 'acceptance'), is_before_approval(d, 'docs-review'), is_before_approval(d, 'docs-approval'))" 2>&1 | tail -1
```
Expect: `True True False`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: `is_before_approval(definition, stage)` in `factory.work.domain.acceptance` exists with the stated signature (`src/factory/work/domain/acceptance.py:309`). It names the two new test modules and the one earlier test row. That row is `test_docs_route.py` line 297, `("acceptance", False)`, and feature decision 7 gives the leave to change it. Every rule it states is covered: unknown stage, no approval stage, approval and `done` give False, the chain rule, and the loop and dead-end ends.
   - Criteria: each is testable by one parametrized test. Criterion 1 has one row per stage. I walked the shipped `factory/pipeline.yml` by `next[0]`: the chains reach an approval stage or end as the criterion says (`smoke-test`→`approval`, `docs-only`→`docs-review`→`docs-approval`, `acceptance`→`approval`). Criterion 2 pins the old single-route results. Criterion 3 covers the loop, the dead end at `done` and the three-move chain. Criterion 4 covers both failing sides (`KeyError`, `ValueError`). Criterion 5 covers both merge entries, early at `acceptance` and ordinary at `approval`. The two closing criteria are in place.
   - Smoke test: the command is runnable. `RuamelPipelineDefinitionReader().parse(text)` exists (`src/factory/pipeline/adapters/pipeline_yaml.py:25`), the command runs no pytest, and the Expect line `True True False` can be checked against the output.
   - Architecture: the change is a pure rule in the work area's domain layer and adds no import. The booking, the merge handling and the pipeline definition stay as they are.
   - Scope: the story is within F0052. It follows from the docs route that S0001 and S0002 added, and it touches nothing in "Out of scope". The change to the earlier test follows decision 7 and is limited to that one row.
4. factory: started tests as vm.
5. tester: Wrote the tests for criteria 1 to 5 against the Interface. One run of the three test files: the failures are wrong results from today's positional rule, not import or syntax errors. 5 failed, and the remaining rows passed. `make lint` is green.

   - criterion 1: tests/work/domain/test_acceptance_before_approval_routes.py::test_every_stage_of_the_shipped_order_is_before_approval_by_its_forward_moves (one row per stage, 12 rows; the `acceptance` row fails today)
   - criterion 2: tests/work/domain/test_acceptance_before_approval_routes.py::test_the_single_route_keeps_its_results (rows `acceptance`, `approval`, `done`)
   - criterion 3: tests/work/domain/test_acceptance_before_approval_routes.py::test_a_forward_chain_is_before_approval_only_when_it_reaches_one (rows `loop`, `dead-end-at-done`, `three-moves`; the first two fail today)
   - criterion 4: tests/work/domain/test_acceptance_before_approval_routes.py::test_an_unknown_stage_or_a_definition_without_approval_is_refused (rows `unknown-stage` → KeyError, `no-approval-stage` → ValueError)
   - criterion 5: tests/work/application/test_acceptance_merged_on_two_routes.py::test_an_acceptance_merged_on_the_shipped_order_says_whether_it_came_before_approval (rows `at-acceptance`, which fails today with the ordinary entry, and `at-approval`). It runs through the shared `AcceptanceWalk` (`walk` fixture) with the two-route definition pushed to main and set as the walk's definition. I did not copy the per-module `opened`/`publish`/`merge` fixtures.
   - Earlier row changed, with the leave from feature decision 7 that the Interface names: tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval, row `("acceptance", False)` → `("acceptance", True)`. It fails today, as intended.

   Files created:
   - tests/work/domain/test_acceptance_before_approval_routes.py
   - tests/work/application/test_acceptance_merged_on_two_routes.py
   - tests/support/two_routes_support.py, which holds `TWO_ROUTES`, the shipped-order definition.

   Earlier test file changed under the standing leave to move a shared test helper:
   - tests/pipeline/application/test_docs_route.py. Its `TWO_ROUTES` constant moved to `support.two_routes_support`, and the module now imports it from there. Every test keeps its name and checks the same thing.

   Modules the runner could not import: none, because `is_before_approval` exists already.

   Rejected: copying the `opened`/`publish`/`merge` fixtures of test_acceptance_merged_before_approval.py into the new application test. The reviewer counts a copy as a finding.

   Open for the docs stage: `tests/support/two_routes_support.py` is a new support module, and the project guide's *Shared test helpers* list names such modules. Criterion 7 does not mention it.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
