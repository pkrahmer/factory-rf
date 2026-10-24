---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 425
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-24T22:20:38.596275Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T22:14:25.147163Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T22:14:25.153110Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T22:14:40.591173Z'
  stage: intake
  run: cf9d10ead2034f75a830dd9ed8c5673a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T22:15:00.838289Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T22:16:23.105444Z'
  stage: tests
  run: ddc4dcfe19af426ebd38905bf8b66130
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T22:16:43.495401Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T22:19:26.871875Z'
  stage: doing
  run: 4eb10380a54445cea7cd89102f573d30
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T22:19:47.365716Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T22:20:17.952409Z'
  stage: review
  run: 9d0128124e5e4bea87fb40ce7b970de2
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T22:20:38.596275Z'
  stage: docs
---

# The guides say what is true after the wiring

<!-- proposed by feature acceptance of 2026-10-24; refine before starting -->

## Description

The stories of F0042 were documented one at a time, and some sentences were true only while a later story was still to come. Since S0010, `build_boundaries` wires a `container` instance: `ContainerMakeCommands` behind `RecordingProjectCommands`, and the runtimes with their `PodmanRuns`. Since the human's change 1, this repository's own `Makefile` and `factory/pipeline.yml` have `sync`. Three passages still say otherwise. Three more describe only the inline environment where the container environment behaves differently:

- the cost sidecar is rewritten after the undo, which under `container` is the take;
- a stall "undoes the rest";
- `Boundaries.project_commands` is described as the inline chain alone.

This story corrects those six passages and nothing else. The inline environment's own descriptions stay, because F0044 removes them. For the operator and for the agents who read the project guide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template or an agent file. The documenter changes `docs/project-guide/processes-and-checks.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/watching.md`, `docs/project-guide/costs.md` and `docs/operator-guide.md`, as the docs criterion says. No test reads the documents; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter makes the following true, each passage checked against the code on `main`:
   - `docs/project-guide/processes-and-checks.md`, *Project commands*: the sentence "This repository's own `Makefile` and `factory/pipeline.yml` do not have it yet: that is the human's change." is gone. In its place, this repository's `Makefile` has the target `sync` (`uv sync --frozen`) and `factory/pipeline.yml` has the command `sync` with `time_limit: 5`.
   - `docs/project-guide/processes-and-checks.md`, the paragraph on `ContainerMakeCommands`: the sentence "The wiring that puts it behind `RecordingProjectCommands` for a `container` instance is a later story; until then nothing builds it." is gone. In its place, `build_boundaries` puts it behind `RecordingProjectCommands` for a `container` instance (see `stage-environment.md`, *The settings and the wiring*).
   - `docs/project-guide/stage-environment.md`, *The agent's container*: the sentence "The wiring that gives a `container` instance's runtimes their `PodmanRuns` is a later story's." is gone. In its place, `build_boundaries` gives the runtime of `FACTORY_AGENT_RUNTIME` its `PodmanRuns` for a `container` instance (*The settings and the wiring*).
   - `docs/project-guide/watching.md`, *Boundaries*: the sentence on `build_boundaries`' `project_commands` names both cases. For `inline` it is `RecordingProjectCommands` around `SealedProjectCommands`, as now. For `container` it is `RecordingProjectCommands` around `ContainerMakeCommands`.
   - `docs/project-guide/costs.md`: the bullets "Until the stage's commit, the running run's record is uncommitted" and "Rewritten after every undo" say that the sidecar is rewritten after the take, which is the undo under `inline`. They say that under `container` the agent works on the dataset, where the sidecar is the one committed at the stage-start commit, and that the factory rewrites the host's copy after the take as it does after the undo. The bullet's title becomes "Rewritten after every take".
   - `docs/operator-guide.md`, *A stall: the stall note*: "undoes the rest" becomes a sentence true of both environments. The factory keeps what the agent wrote inside the stage's write paths and leaves out the rest: an `inline` instance undoes it, and a `container` instance does not take it from the dataset.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c 'do not have it yet' docs/project-guide/processes-and-checks.md; grep -c 'until then nothing builds it' docs/project-guide/processes-and-checks.md; grep -c "is a later story's" docs/project-guide/stage-environment.md; grep -c 'Rewritten after every undo' docs/project-guide/costs.md; grep -c 'undoes the rest' docs/operator-guide.md
```
Expect: five lines, each `0`

```bash
grep -c 'Rewritten after every take' docs/project-guide/costs.md; grep -c 'ContainerMakeCommands' docs/project-guide/watching.md
```
Expect: two lines, `1` and a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a documents-only story. It names the five documents the documenter changes, and each exists in the docs layout CLAUDE.md describes.
   Criteria: 1 and 2 are testable (nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; `make check` is green). Criterion 3 is the docs criterion. It lists six passages with their old and new wording, plus `documents ok`. Each passage has its own check, a grep in the smoke test or the code on `main`. The story states no Interface rule, so there is no failing side to cover. The factory's format check passed.
   Smoke test: the greps are runnable, and every `Expect:` line is checkable (five zeros; `1` and at least `1`; `documents ok`). The patterns match the quoted sentences. The `make documents` command passes no pytest flags.
   Architecture: no code or layer is touched. The new text matches the stage-environment guide's *The settings and the wiring* and the S0010 wiring that F0042 describes.
   Scope: it fits F0042. It is a sweep after S0012, it keeps the inline environment's descriptions (F0044 removes them), and it touches nothing in "Out of scope".
4. factory: started tests as self.
5. tester: No tests written. This story only changes documents, and its Interface says no test reads them.
   criterion 1: no test. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes, and this stage changed nothing there. `git status` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   criterion 2: no new test. The factory's `make check` covers it.
   criterion 3: no test. It is the docs criterion, which the smoke test and `make documents` check.
   Files created: none. Modules the test runner could not import: none. There are no new tests, so I did not run `make test` to look for red: there is nothing new that could fail.
   `make lint`: green.
   Nothing is open.

   `lint`: lint: green (0.5 s)
   `test`: test: green (65.6 s)
6. factory: started doing as self.
7. coder: No code written. This story only changes documents. Its Interface says nothing under `src/factory/`, in any test, the image, the template or an agent file changes, and the documenter writes the six passages.
   criterion 1: nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changed in this stage. `git status --short` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
   criterion 2: I ran `make check` in the foreground and it ended with `check: green` (`test: green (66.1 s)`, coverage 99.19 %).
   criterion 3: left to the docs stage.
   Main choice: I left the working tree as it was. The alternative I rejected was editing the five documents here, because `CLAUDE.md` gives the four guides to the documenter, not the coder.
   Refactor: there is no diff, so nothing needed changing.
   The journal did not change the meaning of the task.
   Noticed but not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar, which the factory writes.
   - Criterion 1: holds. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changed. The tester's entry (5) and the coder's entry (7) each say so.
   - Criterion 2: the coder's `make check` ended with `check: green` (entry 7). The 11 new `duplicates` findings in that record cannot come from this diff, which has no code.
   - Criterion 3: the docs criterion. I checked its six claims against `main`:
     - `Makefile:27` has `sync` (`uv sync --frozen`), and `factory/pipeline.yml:16` has `sync: {time_limit: 5}`.
     - `src/factory/entry/wiring.py:369` builds `ContainerMakeCommands` for a `container` instance, and `src/factory/entry/wiring.py:397` builds its `PodmanRuns`.
     - All six stale passages are still in the documents: `docs/project-guide/processes-and-checks.md:11` and `:47`, `docs/project-guide/stage-environment.md:274`, `docs/project-guide/watching.md:264`, `docs/project-guide/costs.md:14` and `:17`, and `docs/operator-guide.md:833`. So the criterion still describes what the reader must know, and the documenter can write from it as it stands.
   - Interface: it states no rule, so there is no failing side to test.
   - Work item hygiene: the coder's entry gives the main choice (leave the documents to the documenter) and what was rejected (editing them in the doing stage). The Description matches what was built.

   Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
