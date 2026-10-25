---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 457
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-25T21:14:51.138621Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T21:09:48.845045Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T21:09:48.852151Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T21:10:06.469080Z'
  stage: intake
  run: 48eca49b303c4235b3161d4dd60c316a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T21:10:26.584942Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T21:12:45.149287Z'
  stage: tests
  run: 1de54f9e3b1e4cdaa3b179605e93c1bc
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T21:13:05.490976Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T21:14:30.381119Z'
  stage: doing
  run: 9bd4166690aa45e9ada1937d642a6208
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T21:14:51.138621Z'
  stage: review
---

# The restore stop's repair names the one user

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

The operator guide's paragraph on the stop `checkout_restore_failed` (*The stops of the tick*) still describes the long-lived container that F0044 removed. It says "When an agent run left the path, the stage that ran ends without a result", but since F0044-S0008 no agent runs in the factory's checkout: the agent works on the dataset, and only the take writes the checkout, as `factory`. It also says "Repair with `chmod -R g+w <path>` as root". That is the repair of the second user's group `factory-work`, which F0044-S0005 removed. S0006's documenter noticed the paragraph and left it, and S0011's sweep searched only for names, so it was missed. An operator who meets this stop on the VM is sent after a group and an agent run that no longer exist. This story makes the paragraph true of the machine of v1.2: what can still leave a path the factory cannot remove in its checkout (a file made there by hand as root or as another user), the repair (remove that path, as root when `factory` cannot), and what the next tick does once it is gone. Nothing else changes. The restore, the stop and the crash cap behave as they do today, and the other paragraphs of *The stops of the tick* stay.

## Interface

None: nothing changes under `src/factory/`, in any test, or under `vm/`, `template/` or `claude/`. The documenter changes one paragraph of `docs/operator-guide.md`, and the passages in `docs/project-guide/` named in the docs criterion if they say the same thing. No test reads the documents; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The stops of the tick*: the paragraph that begins with `` `checkout_restore_failed` comes`` names no `chmod`, no `g+w` and no group. It no longer says that an agent run left the path, and it says that on the VM only the factory's own git and the take write the checkout. It gives the repair as the removal of the path git's message names, as `factory` (`sudo -iu factory`) or, when `factory` cannot remove it, as root. It says that the next tick clears the stop once the restore succeeds. It states the crash cap only if the code still records a crash for this case; the documenter checks `factory.application.tick` and `factory.application.recovery`. `docs/project-guide/watching.md`, the step **Restore**: the documenter checks it for the same two claims and corrects them if they are present. `README.md` and `docs/decisions.md`: none. `make documents` ends with `documents ok`.

## Smoke test

```bash
awk '/^`checkout_restore_failed` comes/' docs/operator-guide.md | grep -cE 'chmod|g\+w|agent run left' || true
```
Expect: `0`

```bash
awk '/^`checkout_restore_failed` comes/' docs/operator-guide.md | grep -c 'sudo -iu factory'
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is right for a documents-only story. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes, and the one paragraph and the `watching.md` step it names exist (`docs/operator-guide.md:1070`, `docs/project-guide/watching.md:79-80`).
   Criteria: criterion 1 (nothing outside the docs changes) and criterion 2 (`make check` green) are checkable. The docs criterion is checkable by the smoke test: no `chmod`, `g+w` or `agent run left`, and `sudo -iu factory` present. The crash-cap clause is conditional on the code. The documenter reads `factory.application.tick` and `factory.application.recovery` to decide it. The Interface states no behaviour or rule of code, so there is no failing side to test.
   Smoke test: all three commands are runnable. The paragraph is a single line starting with `` `checkout_restore_failed` comes``, so the `awk` pattern selects it. The first command's `|| true` keeps the exit code 0 when grep counts 0. The third runs `factory.entry.check_documents`. Each `Expect:` is a concrete output (`0`, `1`, `documents ok`). No pytest command is used, so there is no `-q` issue.
   Architecture: the change is to documents only, which the documenter owns. `README.md` and `docs/decisions.md` stay untouched, as the criterion says.
   Scope: it stays within F0044 as acceptance story A0001 proposed it (decision 42). It does not touch the restore, the stop or the crash cap, which are in the feature's "stay as they are" list.
4. factory: started tests as self.
5. tester: I wrote no tests, and nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changed. The Interface is "None": the story changes documents only and no test reads them.
   criterion 1 (nothing under src/, tests/, vm/, template/ or claude/ changes): no test. The entry states it, and `git status` shows no change in those paths.
   criterion 2 (`make check` stays green): no test. The factory's checks cover it.
   criterion 3 (docs): no test. The smoke test and `make documents` check it, as the Interface says.
   Files created: none. Modules the test runner could not import: none. Because there are no new tests, the branch has no red tests: `make test` ended `test: green (61.2 s)` (99.55 % coverage) and `make lint` ended `lint: green (0.2 s)`. The coder has no test to make pass and only confirms criterion 1 in their own entry.

   `lint`: lint: green (0.2 s)
   `test`: test: green (61.6 s)
6. factory: started doing as self.
7. coder: I built nothing, and nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changed. The Interface is "None": this story only changes documents, and the documenter makes that change.
   - `make test`: no tests were failing. The tester wrote none because no test reads the documents.
   - `make check`: green. It ended with `test: green (61.7 s)` and `check: green`, coverage 99.55 %.
   - `git status --short`: the only change is the factory's own `.costs.jsonl` sidecar of this work item. My diff is empty, so there was nothing to refactor.

   Main choice: leave the code and the documents alone. The alternative I rejected was to correct the operator guide paragraph on `checkout_restore_failed` myself. `docs/` belongs to the documenter, and CLAUDE.md says the coder does not write it.

   The journal did not change the meaning of the task, so the Description stands.

   Noticed but not touched: whether a crash is still recorded for this stop has to be read from `factory.application.tick` and `factory.application.recovery`. That check is part of the docs criterion and belongs to the documenter.

   `check`: check: green (not run again: passed on tree 92c6af88fac5 at 2026-10-25T21:03:03Z)
   `duplicates`: duplicates: 8 new, 35 known, 3 gone
8. factory: started review as self.
