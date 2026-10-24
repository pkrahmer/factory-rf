---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 423
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T21:52:56.519460Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T21:52:56.525084Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T21:53:14.990447Z'
  stage: intake
  run: 8f2ef02b451d408484707bcf298e0347
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T21:53:35.564888Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T21:54:58.232201Z'
  stage: tests
  run: b0eb58c3995b4769b2d69350dbd2eb3f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T21:55:18.592554Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T21:58:06.598068Z'
  stage: doing
  run: 8834f426cd0e49ce9cc690dd696ac384
---

# The documents describe the stage environment

## Description

Every story of this feature left its part in the documents through its docs criterion: the new guide file `docs/project-guide/stage-environment.md` grew section by section, the operator guide gained the settings and the preflight items of a `container` instance, the decision log its entry, the write-guard guide its sentence on the undo. This story is the sweep at the end, as the brief's requirement 10 asks for: the documenter reads the four documents and the guide file against the code as it is after S0011 and makes them whole and true in one pass: the guide file has the sections in the order of the cycle, with the settings and the preflight at the end; the operator guide's sections say the same as the code; the decision entry names the date, the design, what the take keeps from the undo and what F0044 will remove; and `README.md`, written for the newcomer, says in one paragraph that the factory runs in two stage environments. No code and no test changes; `make documents` passes. What stays: every sentence that is already true.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template or an agent file. The documenter changes `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`, as the docs criterion says. No test reads the documents: `make check` runs at `doing`, before the documenter, and its `not_read` in `factory/pipeline.yml` leaves out `README.md` and `docs/*.md`; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter reads the whole guide file and the operator guide's sections *Configuration*, *The agent runtime*, *The preflight's items*, *The factory log* and *A stall: the stall note* against the code after S0011, correcting any sentence that is no longer true (the inline environment's items and chain stay as they are: F0044 removes them, not this story), and makes the following true; the smoke test and `make documents` check them, no test does:
   - `docs/project-guide/stage-environment.md` has exactly these `##` sections, in this order: *The cycle*, *The snapshots*, *The container runs*, *The fakes*, *The ZFS adapter*, *The podman adapter*, *The stage environment*, *The container environment*, *The sync command*, *The agent's container*, *The take*, *The checks*, *The settings and the wiring*, *The preflight*; *The cycle* is new: the steps of a stage (`planning/v1.2-plan.md`, "The cycle of a stage") as one numbered list, each step one line naming the section that describes it, without repeating *The container environment*'s details, and that under `inline` `prepare` does nothing; *The sync command* is today's subsection of *The stage environment*, raised to a section with its text; its first line is a `#` title and its second non-blank line a sentence that names what it covers; and it names the words `inline` and `container`, `FACTORY_STAGE_ENVIRONMENT`, `/work`, `@base`, `TakeReport`, `stage_environment_of` and the timing line `stage environment: reset` at least once each.
   - `docs/project-guide/README.md`, *The files*, has one bullet for `stage-environment.md` that names every module the file describes: `factory.application.snapshots`, `factory.application.containers`, `factory.application.stage_environment`, `factory.application.take`, `factory.domain.containers`, `factory.adapters.fake_snapshots`, `factory.adapters.fake_containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.podman_runs`, `factory.adapters.printed_output`, and its fourteen section names; and the bullet of `write-guard.md` says that the undo is the inline environment's take.
   - `docs/operator-guide.md` has, in *Configuration*, one table row for each of `FACTORY_STAGE_ENVIRONMENT`, `FACTORY_DATASET`, `FACTORY_WORKSPACE`, `FACTORY_STAGE_IMAGE`, `FACTORY_PODMAN` and `FACTORY_ZFS`; in *The preflight's items*, one table row for each of `podman`, `zfs`, `dataset` and `stage-image`; in *The factory log*, the line `stage environment: reset`; and no sentence that says the contract is three targets.
   - `docs/project-guide/write-guard.md`, *The undo*: the sentence "`StallService` still calls the undo itself." says instead that a stall's undo is the inline environment's take too (S0013); nothing else in the file changes.
   - `docs/decisions.md` has the section *One snapshot instead of many layers*, which names `2026-10-24`, `planning/v1.2-plan.md`, `StageEnvironment`, `InlineEnvironment`, `ContainerEnvironment`, the refusal rule (`refusal`), `restore_state_and_journal` and `F0044`; and `README.md` names `FACTORY_STAGE_ENVIRONMENT` once in a paragraph for the newcomer.
   - `README.md` names `FACTORY_STAGE_ENVIRONMENT` once, in one paragraph for the newcomer: an instance runs its stages `inline` (in its own container, v1.1's way) or in a `container` environment (throwaway containers on a ZFS dataset, v1.2's way, set by `FACTORY_STAGE_ENVIRONMENT`), pointing to the operator guide.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c '^## ' docs/project-guide/stage-environment.md; grep -c '^- `stage-environment.md`:' docs/project-guide/README.md; grep -c 'three targets' docs/operator-guide.md docs/project-guide/processes-and-checks.md || true
```
Expect: four lines, `14`, `1`, `docs/operator-guide.md:0`, `docs/project-guide/processes-and-checks.md:0`

```bash
grep -cE '^\| `(FACTORY_STAGE_ENVIRONMENT|FACTORY_DATASET|FACTORY_WORKSPACE|FACTORY_STAGE_IMAGE|FACTORY_PODMAN|FACTORY_ZFS)` \|' docs/operator-guide.md; grep -cE '^\| `(podman|zfs|dataset|stage-image)` \|' docs/operator-guide.md; grep -c '^## One snapshot instead of many layers' docs/decisions.md; grep -c 'FACTORY_STAGE_ENVIRONMENT' README.md
```
Expect: four lines, `6`, `4`, `1`, `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is concrete and right for a documents-only sweep. It names the six files the documenter changes (`README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/write-guard.md`, `docs/decisions.md`) and says nothing under `src/`, tests, image, template or agents changes. It states no behaviour or rule that would need a criterion of its own.
   - Criteria: criterion 1 (nothing outside the docs changes), 2 (`make check` stays green) and 3 (docs) are each checkable. Criterion 3 splits into bullets that are each checkable by grep or by `make documents`: the fourteen `##` sections in order, the one bullet in the guide index, the six settings rows, the four preflight rows, the log line, no "three targets" sentence, the one-sentence change in the write-guard guide, the decision entry with its named terms, and one `FACTORY_STAGE_ENVIRONMENT` paragraph in the README. Every rule has both its present and absent side (for example "no sentence that says the contract is three targets", "exactly these sections"). No Interface comment states a behaviour without a criterion. No test reads the documents; the Interface says so and the smoke test and `make documents` are the check, which suits a documenter-only story.
   - Smoke test: all three blocks are runnable `grep` or `make documents` commands. Each `Expect:` line is checkable: the counts `14`, `1`, `0`, `0`; `6`, `4`, `1`, `1`; and `documents ok`. No pytest command is involved, so there is no `-q` problem. One small gap, not a blocker: the smoke test also greps `docs/project-guide/processes-and-checks.md` for "three targets", while the criterion names only the operator guide. The expectation still reads true either way.
   - Architecture: nothing under `src/` changes, so the four layers are untouched. The documents involved match the Docs section of `CLAUDE.md`, and the documenter's write paths are `README.md` and `docs/*`. The story does not touch `planning/` or `docs/runs/`.
   - Scope: this is the sweep that the feature's Stories list and Scope ("The documents ... S0012 is the sweep") name. It changes nothing in the feature's "Out of scope": the inline environment's items and chain stay, since F0044 removes them. It changes no test another story wrote.
4. factory: started tests as self.
5. tester: No tests written; nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changed in this stage (criterion 1).
   - criterion 1: no test. The criterion says nothing outside the docs changes. This entry is the tester's statement that it holds: `git status` shows only the factory's `.costs.jsonl` sidecar.
   - criterion 2: no test. `make check` stays green; the factory runs it as the gate.
   - criterion 3 (docs): no test. The Interface says no test reads the documents, and the smoke test and `make documents` check them.
   Files created: none. Modules the test runner could not import: none, because no new tests exist, so this branch has no red tests for the coder. I did not run `make test`: there is nothing new that could fail. `make lint` is green.

   `lint`: lint: green (0.6 s)
   `test`: test: green (65.2 s)
6. factory: started doing as self.
7. coder: No code written. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changed in this stage (criterion 1).
   - What I built: nothing. The Interface says "None": nothing changes under `src/factory/` or in any test. The tester wrote no tests, so no test was failing for me to fix. The documenter will make the docs criterion true: the six files `README.md`, `docs/operator-guide.md`, `docs/project-guide/README.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`. The coder does not write those (CLAUDE.md, *Docs*).
   - Main choice: hand forward with an empty diff. Alternative rejected: starting on the documents here. They are outside the coder's job, and the docs stage owns them.
   - Refactor: no diff to refactor.
   - The journal did not change what the task means, so the Description stays as it is.
   - Noticed but did not touch: as intake noted, the smoke test also greps `docs/project-guide/processes-and-checks.md` for "three targets", but criterion 3 names only the operator guide. The documenter should check both files.
   - `make check`: green (`test: green (66.8 s)`, `check: green`, total coverage 99.19 %).

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
