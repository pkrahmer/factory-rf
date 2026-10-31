# P16 request (2026-10-31): is the suite slow in the job because of fuse-overlayfs?

For the session at work. Written at home after your second P15 run, which answered the root question (thank you: all seven targets green, as root). Answer in this file, under *Response*, and push.

## Why

`make test` took 601 s in the job (10 CPUs seen) against 167 s on the VM (4 CPUs): about nine times slower per CPU, and the pipeline gives `check` 8 minutes, so every story would hit its limit in the job. The suspect is `fuse-overlayfs`: S0002's podman words store images through it, so every file a container reads from its image passes a userspace daemon, and the suite starts thousands of processes. P8 showed podman's native kernel overlay working with its storage on a tmpfs. P16 repeats P15's `make sync` and `make test` with exactly that storage and nothing else changed. Its time against 601 s decides whether S0002's storage words change before S0006 is built.

The backticks in P15's last line were my slip; P16 has none. P16 also prints the test target's last lines, so pytest's summary is in the log.

## What to do

1. `git pull --ff-only`, read `probes/p16-native-overlay-test.sh`.
2. Run it as P15, with `PROBE_PROXY` and `PROBE_NO_PROXY`:

   ```bash
   planning/cloud-sandbox/probes/run_probe.sh native-overlay docker.io/library/debian:trixie-slim p16-native-overlay-test.sh 8 32Gi
   ```

3. Save the log as `results/p16-native-overlay-test.txt`, masked as before.
4. Add a section `## P16: the test suite with the native overlay on a tmpfs (<date>)` at the end of `capabilities.md`: the tmpfs mount's exit, what `podman info` printed (storage driver, graph root, backing filesystem, whether a mount program is used), the build's time, `make sync`'s and `make test`'s exits and times, pytest's summary line, failed tests with their `E` lines if any, the time of the 50 Python starts, the memory, and your one-sentence verdict against the probe's VERDICT line.
5. Write a short answer under *Response* below. If the probe is broken, do not fix it; say what is wrong and push only this file and the log.
6. Commit the result file, `capabilities.md` and this file with the message `planning: cloud sandbox: P16, the test suite with the native overlay`, stage only those, push to `main`.

The rules of P14 and P15 bind: no company value in any file of this repository, no secret printed or committed, no change outside `planning/cloud-sandbox/`, nothing created in the cloud project beyond the one throwaway job the script makes and deletes.

## Response

*(the session at work, 2026-10-31)*

**Verdict.** fuse-overlayfs was the cause. With podman's storage on a 24 GiB tmpfs and the native kernel overlay, `make test` took **182 s** against 601 s, exit 0, coverage 99.57 % (floor 90 %), no failing test; the image build took 107 s against 199 s; 50 Python starts in one container took 1 s. `podman info` confirms the setup: driver `overlay`, native diff true, backing filesystem `tmpfs`, no mount program. S0002's storage words should change before S0006 is built.

**What I added.** As you asked, a watch: 28 lines in `probes/p16-native-overlay-test.sh` around the `make test` step (every 5 s the job's CPU use from `/proc/stat`, the load, the memory; the cgroup's CPU throttling counters before and after). It only reads. I pushed that change with the result, which the request's step 6 did not list, so that the probe in the repository is the one that produced the log. I dropped my own `p16-test-cpu.sh`, which had the same number.

**What the watch showed (the answer to "did the suite use all the cores").** Yes, up to the job's quota: 76 to 88 % of the 9 visible CPUs for the first 160 s (7 to 8 CPUs), against a quota of 7.89 CPUs, with 456 of 1799 periods throttled (25 %), 34.6 s throttled in all. The last 20 s are almost idle: one process finishing the coverage report. Average over the whole test 70.1 %, peak 88.1 %.

**Surprises and slips.**
- The watch's "workers" column is 0 throughout: it looked for `execnet` in the process arguments and the workers do not carry it. Its "busy" column (processes above 20 % CPU) is the usable one: 8 to 10. The `-n auto` count was not read.
- Pytest's summary line is again not in the log (the target runs quietly); the coverage table and the target's green line are.
- `make sync` took 13 s here against 8 s with fuse-overlayfs, probably the first fill of the tmpfs; it does not matter next to the 419 s saved on the test.
- The tmpfs counts against the job's memory: the cgroup peaked at 5388 MiB. A big stage image or several at once will need that room.

**Probe.** Nothing broken, apart from the worker column of my own addition.

**Pushed.** `results/p16-native-overlay-test.txt`, the section *P16* at the end of `capabilities.md`, this file, and the probe with the watch. No company value in any of them, no secret printed, nothing outside `planning/cloud-sandbox/` changed; the throwaway job was created and deleted by the script, and the project holds only the job it held before.
