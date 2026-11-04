---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 534
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-04T03:14:48.377833Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T03:11:27.466666Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T03:11:27.474081Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T03:11:45.554079Z'
  stage: intake
  run: 8afe29d66481488cba5825320a86071f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T03:11:51.297850Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T03:12:13.913652Z'
  stage: tests
  run: 34b45c1e6ff1428484507aac7d489a56
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T03:12:20.021341Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T03:14:14.027605Z'
  stage: doing
  run: 5da7e7f8e6f942aebf0d611504d32d59
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T03:14:21.969138Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T03:14:42.493005Z'
  stage: review
  run: 300c46a6500e4a2b98de24395dd9905d
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T03:14:48.377833Z'
  stage: docs
---

# The stops table and the test helper index follow the stage image

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Two documents still describe the stage image as it was before the feature's last stories. First, the stops table in `docs/operator-guide.md` (*The stops*) still says, in its `stage-image-failed` row, "Fix the file on `main` and start `factory-run` again". Since F0049-S0003 no restart is needed: the factory compares the stage file on `origin/main` before every tick, and the next `main` with another file, or without the file, ends the stop before the next stage. *A change on `main` takes effect before the next stage* ("No restart is needed") and *The stop `stage_image_failed`* already say so. The row is the one place that sends the operator to a restart. Second, F0049-S0004 moved the stage image tests' shared values into the new support module `tests/stage_image_support.py`, and their fixtures `base_identity_settings` and `base_image` into `tests/conftest.py`. Neither is in the index *Shared test helpers* of `docs/project-guide/README.md`, which the guide tells agents to read before writing a helper, and where the reviewer looks before counting a copy. This story corrects the row and adds both to the index. No code and no test change. What a restart does stays as *The stop `stage_image_failed`* says it.

## Interface

- No module under `src/factory/` changes, and no test: the story changes `docs/operator-guide.md` and `docs/project-guide/README.md` only.
- What the documenter carries into the index, from `tests/stage_image_support.py` and `tests/conftest.py` as they are on `main`:
  - `stage_image_support.py`: `BASE_IDENTITY` (the base image's identity, `"sha256-base"`), `FIRST` and `SECOND` (two stage files that satisfy the rule), `StageSeen` (what one tick ran with: image, identity, `PATH`, builds asked for), `built_path` (the project image's `PATH` after a given build).
  - `conftest.py`: `base_identity_settings` (the instance settings with `BASE_IDENTITY` as the image identity) and `base_image` (the base image those settings name).

## Acceptance criteria

1. `docs/operator-guide.md`, the stops table's `stage-image-failed` row: it says that the fix of `factory/stage.Containerfile` on `main` takes effect before the next stage with no restart, and it points to "The project's stage file". The text "start `factory-run` again" is gone from the row, and the other rows of the table are unchanged.
2. `docs/project-guide/README.md`, *Shared test helpers*: one entry for `stage_image_support.py` that names `BASE_IDENTITY`, `FIRST`, `SECOND`, `StageSeen` and `built_path`. The entry for `conftest.py` names the fixtures `base_identity_settings` and `base_image`. No other entry of the index changes.
3. `make check` stays green.
4. docs: `docs/operator-guide.md` and `docs/project-guide/README.md` as criteria 1 and 2 say. `README.md`: none, because its one sentence on the stage file stays true. `docs/decisions.md`: none, because no decision changes.

## Smoke test

```bash
grep -cF 'Fix the file on `main` and start `factory-run` again' docs/operator-guide.md
grep -qF '`stage_image_support.py`' docs/project-guide/README.md && echo listed
grep -qF '`base_identity_settings`' docs/project-guide/README.md && echo listed
uv run python -m factory.entry.check_documents
```

Expect: `0`, then `listed`, then `listed`, then `documents ok`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names the two files that change (`docs/operator-guide.md`, `docs/project-guide/README.md`) and the helpers to index. I checked that `BASE_IDENTITY`, `FIRST`, `SECOND`, `StageSeen` and `built_path` exist in `tests/stage_image_support.py`, and that `base_identity_settings` and `base_image` exist in `tests/conftest.py`. The stage-image row is at `docs/operator-guide.md:1608` with the text the story quotes, and the section "The project's stage file" exists. No source change, and no behaviour is stated in the Interface that would need a criterion.
   - Criteria: 1 and 2 are each checkable by a grep or a read. They are document edits, and the failing side is the removal of the old text, which criterion 1 states. Criterion 2 also says no other index entry changes. The two closing criteria (`make check`, `docs:`) are in place.
   - Smoke test: the greps and `uv run python -m factory.entry.check_documents` are runnable, and the Expect line (`0`, `listed`, `listed`, `documents ok`) matches their output. The story has no pytest command, so the `-q` rule does not apply. The first grep prints `0` but exits 1; this is harmless as a manual check.
   - Architecture: docs only, which fits CLAUDE.md's split. The documenter keeps `docs/*`, and the story edits no code, no test and nothing in `factory/`.
   - Scope: this is a follow-up to F0049-S0003 (no restart) and S0004 (support module), within the feature's stage-image topic. It is not in "Out of scope". It does not touch `README.md`, `docs/decisions.md` or any test.
4. factory: started tests as vm.
5. tester: No tests written. The Interface says this story changes only `docs/operator-guide.md` and `docs/project-guide/README.md`, and that no module under `src/factory/` and no test changes. A pytest test that reads those two documents for the new wording would be a test change the story rules out. Writing one anyway would also add a test that pins documentation text, which nothing in the project does today.
   - criterion 1 (the `stage-image-failed` row in the stops table: no restart, points to "The project's stage file", "start `factory-run` again" removed): no test, by the Interface. It is checked by the smoke test's first grep (expects `0`) and by the reviewer reading the row.
   - criterion 2 (the *Shared test helpers* index lists `stage_image_support.py` with `BASE_IDENTITY`, `FIRST`, `SECOND`, `StageSeen`, `built_path`, and the `conftest.py` entry names `base_identity_settings` and `base_image`): no test, by the Interface. It is checked by the smoke test's second and third greps and by the reviewer.
   - criterion 3 (`make check` stays green): checked by the coder's `make check` and the factory's gate. No test of its own.
   - criterion 4 (docs): the documenter's criterion, checked by `make documents` (`uv run python -m factory.entry.check_documents`) after the docs stage.
   Rejected: grep-style tests under `tests/` for the two documents. The Interface forbids test changes, and the smoke test already holds those checks.
   Files created: none. Modules the test run could not import: none (no test run, because there are no new tests). `make lint` is green.
   Open: none. The coder has no code to write. The doc edits belong to the documenter, as CLAUDE.md's *Docs* section says.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Built nothing: no path changed in this stage. The story changes only `docs/operator-guide.md` (the stops table's `stage-image-failed` row) and `docs/project-guide/README.md` (the *Shared test helpers* index). The Interface says no module under `src/factory/` and no test changes, and the tester wrote no tests, so `make test` had no failures to work from. I ran `make check` on the untouched branch and it ended `check: green` (test: green, coverage 99.52 %).
      - Main choice: leave both document edits to the documenter. `CLAUDE.md` *Docs* says the documenter keeps `docs/operator-guide.md` and `docs/project-guide/` from each story's docs criterion and the coder does not write them. Criterion 4 names both files as the docs criterion. Rejected: making the row and index edits here. They are outside the coder's part of the work, and the documenter would redo them anyway.
      - Refactor: there is no diff, so there was nothing to refactor.
      - Journal: no entry changed the meaning of the task, so `## Description` is unchanged.
      - Noticed, not touched: criteria 1 and 2 can only be checked after the docs stage. A reviewer reading this stage's diff will find nothing to check against them.

   `check`: check: green (not run again: passed on tree c75cce644896 at 2026-11-04T02:57:19Z)
   `duplicates`: duplicates: 0 new, 43 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty, as the story expects. It is a docs-only story, and the Interface rules out any change under `src/factory/` or `tests/`. Both edits belong to the documenter, from criterion 4.
   - Group 1, acceptance criteria: criteria 1 and 2 are document edits, and the smoke test's greps and the docs stage's `make documents` check them. No rule in the Interface has a failing side that a test could pin. The tester decided not to write grep tests of document text, and I agree: the Interface forbids test changes. Criterion 3: the coder's journal entry 7 says `make check` was green (coverage 99.52 %).
   - I checked the Interface's facts against `main`:
     - The row is at `docs/operator-guide.md:1608` and still holds "Fix the file on `main` and start `factory-run` again".
     - The section "The project's stage file" exists at `docs/operator-guide.md:509`.
     - `BASE_IDENTITY` (`"sha256-base"`), `FIRST`, `SECOND`, `StageSeen` and `built_path` are in `tests/stage_image_support.py:7-22`.
     - The fixtures `base_identity_settings` and `base_image` are in `tests/conftest.py:529,535`.
     - The index *Shared test helpers* is at `docs/project-guide/README.md:23`.
     
     So the documenter can carry out criteria 1 and 2 as written.
   - Groups 2 to 4 (architecture, security, quality): there is no code diff, so nothing applies.
   - Group 5, work item hygiene: the Description matches the story's purpose. The tester's and coder's journal entries say why no test and no code were written, and what they rejected. The docs criterion names both documents and why `README.md` and `docs/decisions.md` stay unchanged.

   Earlier tests: none. The diff changes no test file.
10. factory: started docs as vm.
