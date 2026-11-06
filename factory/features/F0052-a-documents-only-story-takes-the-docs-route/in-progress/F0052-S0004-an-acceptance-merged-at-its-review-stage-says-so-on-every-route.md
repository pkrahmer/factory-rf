---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 577
comments_read: [6672901695, 6673109567]
handed_over: null
claim: null
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
- number: 7
  speaker: coder
  kind: question
  at: '2026-11-06T00:07:24.358110Z'
  stage: doing
  run: 60d6aa07b9b14080ba22e925fc12cef8
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-11-06T00:09:15.238323Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T00:09:17.826570Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-06T00:09:40.383940Z'
  stage: doing
  run: 5ddac77f124f4b06b2163e39d3725612
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-06T00:09:45.879944Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-11-06T00:11:04.955262Z'
  stage: tests
  run: 7501e2c7c84d4537a451e1b8638ee4d0
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T00:11:11.263354Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-06T00:16:35.895383Z'
  stage: doing
  run: b51faaff782c49bdba407c28107b5a0c
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-06T00:16:41.052718Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-11-06T00:17:47.372125Z'
  stage: review
  run: a45988830328409587a7023e4ea698f8
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-06T00:17:52.792155Z'
  stage: doing
- number: 18
  speaker: coder
  kind: question
  at: '2026-11-06T00:18:30.525959Z'
  stage: doing
  run: 9f79958530f6463486e7e719a4aa32eb
  blocked: question
- number: 19
  speaker: human
  kind: comment
  at: '2026-11-06T00:22:22.065991Z'
  stage: doing
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T00:22:24.533219Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T00:22:47.566727Z'
  stage: doing
  run: 883f734711a748748b1f1603e1a4aedf
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T00:22:52.529261Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-06T00:25:02.378701Z'
  stage: tests
  run: b0bf8f8aaad043e19a1c60514975b865
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T00:25:07.662549Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-06T00:30:39.027435Z'
  stage: doing
  run: 5559b36316574009a7625a097046d30f
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-06T00:30:44.365853Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-06T00:32:40.844940Z'
  stage: review
  run: c25c15043324428d9c6a81a0bf1c52f6
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-06T00:32:45.926917Z'
  stage: docs
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-06T00:33:24.429883Z'
  stage: docs
  run: 4a5c9298ab5446d6b3bb0f5c7e0fb6af
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-06T00:33:29.815005Z'
  stage: smoke-test
- number: 31
  speaker: smoke-tester
  kind: result
  at: '2026-11-06T00:33:54.259423Z'
  stage: smoke-test
  run: 951f9792ada04abd87bc9c2f289a1176
---

# An acceptance merged at its review stage says so on every route

## Description

The human may merge an acceptance's pull request while the acceptance reviewer still works, and the operator guide promises that the `done` entry then says `done (pull request merged before approval); cost: ...` (`docs/operator-guide/work-items.md`, *Merged before its approval*). `AcceptanceMerged` asks `is_before_approval(definition, stage)` (`factory.work.domain.acceptance`) for this. Today that function compares the stage's position with the position of the definition's *first* approval stage. The shipped `factory/pipeline.yml` now lists `docs-approval` before `acceptance`, so `is_before_approval(definition, "acceptance")` is `False`, and an early merge of an acceptance gets the ordinary entry, which breaks the guide's promise. This story makes the function follow the stage's forward moves instead: a stage lies before the approval when its chain of first `next` entries reaches an approval stage. The order of the stages in the file then no longer matters. The booking, the merge handling and `factory/pipeline.yml` stay as they are. `PipelineDefinition.position` goes, because no code calls it once this rule follows the forward moves (the human's answer in the journal).

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
7. docs: `docs/project-guide/pipeline.md`, *More than one route, more than one approval stage*: `is_before_approval` follows the first `next` of each stage, so the order of the stages in the file does not matter to it; the sentence that every route's stages must be listed before the first approval stage goes. `docs/project-guide/pipeline.md`, *The pipeline definition*: the list of methods no longer names `position(stage)`, which this story removes. `docs/project-guide/README.md`, *Shared test helpers*: the list names `support/two_routes_support.py` (`TWO_ROUTES`, a definition of two routes to two approval stages in the shipped order) and `support/before_approval_support.py` (`ROLES`, `FIXTURE` and `without_approval`, the definitions of the tests of `is_before_approval`). `docs/operator-guide/work-items.md`: none, because it then holds true again. `docs/decisions.md`: one entry. It says that "before the approval" is read from the forward moves, not from the position. The reason is that the docs route lists `docs-approval` before `acceptance`. Rejected: reordering `factory/pipeline.yml` so that every approval stage comes last. That would put a rule into the file's order that nothing checks.

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
7. coder: The code change is done, but `make check` is red because one of this story's new test modules trips a structural guard. I may not edit tests, so I need the human's word on how the tester should fix it.

   Built: `src/factory/work/domain/acceptance.py`, `is_before_approval`. The signature is unchanged. It still raises `KeyError` for an unknown stage and `ValueError` when no stage has `approval: true`. An approval stage gives `False`. Any other stage follows `next[0]`, keeping a set of visited stages. It returns `True` when the chain reaches an approval stage, and `False` at a stage without `next` or at a stage it has already visited. The smoke test prints `True True False`, as expected.

   Main choice: an iterative walk with a visited set. Rejected: a recursive walk, which would need the set passed down anyway. Also rejected: reusing `definition.position`, the positional rule this story removes. `PipelineDefinition.position` stays, because other code may still call it. I did not search for callers, since the story does not touch it.

   Refactor: nothing to change. The diff is one function.

   State of `make check`: lint, types, layers, sast, secrets and licenses are green. In `make test`, every test of this story passes. Exactly one test fails:

   `tests/guards/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own[work/application/test_acceptance_merged_on_two_routes.py]`
   ```
   E       AssertionError: test_acceptance_merged_on_two_routes.py imports nothing of work
   E       assert [] != []
   tests/guards/test_areas.py:264: AssertionError
   ```
   The new module sits in `tests/work/application/`, but it imports only `factory.pipeline.application.boundaries` and `factory.watching.domain.bills`. Its other helpers come from `support.acceptance_walk`. No code change can make this guard pass; it is a test fault (R9).

   Options for the tester:
   - (a) Import a name from `factory.work` that the test actually uses. For example, check the `accepted` outcome against `AcceptanceState`, or build the expected entry from a work-area constant. The module then stays beside its sibling `tests/work/application/test_acceptance_merged_before_approval.py`, which imports `factory.work.application.acceptance`.
   - (b) Move the module to `tests/pipeline/application/`, where its imports already satisfy the guard.

   I would choose (a): the test is about `AcceptanceMerged` in the work area, so it belongs in the work area's test folder. If you agree, I will end the next round with `tests` and name that change.

   Not touched: `tests/support/two_routes_support.py` is a new support module that the project guide's shared-helper list does not name yet. The tester left that open for the docs stage.
8. 2026-11-06 human: (a): end with `tests`. The tester makes `tests/work/application/test_acceptance_merged_on_two_routes.py` import a name from `factory.work` that the test really uses, for example the accepted outcome or the entry text checked against the work area's own names. No import that only satisfies the guard. The module stays beside `test_acceptance_merged_before_approval.py`. The docs stage names `tests/support/two_routes_support.py` in the shared-helper list.
9. factory: started doing as vm.
10. coder: The human chose (a), so this goes to the tester. The test to change is `tests/work/application/test_acceptance_merged_on_two_routes.py`. It must import from `factory.work` a name it really uses: for example, check the `accepted` outcome or the done entry's text against the work area's own names. An import that only satisfies the guard is not enough. The module stays in `tests/work/application/`. The guard `tests/guards/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own` should then pass for this module.

    I changed no code in this run. The new `is_before_approval` in `src/factory/work/domain/acceptance.py` is already committed on the branch from the previous run. It follows `next[0]` and keeps a set of visited stages.

    `make check` was not run in this run. In the previous run it was red only on that guard row, and the code has not changed since. The coder's next round needs `make check` green, then hands forward to `review`.

    Description: unchanged. The human's answer does not change what the task means. It adds one thing for the docs stage: name `tests/support/two_routes_support.py` in the project guide's shared-helper list.
11. factory: started tests as vm.
12. tester: I made the test change the human approved under (a) in entry 8, as the coder named it in entry 10. The changed test is `tests/work/application/test_acceptance_merged_on_two_routes.py::test_an_acceptance_merged_on_the_shipped_order_says_whether_it_came_before_approval`.

    - Change: the test now checks the booked report's state against the work area's own `AcceptanceState` from `factory.work.domain.acceptance`. It does this with `assert isinstance(state, AcceptanceState)` before it checks `(stage, outcome) == ("done", "accepted")`. Before, it called `booked_state` from `support.acceptance_walk`, which made the same assertion out of sight. The import is used by a real check, not added only to satisfy the guard. The test still checks the same thing, and the module stays in `tests/work/application/` beside `test_acceptance_merged_before_approval.py`.
    - Rejected: importing `book_merge` to build the expected entry, because that would test against the implementation. Also rejected: the `AcceptanceOutcome` Literal, which nothing could check at runtime.
    - Run: `uv run pytest -q` on the changed file plus `tests/guards/test_areas.py` passed, including the guard row `test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own[work/application/test_acceptance_merged_on_two_routes.py]`. `make lint` is green (`lint: green (0.1 s)`).
    - Criterion mapping (unchanged): criterion 5 is tested by `tests/work/application/test_acceptance_merged_on_two_routes.py::test_an_acceptance_merged_on_the_shipped_order_says_whether_it_came_before_approval`. Criteria 1 to 4 stay as entry 5 maps them.
    - Files: I created no new file in this run. I changed only `tests/work/application/test_acceptance_merged_on_two_routes.py`, which this story's tests stage wrote. The test run could import every module.
    - Still open for the docs stage, per entry 8: name `tests/support/two_routes_support.py` in the project guide's shared-helper list.

    `lint`: lint: green (0.2 s)
13. factory: started doing as vm.
14. coder: The tester changed the test in entry 12, and `make check` is now green (`test: green (140.9 s)`, `check: green`). I changed no code in this run. The only code change on the branch is from the first doing run.

    Built: in `src/factory/work/domain/acceptance.py`, `is_before_approval` keeps its signature and its `KeyError` and `ValueError`. An approval stage gives `False`. Every other stage follows `next[0]` and keeps a set of visited stages. It returns `True` when it reaches an approval stage, and `False` when it reaches a stage without `next` or one it has already visited. The smoke test prints `True True False`.

    Main choice: an iterative walk with a visited set. Rejected:
    - a recursive walk, which would need the set passed down anyway;
    - keeping `definition.position`, the positional rule this story removes.

    Refactor: I read the diff again, which is one function of 19 lines. Nothing needs changing.

    Description: unchanged. The human's answer in entry 8 changes how the test is written, not what the task means. It also adds a task for the docs stage: name `tests/support/two_routes_support.py` in the project guide's shared-helper list.

    Noticed, not touched: `PipelineDefinition.position` stays in place. This function no longer uses it, and I did not check whether anything else still does. The reviewer may want to look for dead code with `make duplicates`.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 40 known, 3 gone
15. factory: started review as vm.
16. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'`, which covers five files. The code change is `is_before_approval` in `src/factory/work/domain/acceptance.py:309-327`. It keeps the `KeyError` and `ValueError` paths. It gives `False` for an approval stage, follows `next[0]` with a visited set, and returns `True` when it reaches an approval stage. It returns `False` at a stage without `next` or on a loop. That matches every rule of the Interface. The rows of criteria 1, 3 and 5 test what they are named after. The factory's `make check` after the coder was green (entry 14). Architecture holds: a pure domain rule, no new import. Security: nothing to report, no silencing marker.

    Findings:
    1. `tests/work/domain/test_acceptance_before_approval_routes.py:43-55` (`SINGLE_ROUTE`), `:73-83` (`WITHOUT_APPROVAL`) and `:8-16` (`ROLES`): these copy `FIXTURE` and `_without_approval` of `tests/work/domain/test_acceptance_before_approval.py:17-57`. Criterion 2 itself says to use the single-route definition of that file. Fix: the tester moves `FIXTURE` and the definition without an approval stage to a module in `tests/support/`, under the standing leave to move a shared test helper. Both modules then import them from there, and every earlier test keeps its name and what it checks.
    2. `tests/work/domain/test_acceptance_before_approval_routes.py:26-41` (`SHIPPED`): this is a second copy, as a dict, of the stages of `TWO_ROUTES` in `tests/support/two_routes_support.py`. The two can drift apart without any test noticing. Fix: build `SHIPPED` from `TWO_ROUTES` through the pipeline reader, as `test_docs_route.py:263` does, or keep one shared source for both.
    3. `tests/work/domain/test_acceptance_before_approval_routes.py:107-112` and `:126-137`: `test_the_single_route_keeps_its_results` and `test_an_unknown_stage_or_a_definition_without_approval_is_refused` repeat the same rows as the earlier tests at `tests/work/domain/test_acceptance_before_approval.py:60-79`. Those earlier tests already pin criteria 2 and 4 on the same definitions. Fix: drop the two duplicates and map criteria 2 and 4 to the earlier tests. Or, if the tester keeps them here, they must at least share the definitions as finding 1 says.
    4. `src/factory/pipeline/domain/pipeline_definition.py:109-111` (`PipelineDefinition.position`): this diff removed the method's only caller under `src/`, so it is now dead code. Only the earlier test `tests/pipeline/adapters/test_pipeline_yaml.py:78-80` still calls it. Fix: remove the method. Removing the earlier test `test_position_is_the_index_in_the_stages` with it needs the human's leave, so the coder asks first (R8). The other option is to keep the method with a recorded reason and an accepted entry in `security/duplicates-baseline.txt`.
    5. The work item's acceptance criterion 7: it does not name `tests/support/two_routes_support.py`. `docs/project-guide/README.md` (*Shared test helpers*) says that a story adding a support module names it in that list through its docs criterion, and the human asked for it in entry 8. The documenter writes from the criterion, so the module would be left out. Fix: add to criterion 7 that `docs/project-guide/README.md`'s shared-helper list names `tests/support/two_routes_support.py` and `TWO_ROUTES`, the two-route definition in the shipped order.

    Earlier tests:
    - `tests/pipeline/application/test_docs_route.py`: changed under two leaves. Its `TWO_ROUTES` moved to `tests/support/two_routes_support.py` under the standing leave to move a shared test helper. The row `("acceptance", False)` became `("acceptance", True)` in `test_only_the_docs_routes_working_stages_lie_before_the_approval`, under the human's leave: feature decision 7, named in the story's Interface. No other change.
17. factory: started doing as vm.
18. coder: Rework round 1. I stopped before any code change because finding 4 of the review (entry 16) needs your word. Findings 1 to 3 are test changes, which I will pass to the tester with `tests` once you have answered. Finding 5 is done.

    Question: what should happen to `PipelineDefinition.position` (`src/factory/pipeline/domain/pipeline_definition.py:109-111`)? I checked with grep: no code under `src/` calls it any more. Its only caller is the earlier test `tests/pipeline/adapters/test_pipeline_yaml.py::test_position_is_the_index_in_the_stages`, at line 80, which another story wrote. The options I see:
    - (a) Remove both. You give leave to delete that earlier test. In the next round I end with `tests` and name the deletion together with findings 1 to 3. Once the tester has made those changes, I remove the method. The test has to go first, or `make check` turns red.
    - (b) Keep the method. I add an accepted entry for it in `security/duplicates-baseline.txt` and give a reason. The only reason I can see is that the method is public on the pipeline definition, and that is weak.
    - (c) Leave it out of this story and open a separate story for it later.

    I would choose (a): the method is dead code because of this story, and its test pins nothing the factory uses.

    Findings 1 to 3, all for the tester in the next round under the standing leave to move a shared test helper:
    - (1) Move `FIXTURE`, the definition without an approval stage, and `ROLES` from `tests/work/domain/test_acceptance_before_approval.py` to a module in `tests/support/`. Both domain test modules then import them from there.
    - (2) Build `SHIPPED` in `test_acceptance_before_approval_routes.py` from `TWO_ROUTES` through the pipeline reader.
    - (3) Remove the two tests in `test_acceptance_before_approval_routes.py` that repeat the earlier tests of criteria 2 and 4. Those criteria then map to the earlier tests.

    Finding 5, done: your answer in entry 8 changed the docs criterion. I rewrote criterion 7 in `## Description`, whose heading now says "as of the human's answer in entry 8". The criterion now names `tests/support/two_routes_support.py` and `TWO_ROUTES` for the *Shared test helpers* list in `docs/project-guide/README.md`.

    Code: unchanged since entry 14. I did not run `make check` in this round, because no code changed.

    The factory left out changes outside the write paths: factory/features/F0052-a-documents-only-story-takes-the-docs-route/in-progress/F0052-S0004-an-acceptance-merged-at-its-review-stage-says-so-on-every-route.md.
19. 2026-11-06 human: (a), with the human's leave: the tester deletes `tests/pipeline/adapters/test_pipeline_yaml.py::test_position_is_the_index_in_the_stages` and nothing else in that module, together with findings 1 to 3, and names the deletion in its entry. Then the coder removes `PipelineDefinition.position`. Reason: no code calls it any more, since this story reads "before the approval" from the forward moves. Note: your change to criterion 7 in the work item was dropped by the take, because the work item is outside your write paths; the answer in entry 8 stands as the docs criterion all the same.
20. factory: started doing as vm.
21. coder: Rework round 1, after the human's answer (a) in entry 19. I changed no code in this run. The test changes have to come first: if I removed `PipelineDefinition.position` (`src/factory/pipeline/domain/pipeline_definition.py:109-111`) now, the earlier test that still calls it would turn `make check` red. So this goes to the tester. Once the tester has made the changes below, I remove the method in the next doing run.

    Test changes for the tester:
    - Deletion, with the human's leave in entry 19: delete `tests/pipeline/adapters/test_pipeline_yaml.py::test_position_is_the_index_in_the_stages` and nothing else in that module. Name the deletion in the entry.
    - Finding 1 of entry 16, under the standing leave to move a shared test helper: move `FIXTURE`, the definition without an approval stage (`_without_approval`) and `ROLES` from `tests/work/domain/test_acceptance_before_approval.py` to one module in `tests/support/` (named `*_support.py`). Both `test_acceptance_before_approval.py` and `test_acceptance_before_approval_routes.py` then import them from there. Every earlier test keeps its name and checks the same thing.
    - Finding 2 of entry 16: build `SHIPPED` in `tests/work/domain/test_acceptance_before_approval_routes.py` from `TWO_ROUTES` (`tests/support/two_routes_support.py`) through the pipeline reader, as `tests/pipeline/application/test_docs_route.py` does. The stage list then has a single source.
    - Finding 3 of entry 16: remove `test_the_single_route_keeps_its_results` and `test_an_unknown_stage_or_a_definition_without_approval_is_refused` from `test_acceptance_before_approval_routes.py`. Map criteria 2 and 4 to the earlier tests in `tests/work/domain/test_acceptance_before_approval.py`, which already pin the same rows on the same definitions.

    Description: unchanged. The work item is outside my write paths, so the take dropped my earlier rewrite of criterion 7, as entry 19 notes. Entry 8 still stands as the docs criterion: the docs stage names `tests/support/two_routes_support.py` and `TWO_ROUTES` in the *Shared test helpers* list of `docs/project-guide/README.md`. If finding 1 creates a second support module, the docs stage should name that one in the list as well.

    I did not run `make check` in this run, because no code changed. It was green after entry 14.
22. factory: started tests as vm.
23. tester: I made the test changes the coder listed in entry 21. They cover the human's answer (a) in entry 19 and findings 1 to 3 of entry 16.

    - **Deletion (human's leave, entry 19):** I deleted `tests/pipeline/adapters/test_pipeline_yaml.py::test_position_is_the_index_in_the_stages` and changed nothing else in that module. No test or code under `tests/` or `src/` calls `.position(` any more, so the coder can now remove `PipelineDefinition.position`.
    - **Finding 1 (standing leave to move a shared test helper):** I created `tests/support/before_approval_support.py` with `ROLES`, `FIXTURE` and `without_approval()`. I moved them out of `tests/work/domain/test_acceptance_before_approval.py`, which now imports `FIXTURE` and `without_approval` from there. The import is aliased `definition_without_approval` because the test's parameter `without_approval` would shadow it. Every earlier test keeps its name and checks the same thing. `FIXTURE`'s roles are the same `ROLES` dict as before.
    - **Finding 1, second module:** `tests/work/domain/test_acceptance_before_approval_routes.py` now takes `ROLES` from the new support module. I dropped its copies of `ROLES`, `SINGLE_ROUTE` and `WITHOUT_APPROVAL`.
    - **Finding 2:** `SHIPPED` is now `RuamelPipelineDefinitionReader().parse(TWO_ROUTES)`, from `tests/support/two_routes_support.py`, so the stage list has one source. The guard of area imports passes with the pipeline adapter import.
    - **Finding 3:** I removed `test_the_single_route_keeps_its_results` and the duplicate `test_an_unknown_stage_or_a_definition_without_approval_is_refused` from the routes module.

    Criterion mapping after these changes. Criteria 2 and 4 now map to the earlier tests; criteria 1, 3 and 5 are unchanged from entries 5 and 12:
    - criterion 2: tests/work/domain/test_acceptance_before_approval.py::test_only_a_stage_before_the_first_approval_is_before_approval
    - criterion 4: tests/work/domain/test_acceptance_before_approval.py::test_an_unknown_stage_or_a_definition_without_approval_is_refused

    **Files:**
    - Created: `tests/support/before_approval_support.py`.
    - Changed: `tests/pipeline/adapters/test_pipeline_yaml.py` (another story's, under the human's leave in entry 19), `tests/work/domain/test_acceptance_before_approval.py` (another story's, under the standing leave) and `tests/work/domain/test_acceptance_before_approval_routes.py` (this story's).
    - The test run imported every module.

    **Run:** `uv run pytest -q` passed on the three changed modules plus `tests/guards/test_areas.py` and `tests/guards/test_shared_imports.py`. The first try failed in `test_an_unknown_stage_or_a_definition_without_approval_is_refused[no-approval-stage]` with `TypeError: 'bool' object is not callable` (the shadowing), and the alias fixed it. `make lint` is green (`lint: green (0.1 s)`).

    **For the docs stage:** besides `tests/support/two_routes_support.py` (entry 8), the *Shared test helpers* list in `docs/project-guide/README.md` should also name the new `tests/support/before_approval_support.py`.

    `lint`: lint: green (0.2 s)
24. factory: started doing as vm.
25. coder: Rework round 1, the last step of the human's answer (a) in entry 19. The tester has now deleted the only remaining caller (entry 23), so I removed `PipelineDefinition.position` from `src/factory/pipeline/domain/pipeline_definition.py`. A grep for `.position` / `def position` over `src` and `tests` finds nothing else. `PipelineDefinition`'s fields are unchanged, so the generated contract stays as it is and nothing needs regenerating.

    What I built in this story:
    - `src/factory/work/domain/acceptance.py::is_before_approval`, unchanged since entry 14. It walks the `next[0]` chain from the stage, keeping a set of stages it has visited. It returns `True` when it reaches an approval stage, and `False` at an approval stage itself, at a stage without `next`, or when the chain comes back to a visited stage (a loop).
    - Main choice: follow the forward chain. I rejected keeping the comparison by position and reordering `factory/pipeline.yml` instead, which is the alternative the description rejects.

    Refactor: I read the diff again (`git diff main -- . ':!factory'`) and found nothing to change.

    `make check` is green (`test: green (140.7 s)`, `check: green`, coverage 99.26 %).

    For the docs stage (not done here): criterion 7 as entry 8 changed it. That includes naming `tests/support/two_routes_support.py` and `tests/support/before_approval_support.py` in the *Shared test helpers* list of `docs/project-guide/README.md`, as entries 21 and 23 note.

    Noticed, not touched: nothing.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
26. factory: started review as vm.
27. reviewer: Review, round 1. I read the work item and `git diff main...HEAD -- . ':!factory'`, which covers nine files. I also ran `make duplicates` to read its new findings.

    - **Code.** `is_before_approval` (`src/factory/work/domain/acceptance.py:309-327`) keeps its `KeyError` and `ValueError` paths. It gives `False` for an approval stage. It follows `next[0]` with a visited set, returns `True` at an approval stage, and returns `False` at a stage without `next` or on a loop. That matches every rule of the Interface. `PipelineDefinition.position` is removed (`src/factory/pipeline/domain/pipeline_definition.py`), as the human decided in entry 19, and no caller is left under `src/` or `tests/`.
    - **Criteria.** Criterion 1 has 12 rows on `TWO_ROUTES`, parsed through the reader. Its stages and `next[0]` match the shipped `factory/pipeline.yml`. Criterion 3 has three rows: `loop`, `dead-end-at-done` and `three-moves`. Criteria 2 and 4 map to the earlier tests `tests/work/domain/test_acceptance_before_approval.py::test_only_a_stage_before_the_first_approval_is_before_approval` and `::test_an_unknown_stage_or_a_definition_without_approval_is_refused`, which use the same definitions as before. Criterion 5 has the rows `at-acceptance` and `at-approval` in the fake world. The factory's `make check` after the coder was green (entry 25).
    - **Architecture.** The change is a pure domain rule and adds no import.
    - **Security.** Nothing to report, and no silencing marker.
    - **`make duplicates`.** 5 new findings, none of them in a file this diff touches (`claude_runtime`/`opencode_runtime`, `hand_over`/`work.application.acceptance`, `cost_records.py`).
    - **Round 0 findings.** Findings 1 to 4 of entry 16 are fixed. Finding 5 is corrected below.

    no findings

    description corrected:
    - `The booking, the merge handling and the pipeline definition stay as they are.` -> `The booking, the merge handling and factory/pipeline.yml stay as they are. PipelineDefinition.position goes, because no code calls it once this rule follows the forward moves (the human's answer in the journal).` This follows from entry 19.
    - Criterion 7 named neither the shared-helper list nor the removed method. It now also names:
      - `docs/project-guide/pipeline.md`, *The pipeline definition*: the list of methods no longer names `position(stage)`. Line 59 still lists it today.
      - `docs/project-guide/README.md`, *Shared test helpers*: the list names `support/two_routes_support.py` (`TWO_ROUTES`) and `support/before_approval_support.py` (`ROLES`, `FIXTURE`, `without_approval`).

      This follows from the human's answers in entries 8 and 19, and from that list's rule that a story adding a support module names it through its docs criterion. The coder's earlier rewrite was dropped by the take.

    Earlier tests:
    - `tests/pipeline/application/test_docs_route.py`: `TWO_ROUTES` moved to `tests/support/two_routes_support.py` under the standing leave to move a shared test helper. The row `("acceptance", False)` became `("acceptance", True)` under the human's leave, feature decision 7, which the Interface names. Nothing else changed.
    - `tests/pipeline/adapters/test_pipeline_yaml.py`: `test_position_is_the_index_in_the_stages` deleted under the human's leave in entry 19. Nothing else in the module changed.
    - `tests/work/domain/test_acceptance_before_approval.py`: `FIXTURE` and `_without_approval` moved to `tests/support/before_approval_support.py`, and `ROLES` was split out of `FIXTURE`, under the standing leave to move a shared test helper. Every test keeps its name and checks the same thing.
28. factory: started docs as vm.
29. documenter: Docs, round 1. I read the story, the diff against main, and the project guide pages that mention the rule. I changed only documents, so I did not run `make check`. The factory's checks decide.

    Files changed:
    - `docs/project-guide/pipeline.md`, *More than one route, more than one approval stage*: `is_before_approval` now follows the first `next` of each stage. The paragraph says when the answer is `True` and when it is `False`, and says the order of the stages in the file does not matter. The sentence that every route's stages must be listed before the first approval stage is gone. "three rules read the order and the `next` lists" became "read the `next` lists".
    - `docs/project-guide/pipeline.md`, *The pipeline definition*: the list of methods no longer names `position(stage)`, which the coder removed.
    - `docs/project-guide/README.md`, *Shared test helpers*: added `support/before_approval_support.py` (`ROLES`, `FIXTURE`, `without_approval`) and `support/two_routes_support.py` (`TWO_ROUTES`), each in alphabetical place in the first list.
    - `docs/decisions.md`: one new entry, "Before the approval" is read from the forward moves. Its Why and its Rejected line come from the story's docs criterion: the docs route lists `docs-approval` before `acceptance`, and reordering `factory/pipeline.yml` was rejected because nothing checks the file's order.

    Cross-read and found current:
    - `docs/operator-guide/work-items.md`, *Merged before its approval*. The criterion says it holds true again, and I changed nothing.
    - `docs/project-guide/work.md` and the rest of `docs/project-guide/pipeline.md`: no other mention of `is_before_approval` or `position`.
    - The older decision entry on a merge before the approval (2026-10-15) still holds. It does not describe how the stage is judged.

    No findings for the coder. The code matches the Interface (`src/factory/work/domain/acceptance.py`).

    Stale text noticed, not touched: none related to this story.

    `check`: check: green (not run again: passed on tree e8cf3ac1367b at 2026-11-06T00:28:14Z)
    `secrets`: secrets: green (2.0 s)
    `documents`: documents ok
30. factory: started smoke-test as vm.
31. smoke-tester: I ran the smoke test's one command from the repository root, exactly as written. It met its expectation, and I found nothing that contradicts the work item.

    Command 1: parse the shipped `factory/pipeline.yml` and call `is_before_approval` on `acceptance`, `docs-review` and `docs-approval`.

    ```
    True True False
    ```

    Expect: `True True False`. Met.

    Checking the acceptance criteria again:
    - The output agrees with criterion 1 for the three stages it covers: `acceptance` and `docs-review` lie before the approval, and `docs-approval` does not.
    - Criterion 7 also holds. I searched `src/` and found no `def position` and no `.position(` call left. `docs/project-guide/pipeline.md` no longer names `position(stage)` or the rule that a route's stages must be listed before the first approval stage. `docs/project-guide/README.md` lists `support/before_approval_support.py` and `support/two_routes_support.py`. `docs/decisions.md` has an entry titled "Before the approval" is read from the forward moves.
    - The smoke test does not reach criteria 2 to 6: the other tables, the fake-world merge and `make check`. The factory's checks and the earlier stages cover those, and nothing I saw contradicts them.

    Findings: none.
