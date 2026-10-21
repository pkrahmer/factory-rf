---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 388
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T06:42:57.092978Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T06:42:57.098741Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T06:43:16.729461Z'
  stage: intake
  run: c60ba677f885486283c251c9f2640c71
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T06:43:37.077731Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T06:44:54.810338Z'
  stage: tests
  run: 4bebf755dacc4096b41cbea50a0bb9d8
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T06:45:15.659823Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T06:46:39.443954Z'
  stage: doing
  run: 890a0742403649789ceaa49bf3523e74
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T06:47:00.593857Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T06:47:23.497143Z'
  stage: review
  run: 0bf413df0ec04ef8956611322e33442f
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T06:47:44.377300Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T06:48:06.894104Z'
  stage: docs
  run: b3b0ec0c041b4f5db4b866d92e0877d5
---

# The operator guide says the template and the todo demo run under the write guard

## Description

`docs/operator-guide.md`, *The pipeline definition*, says that a project made from `template/`, and the todo demo, "do not run under the guard as they are": their `licenses` recipe and coverage are said to write at the checkout's root, and "until then its `make check` ends with `Permission denied`". That has not been true since both were changed. `template/Makefile` and `demo/todo-service/project/Makefile` write `.reports/licenses-requirements.txt`, the template's `test` recipe sets `COVERAGE_FILE=.reports/.coverage`, the demo's `pyproject.toml` sets `data_file = ".reports/.coverage"`, and both pipeline definitions (`template/factory/pipeline.yml`, `demo/todo-service/project/factory/pipeline.yml`) name `tool_paths` with `.reports/*`. An operator who starts a project from the template is told to make a fix that is already made and to expect a red `make check` that does not happen. This story replaces that one paragraph (finding H1 of the documentation review of 2026-10-20). It changes no other passage.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes one paragraph of `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The pipeline definition*: the paragraph that begins "A project made from `template/`, and the todo demo, do not run under the guard as they are." becomes exactly this paragraph, and no other passage changes:

   "A project made from `template/`, and the todo demo, run under the guard as they are: their tools keep their files under `.reports/` (the `licenses` recipe's requirements file, and coverage's data file), and their pipeline definitions name `.reports/*` in `tool_paths`. A project whose tools write anywhere else at the checkout's root moves those files into a folder its `tool_paths` names, the same way; until then its `make check` ends with `Permission denied`."

   `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F 'do not run under the guard as they are' docs/operator-guide.md || true
grep -c -F 'A project made from `template/`, and the todo demo, run under the guard as they are' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
grep -c -F '.reports/licenses-requirements.txt' template/Makefile demo/todo-service/project/Makefile
grep -c -F '".reports/*"' template/factory/pipeline.yml demo/todo-service/project/factory/pipeline.yml
```
Expect: four lines, `template/Makefile:3`, `demo/todo-service/project/Makefile:3`, `template/factory/pipeline.yml:1`, `demo/todo-service/project/factory/pipeline.yml:1` (what the new paragraph says is what the files hold)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. Nothing under src/, tests/, image/, template/, demo/ or claude/ changes, and the one edited passage is a single paragraph of docs/operator-guide.md.
   - Criteria: criterion 1 (no change outside docs) and criterion 2 (`make check` green) can each be checked by one test or command. Criterion 3 gives the exact new paragraph and says no other passage changes. It is checkable by text match. I confirmed the old paragraph exists exactly once, at docs/operator-guide.md:968. The story states no Interface rule, so no failing side is missing.
   - Smoke test: every command is runnable. I ran the greps against the tree and they give template/Makefile:3, demo Makefile:3, and :1 for each pipeline.yml, as the Expect line says. The old phrase currently counts 1, so the first block (0 and 1) will hold once the paragraph is replaced. `make documents` exists (Makefile:94), and the pytest -q trap does not apply because no command runs pytest. Each Expect line is checkable.
   - Architecture: the story is documents only and is within the documenter's write paths (README.md, docs/*). It touches no layer.
   - Scope: it matches F0038 S0001 (finding H1) in feature.md, and nothing in "Out of scope" is involved.
4. factory: started tests as self.
5. tester: No tests were written, and nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage. This is a documents-only story, and its Interface is "None". Criterion 1 forbids changes under `tests/`, so a test of the documentation paragraph would break the story itself.
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/, claude/ changes): no test. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude` checks it, and this entry states it for the tests stage.
   - criterion 2 (`make check` stays green): no test. The factory's checks enforce it.
   - criterion 3 (docs: the replaced paragraph in `docs/operator-guide.md`, `make documents` ends with `documents ok`): no test. It is the documenter's docs criterion, checked by the smoke test's greps and by `make documents`.
   Files created: none. Modules the test run could not import: none, because no new tests exist. I did not run `make test`: there is no red test to confirm, so the branch stays green on purpose. `make lint`: green.

   `lint`: lint: green (0.5 s)
   `test`: test: green (61.0 s)
6. factory: started doing as self.
7. coder: Built nothing. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage, which is what criterion 1 asks for. This is a documents-only story with Interface "None". Its one change is the paragraph of `docs/operator-guide.md` that criterion 3 names, and that paragraph is the documenter's job: it is outside the coder's remit.
   - Main choice: I handed forward with no code change. I rejected editing `docs/operator-guide.md` now, because `CLAUDE.md` says the documenter keeps the docs and the coder does not write them.
   - Verified: `make check` ran green on the unchanged tree (`test: green (61.3 s)`, `check: green`, coverage 99.14 %).
   - Refactor: there is no diff, so nothing to refactor.
   - Description: the journal did not change the meaning of the task.
   - Noticed but did not touch: nothing.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T06:37:06Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed, so criterion 1 holds, and the tester's entry (5) and the coder's entry (7) each say so.
   - Criterion 2: the coder's entry records `check: green`.
   - Criterion 3 is the docs stage's job. I checked the new paragraph's claims against the tree, and they hold:
     - `template/Makefile:76` and `demo/todo-service/project/Makefile:75` write `.reports/licenses-requirements.txt`.
     - `template/Makefile:89` sets `COVERAGE_FILE=.reports/.coverage`.
     - `demo/todo-service/project/pyproject.toml:103` sets `data_file = ".reports/.coverage"`.
     - Both pipeline definitions name `.reports/*` in `tool_paths`.
     - The old paragraph is still at `docs/operator-guide.md:968`, where the documenter will replace it.
   - Hygiene: the Description matches the work so far (no code), and the docs criterion gives the exact text the documenter writes.
   - Earlier tests: `git diff --name-status main...HEAD` changes no test file, so no leave was needed.
10. factory: started docs as self.
11. documenter: Files changed: `docs/operator-guide.md`, *The pipeline definition*. I replaced the one paragraph that began "A project made from `template/`, and the todo demo, do not run under the guard as they are." with the exact text criterion 3 gives. It was wrong because the template and the demo already keep their licenses and coverage files under `.reports/` and name `.reports/*` in `tool_paths`. No other passage changed. `make documents` ends with `documents ok`.

    Checked against the tree: the reviewer's entry 9 verified the paragraph's claims about the Makefiles, `pyproject.toml` and both pipeline definitions. I did not re-read those files myself. I did not run `make check`, because the only file I changed is a document; the factory's checks decide.

    Cross-read: the diff has no code change, so there was nothing else to cross-read against. I read the paragraph's immediate surroundings (the `not_read` bullets before it and the "rules you meet most often" list after it) and found them unaffected.

    Findings: none. Stale text I noticed but did not touch: none.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T06:37:06Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
