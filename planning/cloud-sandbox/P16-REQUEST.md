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

(empty)
