# The factory in a Cloud Run job

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md) who knows Linux and does not read the code. The factory's own words are explained in the [glossary](../project-guide/glossary.md).

## On Cloud Run

A Cloud Run job runs the factory without a VM. The job starts bare: its root file system is memory, nothing is installed and nothing persists. Every start therefore installs the tools, clones the code and builds the [stage](../project-guide/glossary.md) image again.

The job's command is [job-start.sh](../../operator/vm/job-start.sh), a POSIX `sh` script. It turns a bare `debian:trixie-slim` into a running instance and ends in `exec factory-run`. [job.sh](../../operator/job/job.sh) creates the job and puts that script in its command (see *Creating the job*).

Creating the job, its secrets and its schedule is yours. This chapter says what to give the job, what the script does with it, and how to watch it. The pieces the script uses are described in [machine.md](machine.md) under *The job profile*, *The metadata server in a job*, *Without ZFS* and *The idle shutdown*.

### What the job needs

Give the job these, in this order of importance.

1. **Memory.** The job gets 4 vCPUs and 16 GiB unless `SITE_CPU` and `SITE_MEMORY` say otherwise. Memory is the limit to raise first. The root file system is memory, and so is the tmpfs that holds the image layers. The checkout, the [base](../project-guide/glossary.md) and the workspace count against it too.
   - The stage image is about 2.4 GB. The job builds it without the layer cache and removes the build's untagged leftovers at once, so only the tagged stage image and its base stay.
   - The base is a plain copy (see *Without ZFS* in [machine.md](machine.md)), so the tree is held twice. A reset takes about 1.6 s per GiB.
2. **Time for a start.** A start takes a few minutes: the install, the clone and the image build.
3. **A task timeout below the schedule's interval.** The platform allows 24 hours at most, and that is the default (`SITE_TIMEOUT`, 86400 seconds). A job executed every night must set `SITE_TIMEOUT` below it, such as `23h`. Two executions of one job must never overlap, because both would act as the one instance.
4. **No retries.** Create the job with `--max-retries=0`. Otherwise a timeout starts a second execution at once. `job.sh` does this for you.
5. **The network through the proxy.** The job cannot resolve `github.com` itself. Git over HTTPS and the REST API are reached only through the proxy of the shared connector. The factory's own git and PyGithub read the job's `https_proxy`, so the job's environment must carry it. `NO_PROXY` must not name a GitHub host.
6. **Secrets as files.** Mount each secret with `--set-secrets` at a path, for example `--set-secrets=/secrets/token=<secret>:latest`, and name the path in the environment. See *The token's folder* below.
7. **The metadata server stays out of reach.** The script loads the rule that rejects TCP port 80 to `169.254.169.254`, so the service account's token cannot be read from inside a stage (see *The metadata server in a job* in [machine.md](machine.md)).

What does not work in a job:

- rootless containers;
- a bridge network;
- a pushed image, because there is no registry the factory can push to, so the job builds the image at each start;
- a second job that shares the disk;
- `fuse-overlayfs` for Podman's storage, which is three times slower.

#### The token's folder

The preflight's `token-file` item wants the hosting token's folder private, as on a VM: owned by the factory's user, which is root in a job, with no permission bit for group or others. A mounted secret's folder is read-only at mode `0555`, so give the mounted path as it is.

- When the token's folder is not private, the script copies the token to `<root>/secrets/hosting-token` (folder `0700`, file `0600`) and points `FACTORY_TOKEN_FILE` at the copy. It prints `job-start: token-file: copied to <root>/secrets`.
- A folder that is already private is used as it is, and nothing is copied.
- The original is not changed, and the token's text is never printed.

If the copy fails, the script stops with `job-start: token-file: failed` and status 1.

### The environment

The job's environment is the instance's configuration. The script reads the variables below. When a required one is missing, it stops before anything else runs, prints `job-start: <name> is not set` and exits with status 2.

| Name | What it does | Default | Example |
| --- | --- | --- | --- |
| `FACTORY_INSTANCE` | The instance's name. Required. | none | `kumpel` |
| `FACTORY_REPOSITORY_URL` | The project. Required. | none | `https://github.com/owner/name.git` |
| `FACTORY_CODE_URL` | The repository that holds the factory's code and `operator/vm/Dockerfile`. It is cloned without a credential (see *The code and the project apart* in [machine.md](machine.md)). Required. | none | `https://github.com/owner/factory.git` |
| `FACTORY_CODE_REF` | A tag or a commit of the code repository. It has no default, so nothing pushed to the code's `main` reaches a job unseen: you move the ref on purpose. Required. | none | `v1.2.0` |
| `FACTORY_TOKEN_FILE` | The path of the file that holds the hosting token. It must be a file the script can read, else `job-start: FACTORY_TOKEN_FILE is not a file` and status 2. The script never prints it. Required. | none | `/secrets/hosting-token` |
| `HTTPS_PROXY` or `https_proxy` | The proxy for `apt` and every download. `HTTPS_PROXY` wins when both are given and not empty. The script exports `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY` and `http_proxy` to every later step, because the stage image's package manager fetches over plain HTTP. An `HTTP_PROXY` or `http_proxy` that the job sets to a value that is not empty keeps its own value. Optional. | none | `http://proxy.internal:3128` |
| `FACTORY_JOB_ROOT` | The folder of everything the script makes. | `/srv/factory/<instance>` | `/srv/factory/kumpel` |
| `FACTORY_STAGE_IMAGE` | The name of the stage image the job builds. | `factory-stage:<instance>` | `factory-stage:kumpel` |
| `RUNC_VERSION`, `RUNC_SHA256` | The `runc` release and its checksum. Give both or neither: a version without its checksum would not be checked, so `RUNC_VERSION` alone stops with `job-start: RUNC_SHA256 is not set` and status 2. | `1.5.2` and its checksum, both set in the script | `1.5.2` |
| `FACTORY_TOKEN_URL` and its companions | When set, the token refresher runs (see *A bearer token for the model API* in [agent-runtime.md](agent-runtime.md)). | unset | none |
| `FACTORY_IDLE_SHUTDOWN_MINUTES` | Minutes of idleness after which the factory exits (see *Starts, restarts and the end of an execution*). Unset means no idle shutdown. | unset | `30` |
| `FACTORY_TRANSCRIPT_DIR` | The transcript folder (see *Transcripts*, *In a Cloud Run job* in [health.md](health.md)). When set, the script checks that the folder exists and that a file can be made and removed in it. If not, it stops with `job-start: transcript folder <path> cannot be written` and status 1. | unset | `/transcripts` |
| `FACTORY_JOB_PREFIX` | Put in front of `/etc`, `/usr/local/bin` and `/var/lib/containers`, for the script's own tests. Leave it unset. | unset | none |

Beside these the job carries the settings of any instance: the hosting token's companions, the agent runtime's login, `FACTORY_CONTAINER_ENV`, `FACTORY_CA_BUNDLE` and `FACTORY_OPENCODE_MODELS`. The script never changes those.

#### What the script sets

The script sets the following only where the job gave no value:

| Name | Value |
| --- | --- |
| `FACTORY_SNAPSHOTS` | `copy` |
| `FACTORY_SNAPSHOT_BASE` | `<root>/base` |
| `FACTORY_WORKSPACE` | `<root>/work` |
| `FACTORY_CHECKOUT` | `<root>/repo` |
| `FACTORY_STATE` | `<root>/state` |
| `FACTORY_CLAUDE_HOME` | `<root>/factory/agents` |
| `FACTORY_IMAGE_ID_FILE` | `<root>/image-id` |
| `FACTORY_CONTAINER_PROFILE` | `job` |
| `FACTORY_AGENT_RUNTIME` | `opencode` |
| `FACTORY_IDLE_SHUTDOWN_ACTION` | `exit` |

It also sets `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION` from the lines `ARG CLAUDE_CODE_VERSION=` and `ARG OPENCODE_VERSION=` of the cloned `operator/vm/Dockerfile`. The preflight's item `agent-runtime-version` compares them with the stage image.

To see the script refuse a missing variable, run it with an empty environment. This is safe: it stops before it changes anything.

```console
$ env -i PATH="$PATH" sh operator/vm/job-start.sh; echo "status $?"
job-start: FACTORY_INSTANCE is not set
status 2
```

### The steps

The checks of the required variables, the token file and `RUNC_SHA256` come before the first step line. After them the script prints `job-start: <step>` on standard output at each step, in this order.

1. `inputs`: derives the other settings. It copies a token whose folder is not private, and checks the transcript folder when `FACTORY_TRANSCRIPT_DIR` is set (that check prints no step line of its own). Then `PATH` becomes `<root>/tools/bin` followed by the `PATH` the script started with, so the preflight finds `uv` and the factory's commands that the `tools` step builds there.
2. `proxy`: with a proxy set, exports the four spellings and writes `/etc/apt/apt.conf.d/99proxy`.
3. `packages`: runs `apt-get update`, then one `apt-get install` of `podman`, `uidmap`, `nftables`, `git`, `make`, `curl`, `ca-certificates`, `rsync`, `python3` and `python3-venv`, at the versions of the Debian release.
4. `runc`: downloads `runc.amd64` of the release, checks it with `sha256sum -c` against the script's own checksum, and installs it as `/usr/local/bin/runc`. A mismatch stops with `job-start: runc: checksum does not match` and status 1. A checksum downloaded beside the binary would check nothing, so there is none. The download folder is removed whenever the step ends.
5. `metadata`: loads the `nft` rule of *The metadata server in a job* in [machine.md](machine.md) from `<root>/metadata-block.nft`.
6. `directories`: makes the workspace, the empty base, the checkout and the state folder.
7. `storage`: mounts a tmpfs at `/var/lib/containers`, Podman's storage root, so that images use the kernel's overlay. A failed mount stops with `job-start: storage: cannot mount a tmpfs at <path>` and status 1.
8. `code`: clones `FACTORY_CODE_URL` and checks out `FACTORY_CODE_REF`, with no credential and no prompt. A ref that does not exist stops with `job-start: code: no ref <ref> in <url>` and status 1.
   - Then it installs the checkout's own `operator/vm/git-credential-factory` as `/usr/local/bin/git-credential-factory` with mode `0755`. A failing install stops with `job-start: code: failed` and status 1.
   - The factory's git takes its credential only from that helper, which answers for the project's host only. Without it no fetch of a private project and no push could authenticate (see *The hosting-service token* in [health.md](health.md)). `operator/vm/setup.sh` installs the same helper on a VM.
9. `tools`: makes a virtual environment `<root>/tools` with `uv` at the version of `operator/vm/Dockerfile`, then runs `uv sync --frozen --no-dev` in the code checkout.
10. `image`: builds the stage image from the checkout's `operator/vm/Dockerfile` with the job's Podman options (the three words of *The job profile* in [machine.md](machine.md)). It then writes a new uuid to the image-id file.
11. `token`: when `FACTORY_TOKEN_URL` is set, runs the refresher once and waits for it, which must succeed, then starts it in the background.
12. `start`: runs `exec factory-run` of the code checkout's environment.

Any other failing step stops the script with `job-start: <step>: failed` on standard error and status 1. `factory-run` is not started. The job's log shows the last step printed, followed by its failure line.

### Starts, restarts and the end of an execution

A start or a restart takes a few minutes, because the checkout, the base and the image are rebuilt. The state folder goes with the memory, so the factory log, `health.json` and the preflight stamp start empty, and the preflight runs at every start.

A restart during a stage is a [crash](../project-guide/glossary.md) for the factory (see *A restart during a stage* in [work-items.md](work-items.md)). Recovery charges one crash to the stage in flight. After `crash_cap` crashes, two by default, the [work item](../project-guide/glossary.md) waits for your answer. A [story](../project-guide/glossary.md) in flight on two nights therefore waits once.

How an execution ends:

- **At the timeout** the platform sends `SIGTERM` to `factory-run` with no warning before it. The factory ends after the [tick](../project-guide/glossary.md) in progress. The platform marks the execution failed with `The configured timeout was reached`, even when the exit status is 0. A nightly timeout is planned and is not a fault.
- **When `factory-run` exits with status 0** the execution ends as succeeded at once, background processes such as the refresher included. With `FACTORY_IDLE_SHUTDOWN_MINUTES` set, the factory exits this way when idle, because the script sets `FACTORY_IDLE_SHUTDOWN_ACTION=exit` (see *The idle shutdown* in [machine.md](machine.md)).
- **With `FACTORY_IDLE_SHUTDOWN_MINUTES` set, a [stop](../project-guide/glossary.md) of the machine that stands for ten minutes** ends the execution with status 1, and the platform marks it failed (see *The idle shutdown* in [machine.md](machine.md)).

The next execution starts at the schedule, or when you run `sh operator/job/job.sh execute`.

#### A free model

When the model costs nothing, a price of 0 makes `budget_usd` inert. The time limit of the stage is then the only bound on a run.

### Creating the job

[job.sh](../../operator/job/job.sh) creates, updates, starts and deletes the job from the site file's values (see *The site file* in [site.md](site.md)). It never guesses a project, a region or a job's name. Every `gcloud` call carries `--project` from the file. Every `gcloud run` call carries `--region` too. `logging read` does not, because Cloud Logging has no region. When `SITE_IMPERSONATE` is set, every call carries `--impersonate-service-account`.

These commands run on your own machine, with the site file in place and `gcloud` logged in:

```sh
sh operator/job/job.sh create [--dry-run]
sh operator/job/job.sh update [--dry-run]
sh operator/job/job.sh execute
sh operator/job/job.sh delete [--yes]
sh operator/job/job.sh log [N] [--execution NAME] [--quiet]
sh operator/job/job.sh status
```

A wrong call (an unknown command or option) prints the usage line, which names every command, on standard error and exits 2:

```console
$ sh operator/job/job.sh bogus; echo "status $?"
usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes] | log [N] [--execution NAME] [--quiet] | status
status 2
```

A first start goes in this order:

1. Prove the site file and the machine with `site check` (see *Setting up an operator's machine* in [site.md](site.md)).
2. Create the job. On your machine, run:

   ```sh
   sh operator/job/job.sh create
   ```

3. Start an execution. On your machine, run:

   ```sh
   sh operator/job/job.sh execute
   ```

`create` and `update` build one `gcloud run jobs` call with the settings of *What the job needs*:

- the image `docker.io/library/debian:trixie-slim`, `--execution-environment=gen2`, `--max-retries=0` and `--vpc-egress=all-traffic`;
- the two secrets as mounts, `/secrets/hosting-token` and `/secrets-llm/client-secret`, never their values;
- the job's environment, which carries the proxy in its four spellings and sets no `PATH`.

The meaning and the format of each key are in the table of *The keys* in [site.md](site.md). The commands read these:

| Command | Keys it reads |
| --- | --- |
| `create`, `update` (required) | `SITE_PROJECT`, `SITE_REGION`, `SITE_RUN_AS`, `SITE_CONNECTOR`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_JOB`, `SITE_INSTANCE`, `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_HOSTING_SECRET`, `SITE_MODEL_SECRET`, `SITE_MODEL_BASE_URL`, `SITE_MODEL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID` |
| `create`, `update` (optional) | `SITE_IMPERSONATE` (none), `SITE_CPU` (`4`), `SITE_MEMORY` (`16Gi`), `SITE_TIMEOUT` (`86400`; seconds or a duration), `SITE_IDLE_MINUTES` (`30`), `SITE_MODEL_INPUT_COST` and `SITE_MODEL_OUTPUT_COST` (`0`) |
| `execute`, `delete`, `log`, `status` | `SITE_PROJECT`, `SITE_REGION`, `SITE_JOB`, and `SITE_IMPERSONATE` when set |

Missing required keys are all named in one line, `site: missing <keys> in <path>`, with status 2 and no `gcloud` call.

#### What `create` and `update` refuse

Before they build the call, `create` and `update` refuse three kinds of value. Each prints `job: ...` on standard error, exits with status 1 and makes no `gcloud` call.

- A `SITE_INSTANCE` with a character other than a letter, a digit, `.`, `_` or `-`. The name becomes a path, `/srv/factory/<instance>`, in the shell text the job runs.
- An `@` in `SITE_REPOSITORY_URL`, `SITE_CODE_URL`, `SITE_CODE_REF`, `SITE_PROXY`, `SITE_NO_PROXY`, `SITE_MODEL`, `SITE_LOGIN_URL`, `SITE_LOGIN_SCOPE`, `SITE_LOGIN_CLIENT_ID` or `SITE_IDLE_MINUTES`. The `@` is the delimiter of the job's env list, `--set-env-vars=^@^...`.
- A `SITE_MODEL_INPUT_COST` or `SITE_MODEL_OUTPUT_COST` that is not digits with at most one `.`. The values `15.5` and `.5` pass; `-1`, `1e3` and `nan` do not.

The second rule has a consequence. An SSH repository URL such as `git@host:owner/name.git` holds an `@`, so a job needs the `https://` form of `SITE_REPOSITORY_URL`. The factory itself accepts both (see *Configuration* in [install.md](install.md)).

#### The job's command

The job's command is one line of shell that decodes a script (base64, gzip). The script does four things:

1. It makes `/srv/factory/<instance>`.
2. It writes the provider file `provider.json` from the site's model values.
3. It writes `operator/vm/job-start.sh` to `/tmp/job-start.sh`.
4. It hands over to that file with `exec sh /tmp/job-start.sh`.

The text of `operator/vm/job-start.sh` is taken from `SITE_CODE_REF` of the repository that holds `job.sh`, not from its working tree, so the job runs the code the ref names. A ref the repository does not know stops `create` and `update` with `job: <ref> is not known here; fetch it first` and status 1. A `operator/vm/job-start.sh` that holds a line `JOB_START_SH_END` is refused with `job: operator/vm/job-start.sh holds the line JOB_START_SH_END; the wrapper cannot carry it` and status 1, because that line ends the text in the wrapper.

#### Create, update, start, delete

- `create` refuses a job that exists: `job: <job> exists; use update`. `update` refuses one that does not: `job: <job> does not exist; use create`. Both exit with status 1.
- `--dry-run` runs no `gcloud` call, not even the check for the job. It prints the call, one argument per line, with the wrapper as `<wrapper: N bytes>`, so you can read it before it runs.
- A failing `gcloud` shows its standard error, and `job.sh` exits with its status.
- `execute` starts an execution with `gcloud run jobs execute --async`, prints the execution's name and writes it to `${XDG_STATE_HOME:-$HOME/.local/state}/kumpel/last-execution`.
- `execute` lists the job's executions first. When one is running, it refuses with `job: an execution of <job> is still running: <name>; two executions of one instance must not overlap` and status 1. The check comes before the start because the platform's role at a site may not cancel an execution.
- `delete` without `--yes` prints `job: would delete <job> and stop its running execution; run again with --yes` and exits 1. With `--yes` it deletes the job without asking.

### Watching the job

Cloud Logging is how you see a job. It has three habits that cost time. It arrives one to two minutes late. A failed query looks like an empty log unless the error is shown. The factory's lines are mixed with the package manager's. Two commands of `job.sh` deal with that.

```sh
sh operator/job/job.sh log [N] [--execution NAME] [--quiet]
sh operator/job/job.sh status
```

Both need `SITE_PROJECT`, `SITE_REGION` and `SITE_JOB`, and pass `--impersonate-service-account` when `SITE_IMPERSONATE` is set. Both show a failing `gcloud` instead of swallowing it: `job: gcloud <what> failed: <first line of its standard error>` on standard error, and status 1.

`log` and `status` pass what they print through `operator/bin/sanitise` (see *Sanitising what leaves the machine* in [site.md](site.md)), so the site's names and tokens are replaced. Without a rules file the built-in rules apply, and the sanitiser's warning appears once on standard error.

#### `log`

`log` prints the last `N` lines of one execution, 60 by default. Each line is `HH:MM:SS`, a tab and the text, in time order. Empty lines are dropped before they are counted, so `log 0` prints nothing.

It reads the execution named by `--execution`, else the one in `last-execution` (written by `execute`), else the job's newest. With none, it prints `job: no execution of <job> found` and exits 1. It reads at most 4000 lines of the last two days.

`--quiet` also drops the package manager's noise. That means lines that start, after the time, with one of the texts in *Reference*, and lines that contain `token refreshed:`.

When the answer is empty, `log` prints `job: no log lines yet; Cloud Logging arrives one to two minutes late` on standard error and exits 0. Wait and ask again. A `--quiet` that leaves nothing prints nothing.

#### `status`

`status` prints the job's five newest executions, newest first, one line each:

```text
<name> <state> started <HH:MM> [ended <HH:MM>][: <message>]
```

- The times are UTC.
- The state is `running` when the platform counts one or more running tasks, else `succeeded`, else `failed`, else `waiting`.
- A failed execution ends with the message of its first failed condition, the platform's own words for why.
- With no executions, `status` prints `job: no execution of <job> found` and exits 1.

Then it reads the log of the execution `log` would read, its last 200 non-empty lines, and prints one line about the factory:

- `factory: stopped: <line>` means the log holds a line of the factory's stop form, `stop <kind> <reason>: <detail>`, and no `preflight:` line after it. A `preflight:` line would show the factory running again. The line shown is the newest such stop. Read it as the stops are read (see *The stops* in [stops.md](stops.md)), for instance `stop machine preflight_failed: tool:uv: uv is not on the PATH`.
- `factory: no stop in the last 200 lines` means nothing of that form, or the factory started again after it. A line that only contains the word `stop`, such as `job: stop requested by user`, does not count. A stop older than 200 lines is not seen; ask `log` for more.

A wrong call to `log` or `status` (an `N` that is not a number or is negative, an unknown option) prints the usage line and exits 2.

## Reference

### Exit statuses and messages of `job-start.sh`

| Message | Status | When |
| --- | --- | --- |
| `job-start: <name> is not set` | 2 | A required variable is missing, or `RUNC_VERSION` is set without `RUNC_SHA256`. |
| `job-start: FACTORY_TOKEN_FILE is not a file` | 2 | The token path is not a readable file. |
| `job-start: token-file: failed` | 1 | The copy of the token failed. |
| `job-start: transcript folder <path> cannot be written` | 1 | `FACTORY_TRANSCRIPT_DIR` is not a writable folder. |
| `job-start: runc: checksum does not match` | 1 | The downloaded `runc` differs from the script's checksum. |
| `job-start: storage: cannot mount a tmpfs at <path>` | 1 | The mount of Podman's storage failed. |
| `job-start: code: no ref <ref> in <url>` | 1 | The code repository has no such ref. |
| `job-start: <step>: failed` | 1 | Any other failing step. |

### Texts that `log --quiet` drops

Lines that start, after the time, with `Selecting `, `Preparing to unpack`, `Unpacking `, `Setting up `, `Get:`, `Fetched `, `Processing triggers`, `debconf:`, `Copying blob`, `Copying config` or `Writing manifest`, and lines that contain `token refreshed:`.

### Messages of `job.sh`

| Message | Status | When |
| --- | --- | --- |
| `usage: job.sh create [--dry-run] \| update [--dry-run] \| execute \| delete [--yes] \| log [N] [--execution NAME] [--quiet] \| status` | 2 | A wrong call. |
| `site: missing <keys> in <path>` | 2 | Required site keys are missing. |
| `job: SITE_INSTANCE may hold only letters, digits, '.', '_' and '-'` | 1 | `create` or `update` refuses the instance name. |
| `job: <name> holds '@', the delimiter of the job's env list` | 1 | `create` or `update` refuses a value with `@`. |
| `job: <name> is not a number` | 1 | `create` or `update` refuses a model cost. |
| `job: <ref> is not known here; fetch it first` | 1 | `SITE_CODE_REF` is not in the local repository. |
| `job: operator/vm/job-start.sh holds the line JOB_START_SH_END; the wrapper cannot carry it` | 1 | The script holds the line that ends it in the wrapper. |
| `job: <job> exists; use update` | 1 | `create` on an existing job. |
| `job: <job> does not exist; use create` | 1 | `update` on a missing job. |
| `job: an execution of <job> is still running: <name>; two executions of one instance must not overlap` | 1 | `execute` while one runs. |
| `job: would delete <job> and stop its running execution; run again with --yes` | 1 | `delete` without `--yes`. |
| `job: no execution of <job> found` | 1 | `log` or `status` with no execution. |
| `job: no log lines yet; Cloud Logging arrives one to two minutes late` | 0 | `log` found nothing. |
| `job: gcloud <what> failed: <first line of its standard error>` | 1 | `log` or `status` met a failing `gcloud`. |
