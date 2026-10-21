---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 401
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T09:02:23.932971Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T08:59:47.868243Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T08:59:47.874696Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T09:00:09.621742Z'
  stage: intake
  run: e8e1cc478b21483e8b899ee44102d0f7
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T09:00:30.623360Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T09:02:02.690906Z'
  stage: tests
  run: 355c3125b6e747849d97d34086184aed
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T09:02:23.932971Z'
  stage: doing
---

# The operator guide names no planning code, internal class or dated observation

<!-- proposed by feature acceptance of 2026-10-21; refine before starting -->

## Description

After F0038 the operator guide (`docs/operator-guide.md`) still holds three kinds of text that the feature took out everywhere else, none of them listed in the documentation review of 2026-10-20 because they came later or were missed. In *The machine's image*, "Nothing in it floats (R29):" cites a requirement number that `CLAUDE.md` does not name; only the decision log's header sentence says where R1 to R34 come from, and the operator guide does not point there. In *The project commands run as `agent`*, written by F0040-S0002 after the review, "A seal that does not hold is the same `RepositoryUnsealed` error as after an agent run." names a class the operator never reads: what the operator sees is that the tick ends and the next iteration clones the checkout again, with the line `cloning the checkout again: <reason>` in the factory log (*The checkout is cloned again when it is missing or its `.git` is not the factory's alone*). And three parentheticals keep the date or the occasion of a first observation, where the guide states the current rule: "(seen at the first start of 2026-10-17 under Docker Desktop and Podman)" in the table of checks on a running instance, "(seen at the first start in PowerShell)" in *Podman: the commands*, and "(tested on 2026-10-17)" in *Podman: the restart*; F0038-S0006's documenter noted the first. This story removes those five passages for the operator and changes no other passage. The dated parentheticals are the third criterion's last bullet; when refining, the human may strike that bullet if the occasions should stay as evidence.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, and no other file; no other passage changes:
   - *The machine's image*: "Nothing in it floats (R29):" becomes "Nothing in it floats:". The guide then holds no `(R` followed by a number and `)`.
   - *The project commands run as `agent`*: "A seal that does not hold is the same `RepositoryUnsealed` error as after an agent run." becomes "A seal that does not hold ends the tick, as after an agent run, and the next iteration clones the checkout again with the line `cloning the checkout again: <reason>` (see \"The checkout is cloned again when it is missing or its `.git` is not the factory's alone\")." The guide then names `RepositoryUnsealed` nowhere, and names no class in backticks other than `SettingsInvalid`, `CannotHandle`, `PushFailed` and `HostingServiceError`.
   - The three parentheticals " (seen at the first start of 2026-10-17 under Docker Desktop and Podman)", " (seen at the first start in PowerShell)" and " (tested on 2026-10-17)" are removed with their leading space; the sentences around them stay as they are.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E '\(R[0-9]+\)|RepositoryUnsealed|seen at the first start|tested on 2026-10-17' docs/operator-guide.md || true
grep -c -F -e 'Nothing in it floats: the base image' -e 'A seal that does not hold ends the tick, as after an agent run, and the next iteration clones the checkout again' docs/operator-guide.md
grep -o -E '`[A-Z][a-z]+[A-Z][A-Za-z]+`' docs/operator-guide.md | sort -u | tr '\n' ' '; echo
```
Expect: three lines: `0`; `2`; and `` `CannotHandle` `HostingServiceError` `PushFailed` `SettingsInvalid` `` followed by a space (no planning code, internal class or dated first observation is left; the two replaced sentences are there; only the four kept error names remain)

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
   - Interface: "None" is right for a docs-only story. Nothing under `src/` changes, and the documenter edits only `docs/operator-guide.md`.
   - Criteria: each is checkable. I grepped the guide, and all five passages exist as quoted: "(R29)" at line 374, `RepositoryUnsealed` at line 475, "seen at the first start" at lines 275 and 575, and "tested on 2026-10-17" at line 585. The rules have a failing side as well as a passing one. The guide must hold no `(R<n>)`, no `RepositoryUnsealed` and no class in backticks beyond the four kept. The replacement sentences must be present. The target heading "The checkout is cloned again..." exists at line 104. The three parentheticals are removed with their leading space.
   - Smoke test: the commands are runnable. The first grep uses `|| true`, so the count `0` still prints. The class-name grep currently lists the four kept names plus `RepositoryUnsealed`, so after the edit it should list only the four. The pytest `-q` trap does not apply, because no command runs pytest. `make documents` ends with `documents ok`.
   - Architecture: the change is docs only, in the documenter's write path, and touches no layer.
   - Scope: it fits feature S0007's intent (no class names in the guide, keeping the four error names). It touches no Out-of-scope item. The human's bullet in the Description about the dated parentheticals is already in the criteria, so I took it as written.
4. factory: started tests as self.
5. tester: No tests written: this story changes only documentation, and nothing under `tests/` changes.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test. The criterion itself forbids changes under `tests/`, and the tester stage changed nothing there.
   - criterion 2 (`make check` stays green): no test. The factory's checks are what verify it.
   - criterion 3 (docs: the five passages in `docs/operator-guide.md`, `make documents` ends with `documents ok`): no test. It is the documenter's work, and the story's smoke test and the docs stage's `make documents` check verify it.
   Files created: none. Modules the test run could not import: none, since no test was added.
   I did not run `make test`: with no new tests, nothing could fail for the right reason, so the branch carries no red tests. `make lint` is green. The coder has nothing to implement under `src/`. Per criterion 1, the coder's entry should also say that nothing changes under the listed folders.

   `lint`: lint: green (0.7 s)
   `test`: test: green (67.0 s)
6. factory: started doing as self.
