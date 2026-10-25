---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 440
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-25T09:12:16.149174Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T09:11:36.023948Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T09:11:36.029572Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T09:11:56.176217Z'
  stage: intake
  run: fa6954e0c78047aeaa40af2225adbe35
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T09:12:16.149174Z'
  stage: tests
---

# The rebuild after a merge stops the instance between two stages and says where each command runs

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

The operator guide's *The rebuild after a merge* (chapter `## The machine`) has three gaps. First, it tells the operator to `git pull` and `uv sync` the factory's checkout while `factory@vm` is running, and only then to `systemctl restart factory@vm`. A running instance may be in the middle of a stage, because an agent run lasts up to its role's `time_limit` of 40 minutes. A stop then sets the factory's stop flag (`install_stop_handlers` in `factory.entry.run`), but the tick runs on. `vm/factory.service` sets no `TimeoutStopSec`, so systemd kills the process after its default 90 seconds. The restart then finds its own claim and treats the stage as a crash (the guide, "If the factory dies while a stage runs ..."), and `crash_cap` is 2. The night log shows the human stopping `factory@vm` "no claim" before every pull. The guide does not say to. Second, one code block mixes commands for two machines. `gcloud compute scp` and `gcloud compute ssh` run on the operator's own computer, while `sudo sh setup.sh` and `systemctl` run on the VM, and the section does not say which is which. The block before it ends on the VM with `exit`. Third, the section names only `gcloud`, so an operator of a VM outside GCP is not told how to copy the script. This story rewrites that one section in this order: wait until no work item is held by the instance (`factory-watch`, as in step 11), stop it, bring the checkout and the image up to date as `factory`, copy and run the operator's own `setup.sh`, and start the instance again. Each block is introduced by the machine and the user it runs as, and one sentence covers a VM outside GCP. What stays: the commands as `factory`, the copy from the operator's own checkout (S0008), the paragraph on a differing unit or helper, `vm/setup.sh`, `vm/factory.service` and the code. Whether the unit should let a stage finish on a stop (a `TimeoutStopSec` beyond the lease) is a change to `vm/factory.service`. This story does not make it. It is open for the human (F0043-A0002, check 6).

## Interface

None. Nothing changes under `src/factory/`, in any test, or under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md` only, in its section `### The rebuild after a merge`. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/operator-guide.md`, section `### The rebuild after a merge` of chapter `## The machine`; the smoke test and `make documents` check these, and no test does:
   - Before the pull, the section tells the operator to wait until `factory-watch` (run as in *On GCP, step by step*, step 11) shows no work item held by `vm`, and then to run `sudo systemctl stop factory@vm`. One sentence says why: a stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the restart counts the stage as a crash.
   - The line `sudo systemctl stop factory@vm` comes before the line holding `pull --ff-only`. The section ends the rebuild with `sudo systemctl start factory@vm` and holds no `systemctl restart factory@vm`.
   - Every code block of the section is introduced by a sentence that names where it runs: on your own computer (the two `gcloud compute` commands), on the VM as `factory` (the pull, `uv sync`, `podman build`, the new `image-id`), or on the VM from your own account (`sudo sh setup.sh ...`, `systemctl`). No block holds both a `gcloud` command and a `sudo` command.
   - One sentence says that on a VM outside GCP the operator copies `vm/setup.sh` from their own checkout by their own means, such as `scp`, as *On any Ubuntu 24.04 VM* does.
   - The copy from the operator's own checkout, the sentence "Root runs nothing from `/srv/factory/vm/factory`, ...", and the paragraph on a differing unit or helper stay. No other section of the guide changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
s=$(awk '/^### The rebuild after a merge$/{on=1; next} /^##/{on=0} on' docs/operator-guide.md); printf '%s\n' "$s" | grep -c -F 'sudo systemctl stop factory@vm'; printf '%s\n' "$s" | grep -c -F 'sudo systemctl start factory@vm'
```
Expect: two lines, each a number of at least `1`

```bash
s=$(awk '/^### The rebuild after a merge$/{on=1; next} /^##/{on=0} on' docs/operator-guide.md); printf '%s\n' "$s" | grep -c -F 'systemctl restart factory@vm'; printf '%s\n' "$s" | grep -F -e 'systemctl stop factory@vm' -e 'pull --ff-only' | head -n 1 | grep -c -F 'systemctl stop'
```
Expect: two lines: `0`, `1`

```bash
awk '/^### The rebuild after a merge$/{on=1; next} /^##/{on=0} on' docs/operator-guide.md | awk '/^```/{n++; if (n%2==0) {if (g && s) bad++; g=0; s=0}; next} n%2==1 && /gcloud /{g=1} n%2==1 && /^sudo /{s=1} END{print bad+0}'
```
Expect: `0`

```bash
awk '/^### The rebuild after a merge$/{on=1; next} /^##/{on=0} on' docs/operator-guide.md | grep -c -F 'factory-watch'
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
   Interface: "None" is stated and correct for a documents-only story. It names the only changed file and section: `docs/operator-guide.md`, `### The rebuild after a merge`. I found that heading at line 696 and *On GCP, step by step* at line 544. *On any Ubuntu 24.04 VM* is at line 650, and `factory-watch` is used around line 642. There is no code signature to pin, and none is needed.
   Criteria: each can be checked by one smoke command or by `make documents`. Criterion 1 (nothing outside the docs changes) and criterion 2 (`make check` stays green) are checkable. The docs criterion gives each rule its own bullet:
   - wait for `factory-watch`, then stop, with the stop-timeout reason;
   - the order: stop before `pull --ff-only`, start at the end, no `restart`;
   - where each block runs, with no block mixing `gcloud` and `sudo`;
   - the sentence for a VM outside GCP;
   - what stays.
   The failing side of the order rule (a `restart` present, or the pull before the stop) is covered by the second smoke test. The failing side of the mixed-block rule is covered by the third.
   Smoke test: the commands are runnable awk and grep pipelines over the guide, and `make documents`. The pytest `-q` rule does not apply, because no command runs pytest. Each `Expect:` line is checkable against the output: counts of at least 1, `0`/`1`, `0`, and `documents ok`.
   Architecture: this is documentation only, so the layers are untouched. The documenter's write path covers `docs/*`.
   Scope: the story stays inside F0043's operator-guide work. It touches no code, `vm/` or `factory/`. It leaves the `TimeoutStopSec` change open for the human, as the feature's Out of scope requires.
4. factory: started tests as vm.
