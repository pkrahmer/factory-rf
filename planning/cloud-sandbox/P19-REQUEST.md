# P19 request (2026-10-31): a Cloud Run worker pool instead of a job

For the session at work, after P17 and P18 (`P17-REQUEST.md`). Answer in this file, under *Response*, and push.

## Why

F0047 builds for a Cloud Run job: a task with a timeout of at most a day, restarted every night, with an idle exit (S0008) for scaling to zero. A worker pool runs a long-lived process with no timeout and a fixed number of instances, restarted when it ends. For an always-on factory that may fit better: no nightly restart, no crash charged to the stage in flight, and one instance means one factory, so two executions cannot overlap. Nothing built in F0047 is job-specific except S0008's exit and S0006's chapter, so the question is only whether the platform gives a worker pool the same sandbox and what it does with a process that ends.

P19 answers three things:

1. **The sandbox.** The same kernel, cgroups, root, `NoNewPrivs` and CPUs as a job (compare with P6)?
2. **The factory's needs.** nft's metadata block, a tmpfs mount at podman's storage root, podman as root with S0009's words, one container with the factory's limits, the proxy?
3. **The lifecycle.** The probe exits 0 after its checks. Does the pool start it again, and after how long? Scaled to zero, does a running process get `SIGTERM` first? Scaled back to one, does a new process start?

## Before the first run

`probes/run_worker_pool.sh` was written at home without a worker pool to try it on. Read `gcloud beta run worker-pools --help`, `gcloud beta run worker-pools deploy --help` and `gcloud beta run worker-pools update --help` first, and correct in the harness, where they differ: the words of `deploy` (the instance count `--scaling=1`, `--command`, `--args`, the connector flags), the scaling flag of `update`, and the log filter `resource.type=cloud_run_worker_pool AND resource.labels.worker_pool_name=...`. You may change the harness for this (not the probe); say in the response what you changed. If worker pools are refused by the organisation's policy, or `gcloud beta run worker-pools` does not exist, stop there and say so: that alone is the answer.

## What to do

1. `git pull --ff-only`, read `probes/run_worker_pool.sh` and `probes/p19-worker-pool.sh`, check the gcloud words as above.
2. Run it, with `PROBE_PROXY`, `PROBE_NO_PROXY` and the connector as for the jobs. It needs no secret and no model:

   ```bash
   planning/cloud-sandbox/probes/run_worker_pool.sh worker-pool docker.io/library/debian:trixie-slim p19-worker-pool.sh 2 4Gi
   ```

   It takes about 13 minutes (three phases of four minutes) and deletes the pool at the end, also on failure. Check with `gcloud beta run worker-pools list` afterwards that nothing is left.
3. If phase 1 shows the pool restarting the process, run it once more with `PROBE_MODEL=stay`, which makes the probe stay alive, so that phase 2 shows whether a running process gets `SIGTERM` when the pool scales to zero.
4. Save the output as `results/p19-worker-pool.txt` (and `results/p19-worker-pool-stay.txt`), masked as before.
5. Add a section `## P19: a worker pool (<date>)` at the end of `capabilities.md`: whether a pool could be created, and with which words; the sandbox lines against P6's (kernel, cgroups, uid, `CapEff`, `NoNewPrivs`, CPUs, memory); the nft, metadata, tmpfs, runc and container lines; the storage line; for each phase which start ids appeared and when (a restart is a new id), whether `got SIGTERM` appeared on the scale to zero, and how long after the scale to one a new start appeared; what the deploy and the updates printed; your one-sentence verdict: is a worker pool the same sandbox, and does it restart, stop and start the factory as an always-on instance needs?
6. Write a short answer under *Response* below. Commit the result files, the harness if you changed it, `capabilities.md` and this file with the message `planning: cloud sandbox: P19, a worker pool`, stage only those, push to `main`.

The rules of the earlier probes bind: no company value in any file of this repository, no secret printed or committed, no change outside `planning/cloud-sandbox/`, nothing created in the cloud project beyond the throwaway pool the script makes and deletes.

## Response

(empty)
