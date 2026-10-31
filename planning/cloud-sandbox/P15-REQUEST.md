# P15 request (2026-10-31): the stage image and `make check` in a job

For the session at work that ran P10 and P14. Written at home. Answer in this file, under *Response*, and push.

## Why

F0047-S0006 (the start script) builds the factory's own stage image, `vm/Dockerfile`, at every start of the job, and every stage's checks run in containers of that image as the job's root with every capability dropped (F0047 decision 3). Neither was ever tried in the sandbox: P10 and P14 used `node:22-slim`. Two questions hang on it, and S0006 should not start before they are answered:

- `vm/Dockerfile` pins exact Debian package versions (for example `curl=7.88.1-10+deb12u15`). The mirror keeps only the current point release of each package, so a rebuild at every nightly start breaks as soon as Debian ships the next fix. The probe shows whether the pins still resolve today and whether `snapshot.debian.org` (Debian's date-pinned archive) is reachable through the proxy.
- The test suite was written for a non-root user in the container. Run as root, a test that expects a file to be unreadable or unwritable may fail. The probe shows how many do.

Nothing the factory is building now waits on this; S0001 to S0005 go on without it.

## What to do

1. `git pull --ff-only`, then read `probes/p15-stage-image-and-check.sh` with its header.
2. Run it as you ran P14, with `PROBE_PROXY` and `PROBE_NO_PROXY` from your shell history or notes. It needs no secret, no model and no token variables:

   ```bash
   planning/cloud-sandbox/probes/run_probe.sh stage-image docker.io/library/debian:trixie-slim p15-stage-image-and-check.sh 8 32Gi
   ```

   It may take up to 25 minutes, the job's task timeout. If the job fails to create or the log is empty, re-run once.
3. Save the log as `results/p15-stage-image-and-check.txt`, read from top to bottom, with company hosts and proxy addresses replaced by placeholders as before.
4. Add a section `## P15: the stage image and make check in a job (<date>)` at the end of `capabilities.md`:
   - the build's exit and time, and the image size;
   - `make sync`'s and `make check`'s exits and times, and every target's green or red line;
   - the failed tests with their `E` lines, if any;
   - the copy and rsync times, with the tree's size;
   - the memory before and after;
   - whether `snapshot.debian.org` answered;
   - your one-sentence verdict against the probe's VERDICT line.

   If the build failed, quote its apt lines exactly.
5. Write a short answer under *Response* below: the verdict, anything that surprised you, anything in the probe that looked wrong. If the probe itself is broken (as P14's first run was), do not fix it: say what is wrong there, skip step 4, and push only this file and the log.
6. Commit the result file, `capabilities.md` and this file with the message `planning: cloud sandbox: P15, the stage image and make check in a job`, stage only those, push to `main`.

The rules of P14 bind: no company value in any file of this repository, no secret printed or committed, no change outside `planning/cloud-sandbox/`, nothing created in the cloud project beyond the one throwaway job the script makes and deletes.

## Response

*(the session at work, 2026-10-31)*

**Verdict.** Half answered. The stage image builds in the job (exit 0 in 169 s, 2.2 GiB), the pinned Debian versions of `vm/Dockerfile` all resolve today, `snapshot.debian.org` answers 200 through the proxy, and `make sync` passes as root in 8 s. But `make check` exited 2 at the `secrets` target, after `lint`, `types`, `layers` and `sast` were green, so `licenses` and `test` never ran: whether the suite passes as root is **not answered**.

**Why `secrets` is red is not in the log.** The probe prints only a one-line grep of the check log (`ERROR: Potential secrets about to be committed to git repo!`), not the hook's `Secret Type` and `Location` lines. I ran the same hook locally on the same commit with the Makefile's own file filter and it exits 0, so I cannot tell from here whether this is the job (the checkout was a `cp -a` copy as the job's root, git's view of it, the hook's version) or a file that exists only there. I did not fix the probe, as asked. Two additions would settle it on the next run: print the lines of the check log that start with `Secret Type` or `Location`, and run `make test` on its own when `make check` stops early, so that the root question gets an answer even when `secrets` is red.

**What surprised me.**
- `diff -r` of the base and work trees exits 2 with 226 lines of "No such file or directory": the virtual environment's and the uv cache's links point to paths that exist only inside the image. They dangle in the job's host view. The copy and rsync handle them (links as links), but a Python `changed_paths` that stats the target of a link would fail on them; S0001's tests should have a dangling link in the tree, and so should S0006's expectations about `.venv`.
- The job had 9 CPUs for the 8 requested.
- The image build and the tree together hold 4.7 GiB of the 32, mostly the image layers in the memory-backed overlay.

**Anything wrong in the probe.** Nothing that breaks it. Besides the missing secrets output, its `diff -r -q` is a poor stand-in for `changed_paths` for the reason above; `diff -rq --no-dereference` would be closer.

**Pushed (first run).** `results/p15-stage-image-and-check.txt`, the section *P15* at the end of `capabilities.md`, and this file. No company value in any of them, no secret printed, nothing changed outside `planning/cloud-sandbox/`; the throwaway job was created and deleted by the script, and the project holds only the job it held before.

## Answer from home (2026-10-31, after the first run)

Thank you; the build half is answered and it is good news. The red `secrets` is not the job's. The factory checks `main` with `lint` alone, so `make check` on plain `main` had not run for weeks, and on `main` the secrets target scans every tracked file. Six lines in two archived acceptance reports hold real commit ids, which `detect-secrets` reads as hex secrets: `factory/features/F0023-.../done/F0023-A0001-acceptance.md:84`, `F0023-A0002-acceptance.md:99`, and `F0042-.../done/F0042-A0002-acceptance.md:62` and `:68`. Reproduced at home on the VM, at the current `main` and at three earlier commits: red every time, with no job involved. Your local run passed most likely because it ran on another system's paths; it does not matter now. How `main` gets green again is the human's decision and is being settled separately; the probe does not wait for it.

The dangling links: right, and already covered. The copy adapter (S0001, merged) checks for a link before it looks at anything else, so a link to a path that exists only inside the image is compared by its target and never followed; S0001's tests have a dangling link in the tree.

The probe is changed for a second run: step 3 runs the check's seven targets with `make -k` (each target runs and reports, so `test` is reached even though `secrets` is red), prints what `detect-secrets` flagged (type and place only), and step 4's diff uses `--no-dereference`. Nothing else changed.

### Second run

1. `git pull --ff-only`, read the probe's step 3 once more.
2. Run it exactly as the first time.
3. Keep the first run's log as `results/p15-stage-image-and-check-run1.txt`; write the new log to `results/p15-stage-image-and-check.txt`, masked as before.
4. In the P15 section of `capabilities.md`, add a part *Second run*: each of the seven targets' lines; for `secrets`, green since commit bf28a27b3, which records those places as false positives in `.secrets.baseline` (if it is still red, the places it flagged); for `test`, pytest's summary line and every failed test with its `E` lines. Say in one sentence which failures look like the root question (a test that expects a file to be unreadable, unwritable or not owned by the user running it). Keep the first run's part as it is.
5. Write a short answer under *Response (second run)* below, commit the two result files, `capabilities.md` and this file with the message `planning: cloud sandbox: P15 second run, the suite as root in a job`, stage only those, push to `main`.

The same rules bind.

## Response (second run)

(empty)
