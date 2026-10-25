---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 442
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T09:41:36.596123Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T09:41:36.601707Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T09:41:54.209635Z'
  stage: intake
  run: 5b8e57a1742c42df8ea14eae8fa4a4cc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T09:42:14.581626Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T09:45:48.302626Z'
  stage: tests
  run: 6fb4f020c78a4651968f96c8360f2f1d
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T09:46:08.605623Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T09:49:54.398283Z'
  stage: doing
  run: 86b3319a43ae4273a3f6c92bd01c3ea4
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T09:50:14.708210Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T09:50:32.021075Z'
  stage: review
  run: 436a4318347e459cbba7edb2ebfeb17b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T09:50:52.163955Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-25T09:51:18.053861Z'
  stage: docs
  run: 81a9c89a0d504b889222647307842fdb
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T09:51:38.450811Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T09:52:07.887191Z'
  stage: smoke-test
  run: dbe1bbf9de614ceeaa07ac25866056c0
---

# Step 12 stops the instance between two stages before it stops the VM

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

Step 12 of *On GCP, step by step* (chapter `## The machine` of `docs/operator-guide.md`) tells the operator to stop the VM when it is not used, with `gcloud compute instances stop factory-vm --zone=europe-west3-a`, and says nothing about a stage that may be running. A VM stop shuts the VM down, and systemd then stops `factory@vm` the same way `systemctl stop` does: the factory's stop flag is set, the tick runs on, and systemd kills the process after its default stop timeout of 90 seconds (`vm/factory.service` sets no `TimeoutStopSec`). At the next start the factory finds its own claim and counts the stage as a crash, and `crash_cap` is 2. F0043-S0009 fixed this for *The rebuild after a merge*, which now waits until `factory-watch` shows no work item held by `vm` and then runs `sudo systemctl stop factory@vm`, but it changed no other section, so step 12 still leads straight into the same crash, and it is the step an operator follows every evening to save the machine's cost. This story rewrites step 12 only. Before the VM stop, it tells the operator to wait for no claim and stop the instance, as *The rebuild after a merge* does, and it says where each command runs. What stays: the cost sentence, the start with `gcloud compute instances start`, the sentence that the enabled service comes up with the VM (a `systemctl stop` does not disable it), every other section, `vm/factory.service` and the code. Whether the unit should let a stage finish on a stop (a `TimeoutStopSec` beyond the lease) is still the human's open question (F0043-A0002 and F0043-A0003, check 6), and this story does not decide it.

## Interface

None. Nothing changes under `src/factory/`, in any test, or under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md` only, in step 12 of `### On GCP, step by step`. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/operator-guide.md`, step 12 of `### On GCP, step by step` in chapter `## The machine`; the smoke test and `make documents` check these, and no test does:
   - Before the VM stop, step 12 tells the operator to wait until `factory-watch` (run as in step 11) shows no work item held by `vm`, and then to run `sudo systemctl stop factory@vm` on the VM from their own account. One sentence says why, or points to *The rebuild after a merge* for it: a VM stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the next start counts the stage as a crash.
   - The line holding `sudo systemctl stop factory@vm` comes before the line holding `gcloud compute instances stop`. Step 12 holds no `systemctl restart`.
   - Each command is introduced by where it runs: `sudo systemctl stop factory@vm` on the VM from your own account, `gcloud compute instances stop` and `gcloud compute instances start` on your own computer. No code block of step 12 holds both a `gcloud` command and a `sudo` command.
   - The cost sentence ("A stopped VM costs only its disks and NAT"), the start with `gcloud compute instances start` and the sentence that the service is enabled and comes up with the VM stay. No other section of the guide changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
s=$(awk '/^### On GCP, step by step$/{g=1} g && /^12\. /{on=1} /^### On any Ubuntu 24.04 VM$/{on=0; g=0} on' docs/operator-guide.md); printf '%s\n' "$s" | grep -c -F 'sudo systemctl stop factory@vm'; printf '%s\n' "$s" | grep -c -F 'factory-watch'
```
Expect: two lines, each a number of at least `1`

```bash
s=$(awk '/^### On GCP, step by step$/{g=1} g && /^12\. /{on=1} /^### On any Ubuntu 24.04 VM$/{on=0; g=0} on' docs/operator-guide.md); printf '%s\n' "$s" | grep -c -F 'systemctl restart'; printf '%s\n' "$s" | grep -F -e 'systemctl stop factory@vm' -e 'gcloud compute instances stop' | head -n 1 | grep -c -F 'systemctl stop'
```
Expect: two lines: `0`, `1`

```bash
awk '/^### On GCP, step by step$/{g=1} g && /^12\. /{on=1} /^### On any Ubuntu 24.04 VM$/{on=0; g=0} on' docs/operator-guide.md | awk '/^ *```/{n++; if (n%2==0) {if (g && s) bad++; g=0; s=0}; next} n%2==1 && /gcloud /{g=1} n%2==1 && /^ *sudo /{s=1} END{print bad+0}'
```
Expect: `0`

```bash
awk '/^### On GCP, step by step$/{g=1} g && /^12\. /{on=1} /^### On any Ubuntu 24.04 VM$/{on=0; g=0} on' docs/operator-guide.md | grep -c -F 'gcloud compute instances start'
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
   Interface: "None" is correct for a documents-only story. It names the one file (`docs/operator-guide.md`) and the one place (step 12 of `### On GCP, step by step`). I found step 12 as a single line at `docs/operator-guide.md:648`, as the Description says. It has no `Interface` comment that states a behaviour, so nothing is missing a criterion.
   Criteria: each can be checked by a smoke test or by `make documents`, and the story says no test reads the documents. Criterion 1 (nothing changes outside the docs) is checkable by diff. Criterion 2 is `make check`. The docs criterion covers each clause of the Description: wait for no claim by `vm` with `factory-watch`, then `sudo systemctl stop factory@vm`, and the "why" sentence. It also covers the order of the two commands, no `systemctl restart`, where each command runs, and that the cost sentence, the start and the "enabled" sentence stay. The one clause no smoke test checks is the "why" sentence itself, which the reviewer reads. The rule "wait first, then stop" has its failing side in the order check (smoke test 2) and in the no-restart check.
   Smoke test: all five commands are runnable. The awk range runs from `12. ` to the `### On any Ubuntu 24.04 VM` heading, and both headings exist. Each `Expect:` line can be checked against the output. No command runs pytest, so the `-q` rule does not apply. `make documents` is a project target.
   Architecture: this changes only `docs/operator-guide.md`, which the documenter stage may write. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes.
   Scope: the story stays inside F0043's chapter "The machine". It leaves `vm/factory.service` and the `TimeoutStopSec` question to the human (F0043-A0002/A0003), and it is not in the feature's Out of scope.
4. factory: started tests as vm.
5. tester: No tests written. This story only changes documents. The Interface says nothing changes under `src/factory/` or in any test, and that no test reads the documents. The smoke test and `make documents` check the docs criterion.
   criterion 1 (nothing under src/, tests/, vm/, image/, template/ or claude/ changes): no test function; this stage changed nothing under any of those paths, and `git status` shows a clean working tree.
   criterion 2 (`make check` stays green): no test function; the factory's checks cover it. `make lint` ends `lint: green`.
   criterion 3 (docs, step 12 of `### On GCP, step by step`): no test function, because the criterion says no test checks it; the smoke test and `make documents` do.
   Files created: none. Modules the test run could not import: none, since no new tests exist. I did not run `make test` to look for red tests because there are none to see; the factory's `make test` after this stage should stay green. Nothing is open.

   `lint`: lint: green (0.2 s)
   `test`: test: green (194.7 s)
6. factory: started doing as vm.
7. coder: Built nothing; no paths changed. This story changes only documents. The Interface says nothing changes under `src/factory/`, in any test, or under `vm/`, `image/`, `template/` or `claude/`, and the tester wrote no tests, so there was no failing test to make pass.
   criterion 1 (nothing under src/, tests/, vm/, image/, template/ or claude/ changes): this stage changed no file; the working tree is clean.
   criterion 2 (`make check` stays green): I ran `make check` in the foreground on the unchanged branch and it ended `check: green` (test: green (196.3 s), coverage 99.20 %).
   criterion 3 (docs, step 12 of `### On GCP, step by step` in `docs/operator-guide.md`): the documenter writes this; the coder does not write `docs/` (CLAUDE.md, *Docs*).
   Main choice: I left `docs/operator-guide.md` to the docs stage. The alternative was to write the new step 12 here, and I rejected it because the coder does not write the docs and the criterion names the documenter.
   Refactor: there is no diff to refactor.
   The journal did not change the meaning of the task, so the Description stays as it is.
   Noticed but not touched: `vm/factory.service` still sets no `TimeoutStopSec`. Whether it should is the human's open question, and this story leaves it alone.

   `check`: check: green (not run again: passed on tree 63d480b4dec3 at 2026-10-25T08:00:52Z)
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as vm.
9. reviewer: no findings

   I reviewed `git diff main...HEAD -- . ':!factory'` and the work item. The diff outside `factory/` is empty. The only changed paths are the work item's own `.md` and its new `.costs.jsonl` sidecar.
   - Acceptance criteria: criterion 1 holds, because nothing changes under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`. The tester (entry 5) and the coder (entry 7) each say so. Criterion 2 holds: `make check` ended `check: green`, run by the coder on this tree (entry 7). Criterion 3 is the docs criterion. The documenter writes it next, and the smoke test and `make documents` check it. No test is called for, because the Interface is "None" and no test reads the documents.
   - Interface: it states no rule or limit, so no failing side is missing a test.
   - Architecture, security, quality: no code changed, so there is nothing to judge. The `duplicates: 11 new` record in entry 7 cannot come from this story, because nothing under `src/factory` changed.
   - Work item hygiene: the coder's entry gives the main decision (leave `docs/operator-guide.md` to the docs stage) and the alternative it rejected (writing step 12 itself). The Description still matches the story: a rewrite of step 12 only, still to be written. The docs criterion still says what the documenter must write: wait for no claim by `vm` with `factory-watch`, then `sudo systemctl stop factory@vm` on the VM. It also gives the reason (systemd's stop timeout of 90 seconds, then a crash at the next start), the order of the commands, where each command runs, no `systemctl restart`, and the cost, start and enabled sentences that stay.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` already holds.
10. factory: started docs as vm.
11. documenter: Files changed: `docs/operator-guide.md`, step 12 of `### On GCP, step by step`, and nothing else. Step 12 now tells the operator to wait until `factory-watch` (run as in step 11) shows no work item held by `vm`. Then it tells them to run `sudo systemctl stop factory@vm` on the VM from their own account. Only after that does it tell them to run `gcloud compute instances stop` on their own computer. One sentence gives the reason and points to *The rebuild after a merge*: a VM stop during a stage ends the factory after systemd's 90 s stop timeout, and the next start counts the stage as a crash. The cost sentence, the start with `gcloud compute instances start` and the "service is enabled and comes up with the VM" sentence stay. I added the instance and zone to the start command, and the reason that `systemctl stop` does not disable the service. The two commands are in separate code blocks, so no block holds both `gcloud` and `sudo`. Step 12 holds no `systemctl restart`.

    Checks I ran:
    - The smoke-test commands give 1 for `sudo systemctl stop factory@vm`, 0 for `systemctl restart`, the stop line first, and 0 mixed blocks.
    - I did not run the smoke test's `factory-watch` count or its `gcloud compute instances start` count.
    - `make documents` ends `documents ok`.
    - I did not run `make check`, because I changed only a document.

    Cross-read and found current: *The rebuild after a merge* (the same wait and stop; step 12 now agrees with it) and steps 11 and 6 of the same guide, which step 12 refers to. The diff outside `factory/` is empty, so no other document had anything to be stale against.

    Not touched: `vm/factory.service` still sets no `TimeoutStopSec`. That is the human's open question (F0043-A0002 and F0043-A0003), outside this story. No findings.

    `check`: check: green (not run again: passed on tree 63d480b4dec3 at 2026-10-25T08:00:52Z)
    `secrets`: secrets: green (1.0 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
13. smoke-tester: Ran the five `## Smoke test` commands from the repository root exactly as written, in order. All five met their `Expect:` line, and no criterion is contradicted. No findings.

    Command 1 (counts of `sudo systemctl stop factory@vm` and `factory-watch` in step 12). Expect: two lines, each at least `1`. Met.
    ```
    1
    1
    ```

    Command 2 (count of `systemctl restart`, and whether the stop line comes first). Expect: `0`, `1`. Met.
    ```
    0
    1
    ```

    Command 3 (code blocks in step 12 that hold both a `gcloud` and a `sudo` command). Expect: `0`. Met.
    ```
    0
    ```

    Command 4 (count of `gcloud compute instances start` in step 12). Expect: at least `1`. Met.
    ```
    1
    ```

    Command 5 (`make documents 2>&1 | tail -n 1`). Expect: `documents ok`. Met.
    ```
    documents ok
    ```

    Re-read against `## Acceptance criteria`:
    - Criterion 1: `git diff --stat main...HEAD` lists only `docs/operator-guide.md` and the work item's own `.md` and `.costs.jsonl`. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes. The tester (entry 5) and the coder (entry 7) each said so.
    - Criterion 2: I did not run `make check` myself. Entries 7 and 11 record `check: green`, and the factory runs the stage's checks.
    - Criterion 3: the diff to `docs/operator-guide.md` is one hunk, and it covers step 12 only. The step tells the operator to wait for no work item held by `vm` with `factory-watch` "as in step 11". Then they run `sudo systemctl stop factory@vm` "on the VM from your own account", and after that `gcloud compute instances stop` "on your own computer". One sentence gives the reason (systemd's 90-second stop timeout, then a crash at the next start) and points to *The rebuild after a merge*. The two commands sit in separate code blocks. The start is introduced as "on your own computer". The cost sentence, the start with `gcloud compute instances start` and the "service is enabled and comes up with it" sentence are still there. No other section changed.

    Open: nothing for this story. The `TimeoutStopSec` question for `vm/factory.service` is still the human's (F0043-A0002/A0003).
