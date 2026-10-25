---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 457
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-25T21:10:26.584942Z'
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
