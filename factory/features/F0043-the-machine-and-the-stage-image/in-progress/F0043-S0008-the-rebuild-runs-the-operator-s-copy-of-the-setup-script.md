---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 438
comments_read: []
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T08:42:10.964504Z'
  stage: intake
  run: 3d5a0759a86148649717204fc0952fe2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T08:42:30.916983Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T08:46:01.693831Z'
  stage: tests
  run: 9924d52cf2364bb1984cf6fbf7f00fd1
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T08:46:22.040078Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T08:50:00.970208Z'
  stage: doing
  run: cb1138f658ed43a087de0d667daa29d9
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T08:50:21.657228Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T08:50:53.204458Z'
  stage: review
  run: c0b950ad4b1246afa48c2daf653288a0
---

# The rebuild after a merge runs the operator's own copy of the setup script

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

S0003 closed every path from the user `factory` to root that the reviewers found in `vm/setup.sh`. Each fix rests on one rule: root acts on nothing that `factory` can change without the operator seeing it. That is why every file under `/srv/factory/<instance>` is written as `factory`, links at `state`, `repo` and `/home/factory/.secrets` are refused, and the unit and the credential helper are installed from the checkout only in the run that cloned it or when the installed file is missing (the human's answers in S0003's journal, entries 26, 37, 49 and 60). But the operator guide's *The rebuild after a merge* tells the operator to run `sudo sh /srv/factory/vm/factory/vm/setup.sh ...`. That executes, as root, a script inside the checkout `factory` owns and can write, so whatever that file holds at that moment runs as root. *On GCP, step by step*, step 6, already does it the safe way: the operator copies `vm/setup.sh` from their own checkout of the ref. This story makes the rebuild do the same. The operator takes `vm/setup.sh` from their own checkout of the ref the instance runs, copies it to the VM as in step 6 (`gcloud compute scp --tunnel-through-iap`), and runs that copy as root. The section says why, in one sentence. What stays: the rebuild's other steps (the pull, `uv sync`, `podman build` and the renewed `image-id`, all as `factory`), `vm/setup.sh` itself, the code, and every other section.

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
3. intake: accepted
   Interface: "None" is right for a docs-only story. It names no module or signature because nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes. It names the documents the documenter changes: `docs/operator-guide.md`, and one sentence in `docs/decisions.md`.
   Criteria: Each criterion can be checked by one test function or smoke command with no further decisions. Criterion 1 is a scope statement (nothing in the code areas changes). Criterion 2 is `make check`. Criterion 3 has three docs clauses: the rebuild section runs the setup script from the operator's own copy (`sudo sh setup.sh`) and has no root command that runs a file under `/srv/factory/<instance>/factory`; the decision entry gains one sentence; `make documents` ends with `documents ok`. The Interface states no rules, so there is no failing side to cover. I read the current text. `docs/operator-guide.md` line 712 holds the unsafe `sudo sh /srv/factory/vm/factory/vm/setup.sh`. Step 6 of *On GCP, step by step* (lines 594 to 603) already uses the `gcloud compute scp` plus `sudo sh setup.sh` form. The decision entry `## The factory runs on the host, and the stage image carries the tools alone` exists at line 1039. The "one sentence why" is not checked by a smoke command. The docs reviewer judges it from the criterion text.
   Smoke test: All three commands can be run. The awk/grep pair uses the real heading `### The rebuild after a merge`. The first expects `0`, and it matches today's line 712, so it fails before the change and passes after. The second expects a count of at least 1. The third runs `make documents` and expects `documents ok` as the last line. No pytest command is involved, so the `-q` rule does not apply.
   Architecture: Docs only. No layer is touched, and the root-acts-only-on-what-`factory`-cannot-change rule from F0043-S0003 is the one this story applies.
   Scope: Within F0043. Its scope covers the operator guide's chapter and the decision-log entry of the machine. Nothing in its "Out of scope" is touched. The Description leaves "how the operator obtains a trusted copy" to the human before the story starts. The human started the story, and criterion 3 names the method (a copy from their own checkout of the ref, as in step 6), so I take that as settled and ask nothing.
4. factory: started tests as vm.
5. tester: No tests written. This story only changes the docs. Its Interface is "None" and says no test changes, and criterion 3 says no test checks the documents.
   criterion 1: no test. It limits the story's scope: as the tester, I changed nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`, and the working tree is clean.
   criterion 2: no new test. `make check` covers it, run by the factory and by the coder.
   criterion 3: no test. The smoke test and `make documents` check it, as the criterion says.
   Files created: none. Modules the test run could not import: none. I did not run `make test` because there are no new tests that should fail. `make lint` is green.
   Open: nothing for the coder to implement. The documenter writes `docs/operator-guide.md` and the one sentence in `docs/decisions.md`. The coder's entry should also say that nothing under the listed folders changed.

   `lint`: lint: green (0.2 s)
   `test`: test: green (194.8 s)
6. factory: started doing as vm.
7. coder: I built nothing, so there are no paths. This story only changes the docs. The Interface is "None", the tester wrote no tests, and no test fails, so there is nothing for the coder to implement.
   criterion 1: I changed nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`. The working tree is clean (`git status --short` is empty).
   criterion 2: `make check` is green (`test: green (194.2 s)`, `check: green`).
   criterion 3: this is the documenter's. It changes `docs/operator-guide.md` (*The rebuild after a merge*) and adds one sentence to the decision entry `## The factory runs on the host, and the stage image carries the tools alone` in `docs/decisions.md`.
   Main choice: I left the docs alone, because CLAUDE.md says the documenter writes them and the coder does not. I rejected editing the operator guide here: that would take over the documenter's work.
   Refactor: there is no diff, so nothing needed changing.
   Description: the journal did not change the meaning of the task.
   Noticed but not touched: nothing.

   `check`: check: green (not run again: passed on tree 63d480b4dec3 at 2026-10-25T08:00:52Z)
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as vm.
9. reviewer: no findings

   I reviewed `git diff main...HEAD -- . ':!factory'`, and it is empty. The branch changes only the work item and its `.costs.jsonl` sidecar (`git diff --name-status main...HEAD`).
   - Group 1, acceptance criteria. Criterion 1 holds: nothing changes under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`, and the tester (entry 5) and the coder (entry 7) each say so. Criterion 2 holds: the coder's entry records `check: green`. Criterion 3 is the documenter's and is checked by the smoke test and `make documents`, so it needs no test. The Interface states no rules, so there is no failing side or limit to test.
   - Groups 2 to 4 (architecture, security, quality): there is no code or test in the diff to judge. The coder's record shows `duplicates: 11 new`, but this diff changes nothing under `src/factory`, so none of those findings come from this story.
   - Group 5, work item hygiene: the coder's entry explains the main choice (it leaves the documents to the documenter) and what it rejected. Criterion 3 still says exactly what the documenter must write.

   description corrected: "The operator takes `vm/setup.sh` from their own checkout of the ref the instance runs, or from the reviewed merge, copies it to the VM, and runs that copy as root. ... How the operator obtains a trusted copy is the human's to refine before the story starts. The acceptance report lists the options (its check 6)." -> "The operator takes `vm/setup.sh` from their own checkout of the ref the instance runs, copies it to the VM as in step 6 (`gcloud compute scp --tunnel-through-iap`), and runs that copy as root." Criterion 3 already settles the method (a copy from the operator's own checkout of the ref, as in step 6), and intake took it as settled in entry 3. Nothing else in the work item changed.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
