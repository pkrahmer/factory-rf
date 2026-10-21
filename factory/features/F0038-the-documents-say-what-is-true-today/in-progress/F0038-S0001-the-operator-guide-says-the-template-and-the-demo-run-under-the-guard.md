---
stage: doing
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
