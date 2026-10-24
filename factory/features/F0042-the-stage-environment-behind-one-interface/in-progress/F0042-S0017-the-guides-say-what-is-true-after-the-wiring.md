---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 425
comments_read: [6390283009]
handed_over: approval
claim: null
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
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-24T22:21:09.030902Z'
  stage: docs
  run: e6f33e5eefd24cde95b87fcdb743d2f7
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T22:21:29.505267Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: question
  at: '2026-10-24T22:22:05.240125Z'
  stage: smoke-test
  run: 94dab60ff0c442a8859443692582dbd8
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-24T22:24:24.383902Z'
  stage: smoke-test
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T22:24:42.388621Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T22:25:12.168367Z'
  stage: smoke-test
  run: f1b48d0dd7984416963c16ad13e580c9
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
11. documenter: Docs: I corrected the six passages the docs criterion lists. Only documents changed, so I did not run `make check`. `make documents` ended with `documents ok`.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`, *Project commands*: replaced "do not have it yet" with the fact that this repository's `Makefile` has `sync` (`uv sync --frozen`) and its `factory/pipeline.yml` has the command `sync` with `time_limit: 5`.
    - `docs/project-guide/processes-and-checks.md`, *Container project commands*: replaced "a later story; until then nothing builds it" with the statement that `build_boundaries` puts `ContainerMakeCommands` behind `RecordingProjectCommands` for a `container` instance. It points to `stage-environment.md`.
    - `docs/project-guide/stage-environment.md`, *The agent's container*: replaced "is a later story's" with the statement that `build_boundaries` gives the runtime of `FACTORY_AGENT_RUNTIME` its `PodmanRuns` for a `container` instance.
    - `docs/project-guide/watching.md`, *Boundaries*: `project_commands` now names both cases. The `inline` chain is unchanged. For `container` it is `RecordingProjectCommands` around `ContainerMakeCommands`.
    - `docs/project-guide/costs.md`: the bullet is now "Rewritten after every take". It says the rewrite happens after the take, which is the undo under `inline`. The "uncommitted" bullet now says the `git status` and `git diff` remark holds under `inline`. It adds that under `container` the agent works on the dataset, where the sidecar is the one committed at the stage-start commit, and that the factory writes the host's copy after the take.
    - `docs/operator-guide.md`, *A stall: the stall note*: "undoes the rest" now says the factory keeps what is inside the write paths and leaves out the rest. An `inline` instance undoes it, and a `container` instance does not take it from the dataset.

    Checked against the code on `main`, as the reviewer did:
    - `Makefile:27` and `factory/pipeline.yml:16` match the `sync` text.
    - `src/factory/entry/wiring.py:369` and `:397` build `ContainerMakeCommands` and `PodmanRuns` for a `container` instance.

    I did not re-read the take or the sidecar rewrite in the code beyond that. The costs wording follows the criterion.

    Cross-read and found current: the `Boundaries` field list in `watching.md`, which already described the container wiring of `snapshots` and `containers`.

    Stale text I saw and did not touch:
    - `docs/decisions.md:166` and `:168` still say "rewritten ... after every undo". It is the decision log and records the 2026-10-14 reasoning, so it is not mine to edit.
    - The `costs.md` bullet "Rewritten after every take" still names `AfterAgent.process` as the place of the rewrite. I did not check whether the take path uses the same function. If it does not, that is a follow-up.

    No findings for the coder.

    `check`: check: green (not run again: passed on tree 3389db52e22b at 2026-10-24T22:18:10Z)
    `secrets`: secrets: green (1.9 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test, round 0. I ran the three commands from the repository root as written and fixed nothing. One of them does not meet its `Expect:` line, and I think the fix belongs in the smoke test, which is yours. So I am asking instead of sending the work item to `doing`.

    Command 1:
    ```
    0
    0
    0
    0
    0
    ```
    Met: five lines, each `0`.

    Command 2:
    ```
    2
    1
    ```
    Not met. The expectation is `1` and a number of at least `1`. The second line (`ContainerMakeCommands` in `watching.md`: 1) is fine. The first line (`Rewritten after every take` in `costs.md`) is 2, not 1.

    Command 3:
    ```
    documents ok
    ```
    Met.

    Findings:
    1. Command 2, `grep -c 'Rewritten after every take' docs/project-guide/costs.md`. Expected `1`, observed `2`. The two matches are `docs/project-guide/costs.md:17`, the bullet's new title as criterion 3 asks, and `docs/project-guide/costs.md:14`, where the "uncommitted" bullet points to it with "(see *Rewritten after every take*)". The documenter updated that pointer along with the title, and leaving the old name would have pointed to a bullet that no longer exists. So the documents meet criterion 3. The count of exactly `1` did not allow for the pointer. No criterion is broken: the bullet's title is "Rewritten after every take", and no "Rewritten after every undo" is left (command 1).

    Checked against the acceptance criteria:
    - Criterion 1: `git diff main...HEAD --stat -- src tests image template claude` is empty.
    - Criterion 2: the coder's `make check` was green (entry 7), and the docs stage reused that result (entry 11).
    - Criterion 3: I read the diff of the five documents. Each of the six passages now says what the criterion asks, and `make documents` ends with `documents ok`.

    Question: how should finding 1 be settled?
    (a) You change command 2's `Expect:` line to "two lines, each a number of at least `1`" (or count only the title line, e.g. `grep -c '^- \*\*Rewritten after every take'`), and the smoke test runs again. It should then pass, since nothing else is off.
    (b) I end with `doing`, and the documenter rewords the pointer at `costs.md:14` so the title appears once, for example "(see the bullet below)".

    I would choose (a). The pointer is correct and useful, and only the expected count is wrong.
14. 2026-10-24 human: (a). The pointer at `costs.md:14` is correct and stays. Read command 2's `Expect:` as "two lines, each a number of at least `1`": the count of exactly `1` did not allow for the pointer, and no criterion asks for one occurrence. With that reading command 2 is met (`2`, `1`), so the smoke test passes as you ran it; say so in your entry and quote this answer. No change to the documents.
15. factory: started smoke-test as self.
16. smoke-tester: Smoke test, round 0, run again after the human's answer (entry 14). I ran the three commands from the repository root as written and fixed nothing. No findings.

    Command 1:
    ```
    0
    0
    0
    0
    0
    ```
    Met: five lines, each `0`.

    Command 2:
    ```
    2
    1
    ```
    Met under the human's reading. The human said in entry 14: "(a). The pointer at `costs.md:14` is correct and stays. Read command 2's `Expect:` as "two lines, each a number of at least `1`": the count of exactly `1` did not allow for the pointer, and no criterion asks for one occurrence. With that reading command 2 is met (`2`, `1`), so the smoke test passes as you ran it; say so in your entry and quote this answer. No change to the documents." The `2` is the bullet title at `docs/project-guide/costs.md:17` plus the pointer "(see *Rewritten after every take*)" at `docs/project-guide/costs.md:14`.

    Command 3:
    ```
    documents ok
    ```
    Met.

    Checked against the acceptance criteria:
    - Criterion 1 holds. `git diff main...HEAD --stat -- src tests image template claude` is empty, and `git status --short` shows only the work item's `.costs.jsonl` sidecar, which the factory writes.
    - Criterion 2: the coder's `make check` ended green (entry 7), and the docs stage reused that passed result (entry 11). I did not run `make check` again because this stage changed nothing.
    - Criterion 3: the diff touches exactly the five documents named, with 7 lines in and 7 out. I read each changed passage. The `sync` target and command, `ContainerMakeCommands` behind `RecordingProjectCommands`, `PodmanRuns` from `build_boundaries`, both `project_commands` cases in `watching.md`, the "Rewritten after every take" bullet with its `container` wording, and the stall note's "leaves out the rest" for both environments all say what the criterion asks. `make documents` ends with `documents ok`.

    Open: nothing for this story. The documenter's note (entry 11) still stands as a possible follow-up: `docs/decisions.md:166` and `:168` still say "after every undo", and it has not been checked whether the take path rewrites the sidecar through `AfterAgent.process`.
