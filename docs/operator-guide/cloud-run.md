# The factory in a Cloud Run job

A topic of the [operator guide](README.md).

## On Cloud Run

A Cloud Run job runs the factory without a VM. The job starts bare: the root file system is memory, nothing is installed and nothing persists, so every start installs the tools, clones the code and builds the stage image again. `operator/vm/job-start.sh` is the job's command. It is a POSIX `sh` script that turns a bare `debian:trixie-slim` into a running instance and ends in `exec factory-run`. Creating the job, its secrets and its schedule is yours; this chapter says what to give it. The pieces it uses are described under *The job profile*, *The metadata server in a job*, *Without ZFS* and *The idle shutdown* in [machine.md](machine.md).

### What the job needs

- **Size.** The job gets 4 vCPUs and 16 GiB of memory unless `SITE_CPU` and `SITE_MEMORY` say otherwise. Memory is the limit to raise first: the root file system is memory, and so is the tmpfs that holds the image layers (see *The job profile*), so the root file system, the image layers, the checkout, the base copy and the workspace all count against it. The stage image, about 2.4 GB, sits in the job's memory because podman's storage is a tmpfs; the job builds it without the layer cache and removes the build's leftovers (the untagged images) right after the build, so that only the tagged stage image and its base stay. The base is a plain copy (see *Without ZFS*), so the tree is held twice; a reset takes about 1.6 s per GiB.
- **A start takes a few minutes**, measured on 2026-10-31: the install, the clone and the image build.
- **The task timeout** is 24 hours at most, and the job is executed again every night. Two executions of one job must never overlap, because both would act as the one instance. The default, 86400 seconds, is the platform's maximum of 24 hours and equals a daily schedule's interval, so a job executed every night sets `SITE_TIMEOUT` below it, such as `23h`. Set the timeout shorter than the schedule's interval.
- **No retries:** create the job with `--max-retries=0`, or a timeout would start a second execution at once.
- **The network.** The job cannot resolve `github.com` itself. Git over HTTPS and the REST API are reached only through the proxy of the shared connector (measured in P20). The factory's own git and PyGithub read the job's `https_proxy`, so the job's environment carries it. `NO_PROXY` must not name a GitHub host.
- **Secrets are files.** Mount them with `--set-secrets` at a path (`--set-secrets=/secrets/token=<secret>:latest`) and name the path in the environment. The preflight's `token-file` item wants the hosting token's folder private, as on a VM: owned by the factory's user (root in a job) with no permission bit for group or others. A mounted secret's folder is read-only at mode `0555`, so give the mounted path as it is: when the token's folder is not private, the script copies the token to `<root>/secrets/hosting-token` (folder `0700`, file `0600`), points `FACTORY_TOKEN_FILE` at the copy and prints `job-start: token-file: copied to <root>/secrets`. A folder that is already private is used as it is, and nothing is copied. The original is not changed, and the token's text is never printed. If the copy fails, the script stops with `job-start: token-file: failed`, status 1.
- **The service account's token stays out of reach.** The script loads the rule that rejects TCP port 80 to `169.254.169.254` (see *The metadata server in a job*).

What does not work in a job: rootless containers, a bridge network, a pushed image (there is no registry the factory can push to; the job builds the image at each start), a second job that shares the disk, and `fuse-overlayfs` for Podman's storage (three times slower, measured in P15 and P16).

### The environment

The job's environment is the instance's configuration. The script reads these variables and stops with `job-start: <name> is not set` and status 2 when a required one is missing, before anything else runs.

| Variable | |
| --- | --- |
| `FACTORY_INSTANCE` | required: the instance's name |
| `FACTORY_REPOSITORY_URL` | required: the project |
| `FACTORY_CODE_URL` | required: the repository the factory's code and `operator/vm/Dockerfile` come from; cloned without a credential (see *The code and the project apart* in [machine.md](machine.md)) |
| `FACTORY_CODE_REF` | required: a tag or a commit of the code repository. There is no default, so nothing pushed to its `main` reaches a job unseen: you move the ref deliberately. |
| `FACTORY_TOKEN_FILE` | required: the path of the file that holds the hosting token; a file the script can read, else `job-start: FACTORY_TOKEN_FILE is not a file`, status 2. If its folder is not private, the script copies it into `<root>/secrets` and uses the copy (see *Secrets are files*). The script never prints it. |
| `HTTPS_PROXY` or `https_proxy` | optional: when set (`HTTPS_PROXY` wins when both are given and not empty), `apt` and every download use it. The script exports all four spellings, `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy`, to every later step, because the stage image's package manager fetches over plain HTTP. An `HTTP_PROXY` or `http_proxy` the job sets to a value that is not empty keeps its own value. |
| `FACTORY_JOB_ROOT` | optional, default `/srv/factory/<instance>`: the folder of everything below |
| `FACTORY_STAGE_IMAGE` | optional, default `factory-stage:<instance>` |
| `RUNC_VERSION`, `RUNC_SHA256` | optional, default `1.5.2` and its checksum, both constants of the script. Give both or neither: `RUNC_VERSION` without `RUNC_SHA256` stops with `job-start: RUNC_SHA256 is not set`, status 2, because a version without its checksum would not be checked. |
| `FACTORY_TOKEN_URL` and its companions | optional: when set, the token refresher runs (see *A bearer token for the model API* in [agent-runtime.md](agent-runtime.md)) |
| `FACTORY_IDLE_SHUTDOWN_MINUTES` | optional, yours: unset means no idle shutdown (see below) |
| `FACTORY_TRANSCRIPT_DIR` | optional, yours: the transcript folder (see *Transcripts*, *In a Cloud Run job* in [health.md](health.md)). When set, the script checks that the folder exists and that a file can be made and removed in it; if not, it stops with `job-start: transcript folder <path> cannot be written`, status 1. Unset changes nothing. |
| `FACTORY_JOB_PREFIX` | for the script's tests: put in front of `/etc`, `/usr/local/bin` and `/var/lib/containers`. Leave it unset. |

Beside these the job carries the settings of any instance (the hosting token's companions, the agent runtime's login, `FACTORY_CONTAINER_ENV`, `FACTORY_CA_BUNDLE`, `FACTORY_OPENCODE_MODELS`); the script never changes those.

The script sets the following only where the job gave no value: `FACTORY_SNAPSHOTS=copy`, `FACTORY_SNAPSHOT_BASE`, `FACTORY_WORKSPACE`, `FACTORY_CHECKOUT`, `FACTORY_STATE`, `FACTORY_CLAUDE_HOME` and `FACTORY_IMAGE_ID_FILE` (all under `<root>`), `FACTORY_CONTAINER_PROFILE=job`, `FACTORY_AGENT_RUNTIME=opencode` and `FACTORY_IDLE_SHUTDOWN_ACTION=exit`. It also sets `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION` from the `ARG` lines `CLAUDE_CODE_VERSION=` and `OPENCODE_VERSION=` of the cloned `operator/vm/Dockerfile`, which the preflight's item `agent-runtime-version` compares with the stage image.

### The steps

The script prints `job-start: <step>` on standard output at each step, in this order:

1. `inputs`: the checks above and the derived variables; the copy of a token whose folder is not private; the check of the transcript folder, when `FACTORY_TRANSCRIPT_DIR` is set (it prints no step line of its own); then `PATH` becomes `<root>/tools/bin` followed by the `PATH` the script was started with, so the preflight finds `uv` and the factory's commands that the `tools` step builds there.
2. `proxy`: with a proxy set, exports the four spellings and writes `/etc/apt/apt.conf.d/99proxy`.
3. `packages`: `apt-get update`, then one `apt-get install` of `podman`, `uidmap`, `nftables`, `git`, `make`, `curl`, `ca-certificates`, `rsync`, `python3` and `python3-venv`, at the versions of the Debian release.
4. `runc`: downloads `runc.amd64` of the release, checks it with `sha256sum -c` against the script's own checksum, and installs it as `/usr/local/bin/runc`. A mismatch stops with `job-start: runc: checksum does not match`, status 1. A checksum downloaded beside the binary would check nothing, so there is none. The download folder is removed whenever the step ends, by success or by a stop.
5. `metadata`: loads the `nft` rule of *The metadata server in a job* in [machine.md](machine.md) from `<root>/metadata-block.nft`.
6. `directories`: the workspace, the empty base, the checkout and the state.
7. `storage`: mounts a tmpfs at `/var/lib/containers`, Podman's storage root, so that images use the kernel's overlay. A failed mount stops with `job-start: storage: cannot mount a tmpfs at <path>`, status 1.
8. `code`: clones `FACTORY_CODE_URL` and checks out `FACTORY_CODE_REF`, with no credential and no prompt. A ref that does not exist stops with `job-start: code: no ref <ref> in <url>`, status 1. Then it installs the checkout's own `operator/vm/git-credential-factory` as `/usr/local/bin/git-credential-factory` (mode `0755`); a failing install stops with `job-start: code: failed`, status 1. The factory's git takes its credential only from that helper, which answers for the project's host only, so without it no fetch of a private project and no push could authenticate (see "The hosting-service token" in [health.md](health.md)). `operator/vm/setup.sh` installs the same helper on a VM.
9. `tools`: a virtual environment `<root>/tools` with `uv` at the version of `operator/vm/Dockerfile`, then `uv sync --frozen --no-dev` in the code checkout.
10. `image`: builds the stage image from the checkout's `operator/vm/Dockerfile` with the job's Podman options (the three words of *The job profile* in [machine.md](machine.md)) and writes a new uuid to the image-id file.
11. `token`: when `FACTORY_TOKEN_URL` is set, runs the refresher once and waits for it, which must succeed, then starts it in the background.
12. `start`: `exec factory-run` of the code checkout's environment.

Any other failing step stops the script with `job-start: <step>: failed` on standard error and status 1, and `factory-run` is not started. The job's log has the last step printed.

### Starts, restarts and the end of an execution

A start or a restart costs a few minutes, because the checkout, the base and the image are rebuilt. The state directory goes with the memory, so the factory log, `health.json` and the preflight stamp start empty, and the preflight runs at every start.

A restart during a stage is a crash for the factory (see *A restart during a stage* in [work-items.md](work-items.md)): recovery charges one crash for the stage in flight, and after `crash_cap` crashes (two by default) the work item waits for your answer. A story in flight on two nights therefore waits once. A stop between stages before the nightly restart is a candidate for later and does not exist yet.

How an execution ends:

- **At the timeout** the platform sends `SIGTERM` to `factory-run` with no warning before it (measured in P18). The factory ends after the tick in progress, and the platform marks the execution failed with `The configured timeout was reached`, even when the exit status is 0. A nightly timeout is planned and not a fault.
- **When `factory-run` exits with status 0** the execution ends as succeeded at once, background processes such as the refresher included (P18). With `FACTORY_IDLE_SHUTDOWN_MINUTES` set, the factory exits this way when idle (the script sets `FACTORY_IDLE_SHUTDOWN_ACTION=exit`; see *The idle shutdown*). A machine stop that stands for ten minutes ends it with status 1 instead, and the execution is marked failed. The next execution starts at the schedule, or when you run `gcloud run jobs execute <job>`.

### A free model

When the model costs nothing, a price of 0 makes `budget_usd` inert. The time limit of the stage is then the only bound on a run.

### Creating the job

`operator/job/job.sh` creates, updates, starts and deletes the job from the site file's values (*The site file* in [site.md](site.md)). It never guesses a project, a region or a job's name: every `gcloud` call carries `--project` from the file, every `gcloud run` call `--region` too (Cloud Logging has no region, so `logging read` does not take it), and `--impersonate-service-account` when `SITE_IMPERSONATE` is set.

```bash
sh operator/job/job.sh create [--dry-run]
sh operator/job/job.sh update [--dry-run]
sh operator/job/job.sh execute
sh operator/job/job.sh delete [--yes]
sh operator/job/job.sh log [N] [--execution NAME] [--quiet]
sh operator/job/job.sh status
```

`create` and `update` build one `gcloud run jobs` call with the settings of *What the job needs*: the image `docker.io/library/debian:trixie-slim`, `--execution-environment=gen2`, `--max-retries=0`, `--vpc-egress=all-traffic`, the two secrets as mounts (`/secrets/hosting-token` and `/secrets-llm/client-secret`, never their values) and the job's environment, which carries the proxy in its four spellings and sets no `PATH`. They read these keys; the meaning and the format of each are in the table of *The keys* in [site.md](site.md):

| Command | Keys it reads |
|---|---|
| `create`, `update` (required) | `SITE_PROJECT`, `SITE_REGION`, `SITE_RUN_AS`, `SITE_CONNECTOR`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_JOB`, `SITE_INSTANCE`, `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_HOSTING_SECRET`, `SITE_MODEL_SECRET`, `SITE_MODEL_BASE_URL`, `SITE_MODEL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID` |
| `create`, `update` (optional) | `SITE_IMPERSONATE` (none), `SITE_CPU` (`4`), `SITE_MEMORY` (`16Gi`), `SITE_TIMEOUT` (`86400`; seconds or a duration), `SITE_IDLE_MINUTES` (`30`), `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`) |
| `execute`, `delete`, `log`, `status` | `SITE_PROJECT`, `SITE_REGION`, `SITE_JOB` (and `SITE_IMPERSONATE` when set) |

Missing required keys are all named in one line, `site: missing <keys> in <path>`, with status 2 and no `gcloud` call.

Before it builds the call, `create` and `update` refuse three kinds of value, with `job: ...` on standard error, status 1 and no `gcloud` call:

- A `SITE_INSTANCE` with a character other than a letter, a digit, `.`, `_` or `-`. It becomes a path (`/srv/factory/<instance>`) in the shell text the job runs.
- An `@` in `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_MODEL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID` or `SITE_IDLE_MINUTES`. `@` is the delimiter of the job's env list (`--set-env-vars=^@^...`).
- A `SITE_MODEL_INPUT_COST` or `SITE_MODEL_OUTPUT_COST` that is not digits with at most one `.` (`15.5` and `.5` pass; `-1`, `1e3`, `nan` do not).

The second rule has a consequence: an SSH repository URL such as `git@host:owner/name.git` holds an `@`, so a job needs the `https://` form of `SITE_REPOSITORY_URL` (the factory itself accepts both, see *Configuration* in [install.md](install.md)).

The job's command is one line of shell that decodes a script (base64, gzip). The script only makes `/srv/factory/<instance>`, writes the provider file `provider.json` from the site's model values, writes `operator/vm/job-start.sh` to `/tmp/job-start.sh` and hands over to it (`exec sh /tmp/job-start.sh`). The text of `operator/vm/job-start.sh` is taken from `SITE_CODE_REF` of the repository that holds `job.sh`, not from its working tree, so the job runs the code the ref names. A ref the repository does not know stops `create` and `update` with `job: <ref> is not known here; fetch it first`, status 1. A `operator/vm/job-start.sh` that holds a line `JOB_START_SH_END` is refused, because that line ends the text in the wrapper.

`create` refuses a job that exists (`job: <job> exists; use update`) and `update` one that does not (`job: <job> does not exist; use create`), both with status 1. `--dry-run` runs no `gcloud` call, not even the check for the job: it prints the call, one argument per line, with the wrapper as `<wrapper: N bytes>`, so you can read it before it runs. A failing `gcloud` shows its standard error and `job.sh` exits with its status.

A first start goes in this order:

1. `site check`, to prove the site file and the machine (*Setting up an operator's machine* in [site.md](site.md)).
2. `sh operator/job/job.sh create`.
3. `sh operator/job/job.sh execute`.

`execute` starts an execution with `gcloud run jobs execute --async`, prints the execution's name and writes it to `${XDG_STATE_HOME:-$HOME/.local/state}/kumpel/last-execution`. It lists the job's executions first and, when one is running, refuses with `job: an execution of <job> is still running: <name>; two executions of one instance must not overlap` and status 1: the platform's role at a site may not cancel an execution, so the check comes before the start. `delete` without `--yes` prints `job: would delete <job> and stop its running execution; run again with --yes` and exits 1; with `--yes` it deletes the job without asking.

### Watching the job

Cloud Logging is how you see a job, and it has three habits that cost time: it arrives one to two minutes late, a failed query looks like an empty log unless the error is shown, and the factory's lines are mixed with the package manager's. Two commands of `job.sh` deal with that. Both need `SITE_PROJECT`, `SITE_REGION` and `SITE_JOB`, pass `--impersonate-service-account` when `SITE_IMPERSONATE` is set, and show a failing `gcloud` instead of swallowing it: `job: gcloud <what> failed: <first line of its standard error>` on standard error, status 1.

```bash
sh operator/job/job.sh log [N] [--execution NAME] [--quiet]
sh operator/job/job.sh status
```

**`log`** prints the last `N` lines (default 60) of one execution as `HH:MM:SS`, a tab and the text, in time order. Empty lines are dropped before they are counted, so `log 0` prints nothing. It reads the execution named by `--execution`, else the one in `last-execution` (written by `execute`), else the job's newest; with none it prints `job: no execution of <job> found` and exits 1. It reads at most 4000 lines of the last two days. `--quiet` also drops the package manager's noise: lines that start (after the time) with `Selecting `, `Preparing to unpack`, `Unpacking `, `Setting up `, `Get:`, `Fetched `, `Processing triggers`, `debconf:`, `Copying blob`, `Copying config` or `Writing manifest`, and lines that contain `token refreshed:`. When the answer is empty, `log` prints `job: no log lines yet; Cloud Logging arrives one to two minutes late` on standard error and exits 0: wait and ask again. A `--quiet` that leaves nothing prints nothing.

**`status`** prints the job's five newest executions, newest first, one line each:

```text
<name> <state> started <HH:MM> [ended <HH:MM>][: <message>]
```

The times are UTC. The state is `running` when the platform counts one or more running tasks, else `succeeded`, else `failed`, else `waiting`. A failed execution ends with the message of its first failed condition, the platform's own words for why. With no executions, `status` prints `job: no execution of <job> found` and exits 1.

Then it reads the log of the execution `log` would read (its last 200 non-empty lines) and prints one line about the factory:

- `factory: stopped: <line>`: the log holds a line of the factory's stop form, `stop <kind> <reason>: <detail>` (see *The stops* in [stops.md](stops.md)), and no `preflight:` line after it, which would show the factory running again. The line is the newest such stop. Read it as the stops are read, for instance `stop machine preflight_failed: tool:uv: uv is not on the PATH`.
- `factory: no stop in the last 200 lines`: nothing of that form, or the factory started again after it. A line that only contains the word `stop` (`job: stop requested by user`) does not count. A stop older than 200 lines is not seen; ask `log` for more.

`log` passes every line, and `status` the stop line it prints, through `operator/bin/sanitise` (*Sanitising what leaves the machine* in [site.md](site.md)), so the site's names and tokens are replaced. Without a rules file the built-in rules apply and the sanitiser's warning appears once on standard error. A wrong call (`N` not a number or negative, an unknown option) prints the usage line, which names every command, on standard error and exits 2.
