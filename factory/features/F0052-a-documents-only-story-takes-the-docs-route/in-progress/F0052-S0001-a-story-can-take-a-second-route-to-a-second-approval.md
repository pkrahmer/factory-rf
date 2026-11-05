---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 572
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-05T21:50:44.049380Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T21:46:48.640497Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T21:46:48.647057Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T21:47:12.581520Z'
  stage: intake
  run: 59f0f1b316854d9dbf59911b4476524b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T21:47:18.190209Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T21:50:38.620716Z'
  stage: tests
  run: b8b14106ed4c42e9891876b3876e8fdb
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-05T21:50:44.049380Z'
  stage: doing
---

# A story can take a second route to a second approval

## Description

F0052 adds a route for documents-only stories: `intake` → `docs-only` → `docs-review` → `docs-approval` → `done` (feature decision 1). The code names no stage, so the factory may already carry a story along it, but nothing proves that it does, and two places are known to depend on the stage order: `is_before_approval` (`factory.work.domain.acceptance`) compares a stage's position with the definition's first approval stage, and a close at an approval stage sends the story to that stage's second `next` (`send_back_target`). This story pins the behaviour with a walk through the fake world, on a pipeline definition written in the test that holds both routes, and fixes whatever the walk finds. It changes no shipped pipeline definition: the human adds the route at S0002's merge.

## Interface

- No new module. Any fix goes where the walk finds the fault, and the coder names it in its entry.
- The test pipeline definition: today's stages of `factory/pipeline.yml`, with `intake.next = [tests, docs-only]` and, after `smoke-test`, the three stages of the feature's *The human's changes* (`docs-only` with `next: [docs-review, tests]`), in that order, then `acceptance`, `approval`, `done`.
- `tests/pipeline/application/test_docs_route.py` (new): the walks of the criteria, in the fake world, with the fake agent runtime giving each role its decision.
- The story's work item lives under `factory/features/<feature>/in-progress/` as any story's does.

## Acceptance criteria

1. A story whose intake decides `docs-only` moves `intake` → `docs-only` → `docs-review` → `docs-approval`, one stage per tick, with one journal entry per stage and the label `stage:<name>` of each stage on its pull request. At `docs-approval` the pull request is handed over (ready for review, the description written), as at `approval`.
2. A merge of that pull request archives the story to `done/` as a merge at `approval` does.
3. A close of that pull request at `docs-approval` sends the story back to `docs-only` (the stage's second `next`), with the send-back's journal entry, and not to `doing`.
4. At `docs-review`, a decision `docs-only` counts one round; a third send-back stops at the round cap of two and asks the human, as at `review`.
5. A story at `docs-only` whose documenter decides `tests` moves to `tests` without a round, then takes today's route `doing` → `review` → `docs` → `smoke-test` → `approval`, and a close there sends it to `doing` (the way back, feature decision 6).
6. A story whose intake decides `tests` still takes today's route to `approval`, unchanged (one walk to `approval`).
7. `is_before_approval` is true for `docs-only` and `docs-review` and false for `docs-approval`, `acceptance` and `approval` in the test definition (one row per stage).
8. `make check` stays green.
9. docs: `docs/project-guide/pipeline.md`, *The pipeline definition*: a definition may hold more than one route and more than one approval stage; a close at an approval stage sends the story to that stage's second `next`. `docs/operator-guide/pipeline.md`: the same, in one sentence for the operator. `docs/decisions.md`: none (the feature's decision 1 goes in at S0002).

## Smoke test

```bash
uv run pytest tests/pipeline/application/test_docs_route.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: no new module by design. It names the one new test file, `tests/pipeline/application/test_docs_route.py`, and the test pipeline definition stage by stage (intake `next`, `docs-only`, `docs-review`, `docs-approval`, their order). It names the two functions the walk exercises in the Description, `is_before_approval` (`factory.work.domain.acceptance:309`) and `send_back_target` (`factory.work.domain.send_back:30`); both exist. Any fix is located by the walk, and the coder names it in its entry.
   - Criteria: 1 to 7 each describe one walk or one table, and each is testable by one test function (7 is one row per stage). Failing sides are covered. The close at `docs-approval` going to `docs-only` and not to `doing` is criterion 3. The round cap is criterion 4, and the round-free move to `tests` is criterion 5. The old route is unchanged in criterion 6. `is_before_approval` is false for the approval stages in criterion 7. The Interface states no rule beyond these. Criteria 8 and 9 are the closing ones, in order.
   - Smoke test: `uv run pytest tests/pipeline/application/test_docs_route.py 2>&1 | tail -1 | grep -c passed` is runnable. It passes no `-q`, and `pyproject.toml` `addopts` already sets one, so the last line is the `N passed` summary. `Expect: 1` can be checked against the output.
   - Architecture: the test sits in `tests/pipeline/application/`, which mirrors the package. It uses the fake world and the fake agent runtime, and git is not faked. A fix would land in the `work` or `pipeline` area. The story makes no new package or dependency and does not touch `factory/pipeline.yml`.
   - Scope: the story is S0001 of F0052 and matches the feature's scope bullet 1. It makes no pipeline definition change (that is the human's at S0002's merge), changes no agent, and does not touch the code route. Nothing in "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: wrote the walks of criteria 1 to 7 in the fake world. They run on a pipeline definition written in the test (`TWO_ROUTES`): the stages, caps, checks and reports of today's `factory/pipeline.yml`, `intake.next = [tests, docs-only]`, and after `smoke-test` the three stages from the feature's *The human's changes*. That puts `docs-only`, `docs-review` and `docs-approval` before `acceptance`, `approval` and `done`. The test pushes the definition to `main` with a Makefile that has every target the definition names, then starts the story.

   - criterion 1: tests/pipeline/application/test_docs_route.py::test_an_intake_decision_docs_only_walks_the_docs_route_to_a_hand_over_at_docs_approval
   - criterion 2: tests/pipeline/application/test_docs_route.py::test_a_merge_at_docs_approval_archives_the_story_to_done
   - criterion 3: tests/pipeline/application/test_docs_route.py::test_a_close_at_docs_approval_sends_the_story_back_to_docs_only
   - criterion 4: tests/pipeline/application/test_docs_route.py::test_a_send_back_at_docs_review_counts_a_round_and_the_third_asks_the_human (rows: first send-back, second at the cap, third past the cap)
   - criterion 5: tests/pipeline/application/test_docs_route.py::test_a_documenter_decision_tests_takes_the_code_route_whose_close_sends_back_to_doing
   - criterion 6: tests/pipeline/application/test_docs_route.py::test_an_intake_decision_tests_still_takes_todays_route_to_approval
   - criterion 7: tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval (one row per stage)

   How I read the criteria:
   - Criterion 1's "one journal entry per stage" is checked as one `result` record each for intake, docs-only and docs-review. No agent runs at docs-approval.
   - The hand-over is checked by `handed_over == "docs-approval"`, the pull request no longer a draft, and its description ending with `HAND_OVER_CLOSING`.
   - For criteria 3 and 5, the human comments before the close, so the send-back has a reason and asks no question.

   Files created: tests/pipeline/application/test_docs_route.py. No earlier test file was changed.

   Result of the one run (`uv run pytest -q tests/pipeline/application/test_docs_route.py`): 13 passed. Every module imported, and nothing failed. The walk found no fault in today's code, so there are no red tests on this branch: the story's "fixes whatever the walk finds" comes down to nothing to fix, and the coder has only to confirm `make check`. Two lint-only edits came after that run: a line split, and the parametrized test's case values made keyword-only. `make lint` is green. The type check was skipped, as this stage says.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
