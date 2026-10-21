---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-21T08:59:47.874696Z'
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
