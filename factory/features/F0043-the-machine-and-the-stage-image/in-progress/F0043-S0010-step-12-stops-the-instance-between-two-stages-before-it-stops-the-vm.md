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
  started_at: '2026-10-25T09:41:36.601707Z'
  lease_duration: 60
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
