# P17 and P18 request (2026-10-31): opencode in the stage image, and how a job execution ends

For the session at work. Written at home after P16, which settled the storage question (thank you: S0009 now drops `fuse-overlayfs`). Answer in this file, under *Response*, and push.

## Why

Two links of F0047 are still unmeasured, and both matter before the first real story runs in a job. Nothing being built waits on them.

- **P17, opencode in the factory's own stage image.** P10 and P14 ran opencode in `node:22-slim`. The factory runs it in the stage image (`vm/Dockerfile`, Debian's Node 18), as the job's root with every capability dropped, with podman's native overlay on a tmpfs, F0046's provider block and S0007's lockdown. P17 builds that image and gives the agent one small task: fix a bug in `calc.py`, run Python to show the result, end with the factory's result block.
- **P18, the job's lifecycle.** (A) When the main process exits 0 while a background process still runs (the token refresher of S0004 will), does the execution end at once and count as succeeded? (B) At the task timeout, does the platform send `SIGTERM` before it kills, and how long before? The factory finishes its tick on `SIGTERM` and recovers from a hard kill anyway, but the answer decides what S0006's chapter tells the operator.

Two small changes to `probes/run_probe.sh` come with them: it now starts the probe with `exec`, so that the probe is the job's first process (as `factory-run` will be, S0006 ends in `exec`) and receives the platform's signals; and `PROBE_TASK_TIMEOUT` sets the task timeout (default 1500 s, as before). Neither changes how the earlier probes run.

## What to do

1. `git pull --ff-only`, read `probes/p17-opencode-in-the-stage-image.sh`, `probes/p18-job-lifecycle.sh` and the two changed lines of `probes/run_probe.sh`.
2. Run P17 as P14, with the same environment (the proxy, `PROBE_NO_PROXY` with the API's host, `PROBE_LLM_BASE_URL`, the token variables, `LLM_KEY` mounted as the secret):

   ```bash
   planning/cloud-sandbox/probes/run_probe.sh opencode-stage docker.io/library/debian:trixie-slim p17-opencode-in-the-stage-image.sh 8 32Gi
   ```

3. Run P18 twice. It needs no secret, no proxy and no model; unset `LLM_KEY`'s secret mount from `PROBE_EXTRA_ARGS` for it if you can, it is not read:

   ```bash
   PROBE_MODEL=exit planning/cloud-sandbox/probes/run_probe.sh lifecycle-exit docker.io/library/debian:trixie-slim p18-job-lifecycle.sh 1 512Mi
   PROBE_TASK_TIMEOUT=90 planning/cloud-sandbox/probes/run_probe.sh lifecycle-timeout docker.io/library/debian:trixie-slim p18-job-lifecycle.sh 1 512Mi
   ```

   For each, note the final state the harness prints (running, succeeded, failed, completion) and the condition's message.
4. Save the logs as `results/p17-opencode-in-the-stage-image.txt`, `results/p18-job-lifecycle-exit.txt` and `results/p18-job-lifecycle-timeout.txt`, masked as before.
5. Add two sections at the end of `capabilities.md`:
   - `## P17: opencode in the stage image (<date>)`: the build's time; Node's and opencode's versions in the image and the user id; opencode's exit and time; `calc.py` afterwards; the tool calls; whether the agent reported 5; whether the strict result block parsed; the cost reported; anything in the stderr lines; your one-sentence verdict against the probe's VERDICT line.
   - `## P18: how a job execution ends (<date>)`: for the exit run, whether the probe was process 1, how long after the main process's exit the execution ended, its final state, and whether the child's lines show it was signalled; for the timeout run, whether and when `the main process got SIGTERM` appeared against the 90 s, whether the child got it too, whether `exits 0 after SIGTERM` appeared, the final state and its message. Note that a `sleep 5` in the foreground can delay the trap by up to five seconds.
6. Write a short answer under *Response* below. If a probe is broken, do not fix it; say what is wrong and push only this file and the logs.
7. Commit the three result files, `capabilities.md` and this file with the message `planning: cloud sandbox: P17 and P18, opencode in the stage image and the job's lifecycle`, stage only those, push to `main`.

The rules of the earlier probes bind: no company value in any file of this repository, no secret printed or committed, no change outside `planning/cloud-sandbox/`, nothing created in the cloud project beyond the throwaway jobs the script makes and deletes.

## Response

(empty)
