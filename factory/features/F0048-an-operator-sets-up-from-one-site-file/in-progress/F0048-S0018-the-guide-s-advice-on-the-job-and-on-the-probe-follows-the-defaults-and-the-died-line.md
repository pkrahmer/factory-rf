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
  started_at: '2026-11-03T09:51:33.745787Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T09:51:33.739546Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T09:51:33.745787Z'
  stage: intake
---

# The guide's advice on the job and on the probe follows the defaults and the died line

<!-- proposed by feature acceptance of 2026-11-03; the human added part B on 2026-11-03 (decision 24) -->

## Description

S0014 gave `job.sh` the example's sizes as its defaults (decision 21): 4 CPUs, 16Gi, a task timeout of 86400 seconds (24 hours) and 30 idle minutes. S0015 made a `died` run leave its text in the factory log. Three passages of `docs/operator-guide.md` were written before both and now advise against what the factory does:

- *On Cloud Run*, *What the job needs*, **Size**: "Eight vCPUs and 16 GiB of memory at least". The default and the example's `SITE_CPU=4` give half of that, so an operator who keeps the default reads that their job is below the minimum, and one who trusts the guide changes a value the human chose.
- The same list, **The task timeout**: "Set the timeout shorter than the schedule's interval: 23 hours for a daily schedule". The default is now 24 hours, the interval itself, and the passage does not say that a job on a daily schedule must set `SITE_TIMEOUT` below the default.
- *The probe of the agent run*: a flag the pinned `claude` rejects makes "every real run ... end `died` with no text that says why". Since S0015 the factory log names each such run with its text (*A provider's spend limit*, the paragraph *A run that ends `died`*).

This story corrects the three passages so that they say what the factory does (part A). It changes no default: the defaults are the human's (decision 21).

**Part B: the job keeps one image in memory.** The job mounts podman's storage as a tmpfs (`vm/job-start.sh`, step `storage`), so every image byte counts against the job's memory, which is 16Gi by default now. The step `image` builds the stage image (about 2.4 GB on vm) with podman's layer cache, which leaves the build's intermediate images in that tmpfs beside the final one. Nothing in an execution needs them: the image is built once per execution and never rebuilt in it. Part B builds without the layer cache and removes the unused untagged images right after the build, so that only the tagged stage image and its base stay in memory. On a machine, every rebuild leaves the previous stage image untagged; on vm 104 images and 26 GB had piled up by 2026-11-03. The guide's rebuild routine therefore gains the same prune.

## Interface

Part A: none; the documenter changes `docs/operator-guide.md`.

Part B, `vm/job-start.sh`, step `image`: the build passes `--layers=false`, and after a successful build the step runs `podman $JOB_PODMAN_OPTIONS image prune -f`, whose failure fails the step as a failed build does. It never removes a tagged image. Nothing else in the script changes.

Tests: a new text test over `vm/job-start.sh` (the step `image` holds the build with `--layers=false`, followed by the prune, in that order), beside the existing tests of the script.

## Acceptance criteria

1. (B) The step `image` of `vm/job-start.sh` builds with `--layers=false` and then runs `podman $JOB_PODMAN_OPTIONS image prune -f`, in that order; a step without either, or with them in the other order, fails its row.
2. Nothing under `src/`, `operator/`, `image/`, `template/` or `claude/` changes, and under `vm/` only `vm/job-start.sh`.
3. `make check` stays green.
4. docs: `docs/operator-guide.md`:
   - *What the job needs*, **Size**: says that the job gets 4 vCPUs and 16 GiB of memory unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and that memory is the limit to raise first, because the root file system, the tmpfs of the image layers, the checkout, the base copy and the workspace all count against it. The words "Eight vCPUs" and "at least" go. The rest of the bullet (the plain base copy, about 1.6 s per GiB for a reset) stays.
   - **The task timeout**: says that the default, 86400 seconds, is the platform's maximum of 24 hours and equals a daily schedule's interval, so a job executed every night sets `SITE_TIMEOUT` below it, such as `23h`. The sentence on two executions that must never overlap stays.
   - *The probe of the agent run*: the parenthesis after "a flag the pinned `claude` rejects" says that every real run would end `died`, each with its line `run <run id> of <work item> (<stage>) died: <text>` in the factory log, instead of "with no text that says why".
   - **Size** also says that the stage image, about 2.4 GB, sits in the job's memory because podman's storage is a tmpfs, and that the job removes the build's leftovers (part B).
   - *The rebuild after a merge*: after the image is built, `podman image prune -f` as the factory's user removes the previous stage image and the build's leftovers. It removes only untagged images that no container uses, so another instance's tagged image and a running container are safe. The guide says that the next build is slower without the cache.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'Eight vCPUs' docs/operator-guide.md; grep -c 'no text that says why' docs/operator-guide.md
```
Expect: `0`, then `0`

```bash
sed -n '/^### What the job needs/,/^### The environment/p' docs/operator-guide.md | grep -c 'SITE_TIMEOUT'
```
Expect: a number of at least `1`

```bash
grep -c -- '--layers=false' vm/job-start.sh; grep -c 'image prune -f' vm/job-start.sh
```
Expect: `1`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
