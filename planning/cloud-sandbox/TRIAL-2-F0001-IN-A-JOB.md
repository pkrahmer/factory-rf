# The factory builds a whole feature in a Cloud Run job (2026-11-02)

For the master. The first real run of F0047's job profile: the factory ran in a Cloud Run job of the sandbox project and built the todo demo's feature F0001 (four stories and the feature's acceptance) in the trial repository on the company's code host, with an opencode runtime and a Claude model behind the company's proxy. The raw record is `results/trial-f0001-in-a-job.txt`; this file says what happened, what to fix, and how to repeat it. No company value is in it: `<repo>`, `<project-id>`, `<proxy>` and so on stand for them.

## The short answer

It works. F0001 was built, reviewed, documented, smoke-tested and accepted in 2 h 05 min for 6.72 dollars, with no stop, crash or stall in the factory's log and no question to the human. Two defects of the job profile (below) cost two failed starts and are fixed here only by workarounds in the job's own configuration; they should be fixed in `vm/job-start.sh` and the guide.

| Work item | Minutes | Cost USD | Notes |
|---|---|---|---|
| F0001-S0001 domain model | 27 | 1.59 | includes the image build and preflight (about 3 min) |
| F0001-S0002 service layer | 16 | 0.94 | |
| F0001-S0003 HTTP API | 40 | 2.20 | one review round back to `doing`; a shared test helper moved under the standing leave |
| F0001-S0004 SQLite | 27 | 1.46 | the second repository's row in the contract test, as the feature's decision 15 says |
| F0001-A0001 acceptance | 9 | 0.53 | accepted, no story proposed |

The model costs come from the prices in the provider file (2 and 10 dollars per million tokens); the factory's cost records and the acceptance's table agree.

The idle shutdown worked as designed: 60 minutes after the acceptance was archived the factory logged `idle shutdown: idle for 60 minutes, ending the factory's process`, exited 0, and the execution ended as succeeded (3 h 09 min in all, an hour of it idle). A shorter idle time (10 to 15 minutes) would have saved most of that hour; it is the operator's setting.

## What failed on the way, and why (fix these)

1. **`vm/job-start.sh` does not put `<root>/tools/bin` on the `PATH`.** The preflight stopped the machine with `tool:uv: uv is not on the PATH`. On the VM the service file sets the `PATH`; the job script builds the tools venv and never exports it. Workaround used: a `PATH` variable on the job, `<root>/tools/bin` first, then the Debian default. Fix: the script exports it before `exec factory-run`.
2. **The hosting token cannot be a mounted secret as the guide says.** Cloud Run mounts a secret's folder read-only with mode 0555; the preflight's `token-file` item wants the folder at 0700 and the script cannot change a read-only mount, so the item can never pass. The guide's *What the job needs* tells the operator to mount the token with `--set-secrets=/path=<secret>` and name it in `FACTORY_TOKEN_FILE`. Workaround used: the job's wrapper copies the file into a folder of its own (`mkdir`, `chmod 0700`, `cp`, `chmod 0600`) before `job-start.sh`, and `FACTORY_TOKEN_FILE` names the copy. Fix: either the script does that copy for a token file whose folder is not private, or the item accepts a read-only mount owned by root.
3. **The stage image's `apt-get` needs `http_proxy` and `HTTP_PROXY`, not only the HTTPS pair.** `podman build` hands the build the proxy variables the job exports; apt reads `http://deb.debian.org`. The guide's *What the job needs* says only that `https_proxy` goes in the job's environment. Add `http_proxy` and `HTTP_PROXY` (the probes had all four, which hid this). The failure was `Could not resolve 'deb.debian.org'` at the image's first `apt-get`.
4. **A machine stop never ends an execution.** A run that stopped at the preflight (finding 1) stayed running for over 40 minutes: the idle shutdown does not fire while a machine stop holds the factory, and the task timeout was two hours. Combined with finding 5 this holds 8 CPUs for nothing. Worth a rule: in a job a machine stop at the preflight should end the process after a short wait, so that the platform shows the failure.
5. **The provisioner role cannot cancel an execution** (`run.executions.cancel` is denied for the impersonated identity). The only way to stop a running execution was to delete its job. If the operator's identity is the same, say so in the guide.

## What held

- Every step of `vm/job-start.sh` after the two fixes: inputs, proxy, packages, runc, metadata block, directories, tmpfs storage, code, tools, image, token, start. The image built in about 2 min of silent npm steps (the log shows nothing for several minutes after the apt output; do not mistake it for a hang). A first build took about 10 min, a later one about 3.
- The preflight: `podman`, `snapshots`, `metadata-block` and the `agent-run-probe` (one real model call) were green on every start after the fixes.
- The token refresher kept the model login valid for the whole run (3599-second tokens, refreshed every 10 minutes, no failure).
- The copy snapshots cost about 9 seconds per stage (reset 1.9 s, sync 0.8 s, advance 2.0 s, take 4.6 s); disk use at the end was 2 GB under the instance's root.
- The write path to the hosting service: the factory opened every draft pull request, set the stage labels, moved them, posted its comments and archived each merged work item within 30 seconds of the merge. P21's finding about marking a draft ready did not bite.
- Recovery and caps: nothing was needed. One review round back (S0003) went through at the normal cap.

## What the human-in-the-loop saw (for the operator skill)

- The `kumpel` skill's scripts use the `gh` login. At work that login did not see the trial repository; I drove the run with a small local helper that calls the hosting API with the sandbox's bot token (read from the secret store into a shell variable, never printed). If the skill is to work at work, its scripts need a token source other than the `gh` login, or the `gh` login must be allowed into the project's repository.
- The six approval checks were cheap to do from the API: the changed files with their status letters, a scan of added lines for suppression markers, the journal's smoke-test and review lines, and the cost records on the branch. They found nothing to refuse in five approvals. Two are worth a note: S0003's tester changed an earlier test file only to move a helper (the standing leave), S0004's tester added a row to an earlier file's repository lists, which the feature's decision 15 names.
- The waits: a loop that polls the work-item pull requests every 25 seconds and returns when the labels, the draft flag or the comment count change was enough. The pulls list does not carry a comment count; the issue endpoint does.
- `mergeable_state` read `unstable` on one pull request because an organisation status check (a security scanner) was still pending. It is outside the factory; with no branch protection the merge went through. A repository with required checks would hold every approval until the scanner finishes.
- Dependency bots of the organisation opened two pull requests on the trial repository during the run (a dependency bump and a bot's configuration). The factory ignored them; a human filtering the pull requests by branch name `work-item/...` does the same.
- A finished story removes its feature's `in-progress/` folder from `main` (the factory moves the file to `done/`), so the next start must create the folder again before `git mv`. The skill's `start-story.sh` does `mkdir -p`; a hand-written start does not.

## How to repeat it (the shape of the job, with placeholders)

Create one job (never two with the same instance at once) and execute it:

```bash
gcloud run jobs create <job> --image=docker.io/library/debian:trixie-slim --execution-environment=gen2 \
  --cpu=8 --memory=32Gi --task-timeout=14400 --max-retries=0 \
  --vpc-connector=<shared connector> --vpc-egress=all-traffic --service-account=<run-as> \
  --set-secrets=/secrets/hosting-token=<git token secret>:latest,/secrets-llm/client-secret=<model client secret>:latest \
  --set-env-vars="^@^FACTORY_INSTANCE=<name>@FACTORY_REPOSITORY_URL=<project url>@FACTORY_CODE_URL=<code url>@FACTORY_CODE_REF=<commit>@FACTORY_TOKEN_FILE=<root>/secrets/hosting-token@PATH=<root>/tools/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin@https_proxy=<proxy>@HTTPS_PROXY=<proxy>@http_proxy=<proxy>@HTTP_PROXY=<proxy>@NO_PROXY=<the model API's domain>@no_proxy=<the model API's domain>@FACTORY_CONTAINER_ENV=HTTPS_PROXY,https_proxy,NO_PROXY,no_proxy@FACTORY_OPENCODE_PROVIDER_FILE=<root>/provider.json@FACTORY_OPENCODE_MODELS=opus=<id>,sonnet=<id>,haiku=<id>@FACTORY_API_LOGIN_FILE=<root>/api-login@FACTORY_TOKEN_URL=<url>@FACTORY_TOKEN_SCOPE=<scope>@FACTORY_TOKEN_CLIENT_ID=<id>@FACTORY_TOKEN_CLIENT_SECRET_FILE=/secrets-llm/client-secret@FACTORY_IDLE_SHUTDOWN_MINUTES=60" \
  --command=sh --args="-c,<wrapper>"
```

The wrapper (one line of shell, its text shipped base64 and gzipped so that no quoting survives into the job): make `<root>/secrets` at 0700 and copy the mounted token into it; write `<root>/provider.json` (the provider file of the guide: id, base URL, `api_key_env` `ANTHROPIC_API_KEY`, one model with context, output and the two prices, `small_model`); write `vm/job-start.sh` of the code commit to `/tmp` and `exec sh` it. The commands are `gcloud run jobs execute <job>` and, afterwards, `gcloud run jobs delete <job>`; the log is `gcloud logging read 'resource.type=cloud_run_job AND labels."run.googleapis.com/execution_name"=<execution>'` (the lines arrive a minute or two late; a freshness flag is needed beyond the default for old executions).

To drive a story: commit `<story id>: start` on `main` after `git mv`-ing the file from `backlog/` to `in-progress/` (create the folder first), then poll the work-item pull requests; at `stage:approval` check the six things, merge with a merge commit, wait for the factory's `merged, archived` commit, and start the next story. When the last story is archived the factory opens the feature's acceptance on its own; merge it if it recommends acceptance.

## Slips of the session, for the record

- The first execution had the proxy variables of the HTTPS pair only (finding 3), so its image build failed. The second, with all four, failed at the preflight (findings 1 and 2) and stayed running. After the workarounds I deleted the job, which stopped the stuck execution, and recreated it, but a `sed -i` of my create script failed silently on the laptop's `sed`, so the new job had a two-hour timeout and a 20-minute idle exit instead of the intended four hours and one hour. I noticed within a minute, deleted it again and recreated it with the right values.
- Executions in all: five. One failed at the image, one stopped at the preflight until its job was deleted, one was deleted a minute after its start (the wrong timeout), one passed the preflight and idled out as succeeded after 20 minutes (the test of the workarounds), and the last built the feature.
