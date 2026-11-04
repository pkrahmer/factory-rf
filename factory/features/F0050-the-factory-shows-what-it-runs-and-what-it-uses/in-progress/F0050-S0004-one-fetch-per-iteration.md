---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 542
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T14:22:54.868675Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T14:22:54.875427Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T14:23:19.708543Z'
  stage: intake
  run: a95ab27cceb64c3091dcc3fc2106828a
  blocked: question
---

# One fetch per iteration

## Description

Since F0049-S0003 and S0004 the factory fetches twice in every iteration: once before the tick, where it compares the stage file on a new `main` (`_ProjectImageStart._follow_main` in `factory.entry.run`), and once more at the start of the tick itself (`factory.application.tick`). The second fetch finds nothing new in almost every case, but it costs a call to the remote and its time in every iteration, and both places raise and clear `fetch_failed` on their own. This story makes the factory fetch once per iteration: the fetch before the tick serves the tick too, and `fetch_failed` is raised and cleared in one place. What the tick sees of `origin/main` and of the work-item branches does not change.

## Interface

- One iteration of `factory-run` calls `Git.fetch` once. The coder decides which of the two places keeps it and how the other learns that the fetch was made; the tick still works on a fresh `origin/main` and fresh work-item branches.
- A failed fetch stands as `fetch_failed` (S0004 of F0049), raised in one place, and ends the iteration without a tick; a passed fetch clears it.
- `factory-watch` and every other caller of the tick keep fetching as today, when they run the tick without the fetch before it.

## Acceptance criteria

1. One iteration of `factory-run` with a passed fetch calls `Git.fetch` exactly once and runs the tick on what that fetch brought: rows for a new commit on `main` and for a new commit on a work-item branch, each seen by the same iteration's tick.
2. One iteration with a failed fetch calls `Git.fetch` once, raises `fetch_failed` with the fetch's first line in its detail, and runs no tick; the next iteration with a passed fetch clears the stop and runs the tick.
3. A tick run without the fetch before it (as `factory-watch` runs it) still fetches once.
4. `make check` stays green.
5. docs: `docs/project-guide/` in the file on the tick or the stage environment: where the iteration fetches, once. `docs/operator-guide.md` and `docs/decisions.md`: none, unless an existing sentence says the tick fetches; then that sentence follows. `README.md`: none.

## Smoke test

```bash
grep -rn 'git.fetch()' src/factory/application src/factory/entry | wc -l
uv run pytest tests/entry tests/application -k fetch 2>&1 | tail -1
```

Expect: a number not larger than before the story (3 on `main` when it was written), then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed):

   1. The Interface names no concrete seam. "The coder decides which of the two places keeps it and how the other learns that the fetch was made" leaves the tester without a signature to write tests against. Two testers could pick different seams, and both would pass criteria 1 to 3. Please name the seam. For example: `Tick.run(fetched: bool = False)` in `factory.application.tick`, which skips `git.fetch()` when the caller already fetched; `_ProjectImageStart._follow_main` in `factory.entry.run` keeps the one fetch and the one raise and clear of `fetch_failed`. I would choose this option, because `factory-watch` then keeps today's default.

   2. `src/factory/application/scheduler.py:126` also calls `self._boundaries.git.fetch()`. The Description and the smoke test count three calls on `main`: tick.py:148, scheduler.py:126 and run.py:235. The story does not say what that call does, or whether it is in the iteration's path. Please say if it belongs to this story (for example, if it is the tick's fetch via the scheduler) or stays as it is. The smoke test's "not larger than before" count depends on the answer.

   3. The Interface says a failed fetch is "raised in one place". Criterion 2 tests this only through `factory-run`. A tick run without the fetch before it, as `factory-watch` runs it, also raises and clears `fetch_failed` at tick.py:148. Does criterion 3 cover that failing side? Please add a criterion for it: a tick run alone with a failed fetch stops as it does today, or the Interface says it no longer raises it. Without this the failing side of the "keep fetching as today" rule has no test.

   4. Criterion 1 has two clauses, a new commit on `main` and a new commit on a work-item branch, in one criterion. A single test function cannot easily show both. Please split it into two criteria, or confirm that one test with two assertions is meant.

   The other checks passed. The smoke test is runnable, and `addopts` already sets `-q`, so the `tail -1` summary line exists. The scope fits the feature (S0004 in `feature.md`). The layers hold: the entry fetches and the application tick receives the knowledge.
