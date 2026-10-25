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
  instance: vm
  stage: intake
  started_at: '2026-10-25T08:41:49.627998Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T08:41:49.622617Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T08:41:49.627998Z'
  stage: intake
---

# The rebuild after a merge runs the operator's own copy of the setup script

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

S0003 closed every path from the user `factory` to root that the reviewers found in `vm/setup.sh`. Each fix rests on one rule: root acts on nothing that `factory` can change without the operator seeing it. That is why every file under `/srv/factory/<instance>` is written as `factory`, links at `state`, `repo` and `/home/factory/.secrets` are refused, and the unit and the credential helper are installed from the checkout only in the run that cloned it or when the installed file is missing (the human's answers in S0003's journal, entries 26, 37, 49 and 60). But the operator guide's *The rebuild after a merge* tells the operator to run `sudo sh /srv/factory/vm/factory/vm/setup.sh ...`. That executes, as root, a script inside the checkout `factory` owns and can write, so whatever that file holds at that moment runs as root. *On GCP, step by step*, step 6, already does it the safe way: the operator copies `vm/setup.sh` from their own checkout of the ref. This story makes the rebuild do the same. The operator takes `vm/setup.sh` from their own checkout of the ref the instance runs, or from the reviewed merge, copies it to the VM, and runs that copy as root. The section says why, in one sentence. What stays: the rebuild's other steps (the pull, `uv sync`, `podman build` and the renewed `image-id`, all as `factory`), `vm/setup.sh` itself, the code, and every other section. How the operator obtains a trusted copy is the human's to refine before the story starts. The acceptance report lists the options (its check 6).

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md`, plus one sentence in `docs/decisions.md` as the docs criterion says. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the smoke test and `make documents` check these, and no test does:
   - In `docs/operator-guide.md`, *The rebuild after a merge* (chapter `## The machine`) runs the setup script from a copy the operator made from their own checkout of the ref, as in *On GCP, step by step*, step 6 (`gcloud compute scp --tunnel-through-iap vm/setup.sh factory-vm:`, then `sudo sh setup.sh ...` with the arguments of the first run). It contains no command that runs a file under `/srv/factory/<instance>/factory` as root. It says in one sentence why: root runs nothing from a checkout `factory` can write. The rest of the section is unchanged: the steps as `factory`, the restart, and the removal of a differing unit or helper.
   - In `docs/decisions.md`, the entry `## The factory runs on the host, and the stage image carries the tools alone` gains one sentence: root runs no file of the factory's checkout, and the operator runs the setup script from their own copy. No other entry changes.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
awk '/^### The rebuild after a merge$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -E 'sudo sh /srv/factory/[^ ]*/factory/vm/setup\.sh'
```
Expect: `0`

```bash
awk '/^### The rebuild after a merge$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -F 'sudo sh setup.sh'
```
Expect: a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
