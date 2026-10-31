# P21 request (2026-10-31): the trial project in a job

For the session at work, which seeded the demo project into a repository on the company's GitHub. Answer in this file, under *Response*, and push. Thank you for P20: it showed that GitHub is reached only through the proxy, now in S0006's chapter.

## First: bring the seeded demo up to v1.2

The demo project in factory-rf was stale: since v1.2 the stage environment runs `make sync` before every agent run and every check, and the demo had no `sync` target, so the first stage would have failed. Fixed at home in commit `7c7b045b7`. Your seeded repository has the same gap.

1. `git pull --ff-only` in factory-rf.
2. Copy `demo/todo-service/project/Makefile` and `demo/todo-service/project/factory/pipeline.yml` over the same two files of the seeded repository, commit them on its `main` with the message `v1.2: the sync target and command`, and push. Compare the rest of the seeded repository with `demo/todo-service/project` (`diff -r`, leaving out `.git`) and name any other difference in the response; change nothing else.

## Why

Two questions stand between F0047 and its first real story, and both are about the trial project:

1. **Does the demo's check pass in the stage image, in a job?** P16 ran factory-rf's own suite. The demo has its own `Makefile`, `pyproject.toml` and `uv.lock`, and its `make check` runs `semgrep`, `detect-secrets` and the rest in containers of the stage image, as root.
2. **Does the token the factory will use suffice for its write path?** P20 only read, with a classic token. The factory pushes branches and opens, labels, comments on, closes and reopens pull requests. P21 does each once, on a throwaway branch, and removes everything again; `main` is not touched.

## What to do

1. Read `probes/p21-demo-project-in-a-job.sh`.
2. Run it with **the token the factory will use** for this repository (a fine-grained token limited to it, if that is what you will give the factory), mounted as the secret `GIT_TOKEN` as in P20, the repository as `<owner>/<repo>` in `PROBE_LLM_BASE_URL`, and the proxy as always:

   ```bash
   planning/cloud-sandbox/probes/run_probe.sh demo-project docker.io/library/debian:trixie-slim p21-demo-project-in-a-job.sh 8 32Gi
   ```

3. Afterwards, check in the repository's web page that no branch `probe/...`, no open pull request of the probe and no label `p21-...` is left. A closed pull request stays in the history; that is expected.
4. Save the log as `results/p21-demo-project-in-a-job.txt`, masked as before (the repository's name never appears; check it).
5. Add a section `## P21: the trial project in a job (<date>)` at the end of `capabilities.md`: whether the seeded repository has the four files and the four targets; the build's time; `make sync` and every check target, green or red, with failed tests and their `E` lines and what `detect-secrets` flagged; for part B every step's HTTP status and message; whether anything was left over; and your one-sentence verdict against the probe's VERDICT line. If a step of B answers 403 or 404, name the permission the token lacks, as GitHub's message names it.
6. Write a short answer under *Response* below, with the differences found in *First*. Commit the result file, `capabilities.md` and this file with the message `planning: cloud sandbox: P21, the trial project in a job`, stage only those, push to factory-rf's `main`.

The rules of the earlier probes bind: no company value in any file of factory-rf, no secret printed or committed, no change outside `planning/cloud-sandbox/` in factory-rf, nothing created in the cloud project beyond the throwaway job the script makes and deletes.

## Response

(empty)
