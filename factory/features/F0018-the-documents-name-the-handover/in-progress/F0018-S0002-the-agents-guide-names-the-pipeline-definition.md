---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 218
comments_read: [6250212284]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T12:59:03.868461Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T12:59:03.873829Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T12:59:20.130700Z'
  stage: intake
  run: f3c6912b075a40df83b177ae7020e8e6
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T13:00:36.241486Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T13:00:53.784861Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T13:01:04.040447Z'
  stage: intake
  run: b6e5fe0f3c554cfd8ed27bbed9a5f1cc
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T13:01:24.051747Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T13:02:48.753069Z'
  stage: tests
  run: 64b62336d28d449d8a44aae8a36e352e
---

# The agents' guide names v1.1's pipeline definition

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

S0001 made the README and the operator guide name the handover, but two passages outside its scope still say that v1's configuration runs this repository. `docs/project-guide.md`, section *The document check*, says "v1's pipeline configuration for this repository runs it as a check of the docs stage through `make documents`". Since the handover, `factory/pipeline.yml` (stage `docs`, `checks: [check, documents]`) does that. `docs/decisions.md`, entry *Three top-level paths for the product beyond `src/` and `tests/`*, says "The coder's write paths in `factory/stages.yml` name them". That file now lies at `factory/v1/stages.yml`, and the coder's write paths are in `factory/pipeline.yml` (`src/*`, `image/*`, `template/*`, `claude/*`). This story makes both passages true for the agents who read them. It is documentation only: the tester and the coder change nothing. Everything else in the two documents stays as it is, and so do `factory/v1/` and the dated history in the decision log's other entries.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/project-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/project-guide.md`, section *The document check*, the sentence that begins "v1's pipeline configuration for this repository runs it" says instead that this repository's pipeline definition (`factory/pipeline.yml`) runs it as a check of the docs stage through `make documents`; the rest of the paragraph stays. In `docs/decisions.md`, entry *Three top-level paths for the product beyond `src/` and `tests/`*, the sentence "The coder's write paths in `factory/stages.yml` name them" says that the coder's write paths in the pipeline definition (`factory/pipeline.yml`; v1's `factory/stages.yml` until the handover of 2026-10-18) name them. No other passage of either document changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "v1's pipeline configuration for this repository" docs/project-guide.md
```
Expect: `0`

```bash
grep -c "The coder's write paths in \`factory/stages.yml\` name them" docs/decisions.md
```
Expect: `0`

```bash
grep -c "v1's \`factory/stages.yml\` until the handover of 2026-10-18" docs/decisions.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: 1. Scope: `feature.md` lists in its Scope only the README's opening and *How it is built*, the operator guide's bullet, and a new decision-log entry for the handover. This story edits `docs/project-guide.md` (section *The document check*) and rewords an existing, dated entry in `docs/decisions.md`. Neither is in the Scope, and the feature's Stories list names only S0001. Out of scope does not exclude them. Do you want `feature.md` widened to cover them and S0002 added to its Stories list? That file is yours to change (R14). I would choose yes: the passages are plainly stale, and the story is the acceptance reviewer's proposal that you started from `backlog/`.
   2. Decision log: criterion 3 rewrites a sentence in an existing dated entry, while the Description keeps "the dated history in the decision log's other entries". Is a rewording in place what you want, or should the correction be a new dated line added to that entry? I would choose the in-place rewording the criterion states, since it keeps the pointer to v1's file.
   3. Criterion 1 ("the tester and the coder each end with an entry saying so") is a statement about journal entries. One test function cannot check it, and it has no check for the files that must not change. Do you accept it as a process note, with the reviewer checking the diff? I would choose yes.
4. 2026-10-18 human: 1. Yes: `feature.md` now names both passages in its Scope and S0002 in its Stories (on main; the next stage start merges it).
   2. Reword in place, as the criterion states, keeping the pointer to v1's file (feature decision 3).
   3. Yes: criterion 1 is a process note; the reviewer checks the diff.
5. factory: started intake as self.
6. intake: accepted
   Interface: "None" is stated and exact: documentation only, no module or signature, so there is no Interface comment or rule needing a criterion.
   Criteria: the intake answers (journal 4) settled criterion 1 as a process note checked by the reviewer's diff. Criterion 2 is `make check`. Criterion 3 gives exact before and after sentences for both passages, and `documents ok` is checkable. Nothing in the story states a validation or error rule, so there is no failing side to cover.
   Smoke test: the four commands are runnable from the repo root, and each has an `Expect:` line checkable against the output (`0`, `0`, `1`, `documents ok`).
   Architecture: nothing under `src/` changes, so the four layers are untouched. Only `docs/project-guide.md` and `docs/decisions.md` change, which is the documenter's job.
   Scope: `feature.md` now names both passages in its Scope and S0002 in its Stories (journal 4, answer 1), and neither is in its Out of scope. The in-place rewording matches feature decision 3. I made no edits to the story.
7. factory: started tests as self.
8. tester: No tests written. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes. The story is documentation only: its Interface is "None", and criterion 1 asks the tester to change nothing.
   criterion 1: no test. It is a process note (journal 4, answer 3), and the reviewer checks it on the diff.
   criterion 2: covered by `make check` itself; no new test.
   criterion 3: no test. It is the documenter's change to `docs/project-guide.md` and `docs/decisions.md`. The smoke test checks it, as does `python -m factory.entry.check_documents` (`documents ok`).
   Files created: none. Modules the test run could not import: none. `make test` is green (coverage 99.44%), so the branch has no red tests, which is intended for this story. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (35.4 s)
