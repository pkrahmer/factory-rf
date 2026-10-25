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
