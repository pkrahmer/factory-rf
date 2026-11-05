---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 572
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T21:47:18.190209Z'
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
