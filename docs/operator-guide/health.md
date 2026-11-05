# Health, logs and transcripts

A topic of the [operator guide](README.md).

## The preflight and the health check

### The hosting-service token

The token lives in one file on the VM, `/home/factory/.secrets/hosting-token`, which you place by hand (see "The machine" in [machine.md](machine.md)); the environment file sets `FACTORY_TOKEN_FILE` to that path. `vm/setup.sh` makes the folder `/home/factory/.secrets` as `factory:factory`, mode `0700`: only the factory's user can enter it, whatever the file's own mode. A stage container never mounts the token (only the host fetches and pushes), so the agent has no path to it.

Only two things read the file: the factory process, once, to hand the token to PyGithub, and git's credential helper, `/usr/local/bin/git-credential-factory`. The helper answers git's `get` with the user name `x-access-token` and the file's content as the password. If `FACTORY_TOKEN_FILE` is unset or the file cannot be read, it prints nothing and exits 1, so a process that cannot read the file gets no credential. With `FACTORY_REPOSITORY_URL` set (the environment file sets it), the helper also answers only a request whose `host=` line names the host of that URL, compared in lower case with user and port removed from both (`https://[user@]host[:port]/...`, `ssh://[user@]host[:port]/...` and `[user@]host:path` all work); another host, and a request without a `host=` line, get nothing and exit 1. With the variable unset the helper behaves as before. For `store`, `erase` and any other operation it prints nothing and exits 0. The factory's git reaches the helper only through the environment the factory gives it, so the agent's git has no credential. `vm/setup.sh` installs the helper from `vm/git-credential-factory` (step `tools`, see "The machine" in [machine.md](machine.md)).

An agent run's environment is an allow list of six names: `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`. The factory builds `PATH` and `HOME` itself and takes the other four from its own environment when it has them. Everything else the factory process holds (`FACTORY_TOKEN_FILE`, `GH_TOKEN`, `GITHUB_TOKEN`, `GIT_ASKPASS`, `SSH_AUTH_SOCK`, any variable of yours) is dropped at the source and never reaches an agent. The factory's own pushes and posts are not affected.

The preflight item `token-file` (see "The preflight's items") checks that the token file exists and that its folder belongs to the factory's user and has no permission bit for group or others. The file's own owner and mode do not count, because a bind mount shows the host's. Its detail is `<path>: <fault>`, with the fault:

- `no token file is set`: `FACTORY_TOKEN_FILE` is unset. Set it (the environment file does, see "The service" in [machine.md](machine.md)) and start the instance again.
- `the token file does not exist`: the folder or the file is missing. Place the token in `/home/factory/.secrets/hosting-token` (see "The machine" in [machine.md](machine.md)), or correct the path `FACTORY_TOKEN_FILE` names.
- `the folder <folder> belongs to uid <n>, not to <m>`: the folder is not the factory's user's. Use `/home/factory/.secrets`, or `chown` your folder to that user.
- `the folder <folder> has mode <mode>; make it 0700`: `chmod 0700` the folder, or use `/home/factory/.secrets`.

The folder is checked first, so a folder the factory's user does not own is reported even when it cannot enter it.

**The project commands.** Every project command (`make check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, and the preflight's `lint` on `main`) runs in a check container on the dataset.


### The health check

`factory-health` reads `health.json` in the state directory, `/state` unless `--state-directory <path>` names another (on the VM, the directory `FACTORY_STATE` names; "The service" in [machine.md](machine.md) shows the command). With no stop it prints `healthy` and exits 0; when the file is missing it prints `no health status: <path> is missing` and exits 1 (`factory-run` writes an empty status when it starts, so a missing file means the instance has not started or the check reads another state directory); with stops it prints one line per stop and exits 1:

```
preflight_failed (machine): tool:uv: uv is not on the PATH; add it to the image (since 2026-10-12T08:00:00Z)
```

The status reads healthy again by itself when the factory clears the stop. A stop of a work item is not in the health status. The stops the health status can show are in "The stops" in [stops.md](stops.md), with what to do about each.

Nothing runs the check by itself, and the factory builds no watchdog: systemd restarts a process that has died (`Restart=always`, see "The service" in [machine.md](machine.md)).

### The preflight's items

The preflight is a list of five items, and of up to thirteen with the machine's extras (`token-file`, `podman`, `zfs`, `dataset` (under `FACTORY_SNAPSHOTS=copy`, the one item `snapshots` in their place), `stage-image`, `metadata-block` under the profile `job` only, `opencode` under opencode only, and `agent-run-probe`), in the order of the table. Every item runs whatever the others found, so one report names everything that is wrong. A failed report becomes one `preflight_failed` stop with scope `machine`; its detail lists each failed item as `<name>: <detail>`, joined by `; `. The preflight installs nothing: a missing tool is reported and you fix the image. The items run only when the image build has changed (see "The stamp and the probe of the main branch").

| Item | Passes when | If it fails |
|---|---|---|
| `tool:git`, `tool:uv` | the tool is on the `PATH` | The detail is `<tool> is not on the PATH; add it to the image`, as the code prints it, though the tools are on the VM, not in the image. Install the tool on the VM (`vm/setup.sh` installs `uv` into `/srv/factory/<instance>/tools`, and `git` comes with its package step) and restart the instance. |
| `hosting-service` | a read-only call (the open pull request of `main`) is answered | The detail holds the operation and the service's message. Check the token (`FACTORY_TOKEN_FILE`) and the network. |
| `agents` | at least one agent file is in `FACTORY_CLAUDE_HOME` (`<it>/agents/<role>.md`) | The detail names the directory, whether it is empty, missing or unreadable. Install the agents into `FACTORY_CLAUDE_HOME`. |
| `agent-runtime-version` | the first word of the runtime's `--version` equals the pin of the runtime in force (`FACTORY_CLAUDE_VERSION`; under opencode `FACTORY_OPENCODE_VERSION`) | The detail names both versions (`the agent runtime reports 2.1.290, the image pins 2.1.289`): rebuild the image or change the pinned version. Without the pin it says `the image does not pin a version: FACTORY_CLAUDE_VERSION is not set` (`FACTORY_OPENCODE_VERSION` under opencode); when `claude --version` cannot run, it holds the runtime's error. |
| `token-file` | `FACTORY_TOKEN_FILE` names a file that exists, in a folder that belongs to the factory's user and has no permission bit for group or others (the file's own mode does not count) | The detail is `<path>: <fault>`; see "The hosting-service token" for the four faults and the fix. |
| `opencode` | under opencode only: `FACTORY_OPENCODE_MODELS` maps every alias the installed agents use. No executable is looked for, since it is the stage image's and `agent-runtime-version` runs it there | `no model is set for <alias> in FACTORY_OPENCODE_MODELS`: add `<alias>=<provider>/<model>`. The item asks for no API key: see "Running on opencode" in [agent-runtime.md](agent-runtime.md). |
| `podman` | `podman --version` answers; the detail is its first line (`podman version 4.9.3`), which the factory log names once per image build | The detail is `podman does not answer --version: <the error>`. Install `podman` where the factory runs, or correct `FACTORY_PODMAN`. |
| `zfs` | `zfs --version` answers; the detail is its first line | The detail is `zfs does not answer --version: <the error>`. Install ZFS, or correct `FACTORY_ZFS`. |
| `dataset` | `zfs list -H -o name <dataset>` names `FACTORY_DATASET` | `the dataset <dataset> does not exist; make it with zfs create, and its base with zfs snapshot <dataset>@base`: do that, once. An instance made by `vm/setup.sh` has both already (step 5); the message concerns a dataset made by hand. When `zfs list` itself fails, the detail is `cannot list the dataset <dataset>: <the error>` (for example a permission the factory's user lacks). |
| `snapshots` | with `FACTORY_SNAPSHOTS=copy` only, in place of `zfs` and `dataset`: the workspace and the base are directories; the detail is `workspace <w>, base <b>` | `the workspace <w> is not a directory`, `the base <b> does not exist; make it empty with mkdir, the first advance fills it` or `the base <b> is not a directory`. |
| `stage-image` | `podman image exists <FACTORY_STAGE_IMAGE>` answers yes | `the stage image <image> is not built; build it with podman build`. When podman cannot answer, the detail is `cannot look for the stage image <image>: <the error>`. |
| `metadata-block` | with `FACTORY_CONTAINER_PROFILE=job` only: a container's request to the metadata server is refused (curl prints `000`); the detail is `refused` | See "The metadata server in a job" in [machine.md](machine.md): the sentences are there, and so is the rule to load. |
| `agent-run-probe` | one `claude -p` call, or one `opencode run` call under opencode, made as a stage makes it, ends `completed` | See "The probe of the agent run" below. |

The preflight asks for no `make`, no `claude` and no `opencode` on the factory's `PATH`: the runtime and `make` run only inside the stage image's containers, and `agent-runtime-version` fails when the runtime is missing there.

#### The probe of the agent run

`agent-run-probe` runs the agent runtime once, with the factory's own arguments: the project's agent `coder` (`factory/agents/coder.md` on `origin/main`) or the installed one, a budget of 0.10 dollar, a fixed one-line prompt, the decision `question` only, a time limit of 2 minutes, with the agent run's environment. The probe takes nothing from the dataset after the run, so nothing it writes reaches the checkout. The dataset is prepared for `main` first, as a stage's is (the sync container runs on `origin/main` and the base moves), so the run starts on a clean copy; two faults are added: `no origin/main to prepare the stage environment from` (the clone has no `main`: nothing is run), and the message of the snapshot or container command that failed, such as `snapshot command zfs rollback -r <dataset>@base failed: cannot open '<dataset>@base': dataset does not exist` (with ZFS: the dataset has no base; `vm/setup.sh` makes the first one, and for a dataset made by hand run `zfs snapshot <dataset>@base`) or `snapshot command reset failed: no base at <path>` (with `FACTORY_SNAPSHOTS=copy`: the base directory is missing; make it empty with `mkdir`) or `container command sync failed: <last output line>` (`make sync` failed in the sync container). It costs a few cents. Like the other machine items it runs once for each image build and is skipped while the image is unchanged.

It fails with `the probe run ended <reason>; run claude -p by hand as the factory user to see why` (under opencode `run <executable> run by hand as the factory user to see why`, with no token hint) when the run does not end `completed`. When `FACTORY_CLAUDE_LOGIN_FILE` is set, the detail ends with `; the agent's login token is read from <file>: make it with claude setup-token if it is missing, empty or expired`. When the probe ran with the API key, the detail ends instead with `; the agent's API key is read from <file>: check that it is valid and that its account has credit`. A login file that cannot be read or is not ASCII text fails the item with the runtime's message, `cannot read the agent's login file <file>: ...`, or `cannot read the agent's API login file <file>: ...` for the API key. The usual causes are a flag the pinned `claude` rejects (every real run would end `died`, each with its line `run <run id> of <work item> (<stage>) died: <text>` in the factory log), a login missing for the factory user (a missing or expired token when the detail names the login file; otherwise log in as that user and keep the login in its `HOME`), and a run that ran out of its budget or time. A state directory that cannot be written fails it with the runtime's own message, and a missing agent `coder` fails it with the reader's message naming the agent. All of these stop the machine before any work item is claimed.

Under opencode a failed probe whose login was `none` ends with `; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names`. No login kept in the agent's home is advised, because the rollback clears it (see "Running on opencode" in [agent-runtime.md](agent-runtime.md)).

When the probe completes, the item passes and the factory log gets one line with its detail, which names the login in force: `the agent runs log in with the API key from <file>`, `the agent runs log in with the subscription token from <file>`, or, when a login file is named but holds no login (missing or blank), `the agent runs get no login from a file; the runtime uses the login kept in its home` under Claude Code and `the agent runs get no login from a file` under opencode (a provider whose key comes through `FACTORY_CONTAINER_ENV` passes this way). With no login file set at all, the detail is empty.

The items read the instance's settings, so the three variables `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION` are the ones to check first; under opencode, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`. The commit identity is not an item.

The detail of `preflight_failed` also takes a form that is no item: `the probe on main could not run: <message>` means the probe of the main branch (see "The stamp and the probe of the main branch") itself failed, because git or `make` could not run or the checkout is gone: fix the machine, not `main`. The message may also be a snapshot or container command that failed while the dataset was prepared for `main`, for example `the probe on main could not run: container command sync failed: boom` or `the probe on main could not run: snapshot command reset failed: no base at <path>`.

### The stamp and the probe of the main branch

`Preflight.run` remembers what it has passed in `preflight-stamp.json` in the state directory: the image identity the machine's items passed on, and the commit of `origin/main` whose `lint` passed or failed. The stamp holds no time and no timer expires it.

- **The machine's items** run when the stamp's image differs from the instance's image identity, when there is no stamp, and on every call when the instance has no image identity. While the image build is unchanged they are skipped, however much time passes. A failed report writes no stamp, so the items run again at the next call.
- **The probe** runs the project's `lint` command with a `time_limit` of 10 minutes, on the main branch only: it puts the checkout on `main` at `origin/main` first, and prepares the dataset for that commit before `lint` runs in a check container. A red `lint` on a work item's branch never fails the preflight. The probe runs only when `origin/main` is a commit the stamp has not seen, and after a new image build (a new build forgets what was probed). The preflight does not fetch; the tick that calls it does.
- **A red `lint` is a stop.** The probe raises `main_branch_failing` with the detail `lint is red on main at <12 characters of the commit>: <last line of the output>` (when `lint` printed nothing, the last line is replaced by how it ended: `lint ended with exit status <n> and printed nothing on main at <commit>`, or `ended by signal <n>`), or `lint reached its time_limit on main at <commit>` when `lint` ran out of its time.
- **A red `main` is probed once.** The failing commit is remembered, so an idle tick runs no project command while the stop stands. If `health.json` loses the stop meanwhile, the next call raises it again with the detail `lint is red on main at <commit> (probed earlier)`, without running `lint`.
- **A probe cut off by the factory's own stop is not judged.** When `factory-run` is asked to stop (SIGTERM from `systemctl stop` or `restart`) while the probe's `lint` runs, the probe raises no stop, writes no stamp and records nothing as failed, and its tick ends without claiming or dispatching any work. The next start probes `main` again. A `lint` ended by signal 15 while the factory is not stopping (an out-of-memory kill, for example) is judged: it raises `main_branch_failing` with the detail above. Only the probe of `main` follows this rule; a stage's checks cut off by a stop end in a crash and a rerun.
- **A fix clears it.** When you push a new commit to `main`, the next call probes it, and when `lint` passes the stop `main_branch_failing` is cleared. A call that ends without a probe error also clears a standing `preflight_failed` stop.
- **A failed machine clears a stale stop.** While the machine's items fail the probe cannot run, so a `main_branch_failing` is cleared when the stamp's failing commit is no longer `origin/main` (a fix was pushed, or `main` is gone) and the call still returns `preflight_failed`. The new `main` is probed when the machine's items pass again, and a red one raises the stop anew. A stop whose commit is still `main` stays, and so does a stop when git cannot resolve `origin/main`. The exception is a `main` that differs from the failing commit only in `factory/stops.jsonl`: see the next bullet. If git cannot compare the two (the failing commit is not in the clone), the stop is cleared. The stamp is not rewritten.
- **A `stops recorded` commit is a new `main`.** The probe runs again for it once the machine's items pass. While they fail (`preflight_failed` stands), the stale-stop rule above keeps `main_branch_failing` when every path that differs between the stamp's failing commit and the checkout is `factory/stops.jsonl`, so no `cleared` record is written for a `main` nobody fixed. A commit that also changes another file clears the stop.
- A repository with no commit on `main` has nothing to probe, and the preflight passes once the machine's items have.

Deleting `preflight-stamp.json` is safe: a missing or damaged stamp reads as no stamp, and the only cost is one more run of the machine's items and of the probe. The agent can read the file and cannot write it.

### The wait for a repository that is not ready

Before each tick the instance checks that `origin/main` exists and holds `factory/pipeline.yml`. When it does, nothing is fetched here (the tick fetches) and any `repository_unavailable` stop is cleared. When it does not, the instance fetches once, looks again, and if the fault stays it raises the stop and skips the tick; the loop pauses as for any idle iteration and tries again. The stop is written once per detail: the same fault on the next iteration adds no second line, a different fault adds a new one. Push the missing branch or file and the next iteration clears the stop. The detail says which fault it is:

- `cannot prepare the checkout: <git's message>`: the clone failed. Check `FACTORY_REPOSITORY_URL` and the credentials.
- `cannot fetch: <git's message>`: the fetch failed.
- `the repository has no main branch yet`: the repository has no commit on `main`.
- `origin/main has no factory/pipeline.yml yet`: push `factory/pipeline.yml` to `main`.

## The factory log and the health status file

Both live in the factory's state directory. `factory-run` starts the factory; this describes what it writes; the next section says when a stop is written and when it goes away.

### The factory log

The factory log writes every line twice: to standard output and, appended, to a file (UTF-8, lines end in `\n`). A line is `<stamp> <text>`. The stamp is `YYYY-MM-DDTHH:MM:SSZ`: UTC, whole seconds (a fraction is cut off, not rounded). One call can hold several lines, and they all carry one stamp, because the clock is read once per call:

```text
2026-10-12T12:00:07Z first
2026-10-12T12:00:07Z second
2026-10-12T12:00:12Z third
```

**The stage environment's timing line.** The factory writes one line per stage, after the take: `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`, each in seconds with one decimal, for example `stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s`. `reset` and `advance` are the dataset's roll-back and the move of its base, `sync` the sync container (`make sync` included), `take` the copy of the agent's result into the checkout; read the cost of a stage's setup from these lines in `/state/factory.log`.

Missing parent directories are created. If the file cannot be written, the line has still reached standard output, and the write fails with an `OSError`.

### The health status file

`health.json` in the state directory holds the stops in force for the repository or the machine, as one JSON object: `{"stops": [{"scope": ..., "reason": ..., "detail": ..., "at": ...}]}`. `factory-health` reads it (see "The preflight and the health check"); an empty `stops` list is healthy.

- One stop per reason. `scope` is `machine` for `preflight_failed`, `disk_low` and `stage_image_failed`, and `repository` for every other reason; `detail` names the fault and is never blank; `at` is in UTC.
- The reasons are `fetch_failed`, `checkout_restore_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `repository_unavailable`, `main_branch_failing`, `preflight_failed`, `disk_low` and `stage_image_failed`.
- `factory-run` writes an empty status (`{"stops": []}`) when it starts and finds no file, before it reads the token file; an existing file is left as it is, its stops in force. If that write fails, `factory-run` fails with the `OSError` and clones nothing.
- A file that is missing reads as not healthy for the health check (`no health status: <path> is missing`, exit 1). A file that cannot be read, is not JSON or is not a valid status reads as healthy (no stops). Do not repair it by hand: the next stop that is raised replaces the whole file, and a fault that lasts is raised again.
- A write goes to a temporary file in the same directory and replaces `health.json` in one step, so a reader never sees half a file. If `health.json` is a directory, the write fails with an `OSError` and leaves nothing behind.

### The records

The state directory's `records/` folder holds four JSON Lines files. None is committed; the tick publishes the stop records to `factory/stops.jsonl` on `main` (see "The stop records on main" in [stops.md](stops.md)). `project-commands.jsonl` holds every project command run (below), `known-results.jsonl` is described in "The known results", `stops.jsonl` in "The stop records" and `disk.jsonl` in "The disk record". A line of any of them that a kill cut, or that is not UTF-8, is skipped when the factory reads the file, so a damaged record file needs no repair. A record appended right after a line a kill cut shares that line and is skipped with it; a whole line that is not UTF-8 costs only itself.

`records/project-commands.jsonl` in the state directory `FACTORY_STATE` names (`/srv/factory/<instance>/state/records/project-commands.jsonl` on the VM) holds one JSON line for every project command the factory runs (`check`, `lint`, `test` and the rest), whoever asked for it: the stage checks after an agent, the preflight's probe and the check of `main`. The folder is created on the first run. A line has these fields:

| Field | Meaning |
|---|---|
| `command` | The make target, for example `check`. |
| `commit` | The 40-character commit of the checkout's `HEAD` when the command started; `null` when it cannot be read. |
| `started_at` | When the command started, UTC with an offset. |
| `duration_seconds` | How long it ran, in seconds. |
| `status` | `passed`, `failed` or `time_limit`. |
| `exit_status` | The exit status; `null` for `time_limit`. |
| `targets` | For each target that ended green, `{"target": ..., "seconds": ...}`, in the order printed (for `check`, the time of each of its targets). |

`project-commands.jsonl` is telemetry beside the factory log, not a work item's state: nothing reads it to decide anything. You may delete the file at any time; the next run starts a new one. A command that raises an error (a missing `make`, a time limit of 0) leaves no record. When a line cannot be written, the factory log gets `cannot write the record of <command>: <error>` and the run goes on.

To count the `check` runs of each commit, with the most-run commits first:

```bash
python3 -c "import json,collections as c; print(c.Counter(r['commit'] for r in map(json.loads, open('/srv/factory/vm/state/records/project-commands.jsonl')) if r['command']=='check').most_common())"
```

A commit that appears more than once was checked more than once.

#### The known results

`records/known-results.jsonl` in the state directory `FACTORY_STATE` names (`/srv/factory/<instance>/state` on the VM) holds one JSON line for each run of a stage's check or report and for each time the factory took an earlier result instead of running it. After an agent the factory runs every check and report of the stage; when the last run under the same key passed, it does not run the command again. The preflight's probe and `project-commands.jsonl` are not part of this: the probe still runs, and `project-commands.jsonl` still holds every real run and no reuse. A line has these fields:

| Field | Meaning |
|---|---|
| `key` | What the result depends on: `command`, `tree`, `definition` and `image`. |
| `at` | When the factory started the run or took the result, UTC. |
| `status` | `passed`, `failed` or `time_limit`. |
| `last_line` | The last line of the command's output. |
| `duration_seconds` | How long the command ran; 0 for a reuse. |
| `reused` | `null` for a real run; for a reuse, the `at` of the run it took. |

The key has four parts:

- `command`: the make target.
- `tree`: the tree the command reads, as `Git.work_tree_id` names it for the command's `not_read` (see "The pipeline definition" in [pipeline.md](pipeline.md)).
- `definition`: the SHA-256, in hex, of the whole pipeline definition.
- `image`: the stage image (see "The image on the cost records" in [machine.md](machine.md)), `null` without one.

A known result is invalidated by a change in any part: a changed file the command reads, a merge of `main` that brings one, any change of the pipeline definition (a time limit, a stage, any value), or a new image. A change only in left-out files keeps the key.

- A failed or timed-out result is never reused. The last real run of a key decides: a pass, then a failure of the same key, ends the reuse of the pass until a new run passes.
- A reuse is a record too, with the time of the run it took, so no check is silenced and the runs of a tree can be counted.
- Only the factory's own runs are known. What an agent ran itself is not.
- Deleting the file forgets every known result: the next run of each command runs it.

When something goes wrong the command runs as it did before, and the factory log says why, in one line:

| Line | Meaning |
|---|---|
| `known results: no key for <command>: <error>` | The tree could not be named; the command ran and nothing was recorded. |
| `known results: cannot read the records: <error>` | The file could not be read; the command ran. |
| `known results: cannot write the record of <command>: <error>` | The line could not be written; the result is still used. |

To count the `check` runs of each tree, the most-run first (a reuse is not counted):

```bash
python3 -c "import json,collections as c; print(c.Counter(r['key']['tree'] for r in map(json.loads, open('/srv/factory/vm/state/records/known-results.jsonl')) if r['key']['command']=='check' and r['reused'] is None).most_common())"
```

#### The stop records

`records/stops.jsonl` in the state directory holds one JSON line for each event of a stop of the repository or the machine. A line has these fields, in this order: `event` (`raised` or `cleared`), `scope` (`machine` for `preflight_failed` and `disk_low`, `repository` for the rest), `reason`, `at` (UTC, ending in `Z`) and `instance` (the instance's name). It never holds the stop's detail:

```text
{"event":"raised","scope":"machine","reason":"disk_low","at":"2026-10-18T10:00:00Z","instance":"self"}
```

- `raised` is written when a stop of its reason is raised and the health status held none of that reason. A stop raised again every cycle while it lasts writes nothing more. `cleared` is written, after the status and the `stop cleared` line, when a stop of that reason stood and is removed; clearing a reason that does not stand writes nothing.
- A raise whose health status cannot be read writes no `raised` record. The next raise that can read the status finds no stop standing and writes it. A stop that clears before the status is readable again therefore never reaches the records; its line is still in the factory log.
- When the record cannot be written, the other destinations were still tried and the factory reports the `OSError` as for the log and the status.
- The factory never clears this file. The tick publishes its records to `main` (see "The stops" in [stops.md](stops.md)), and a record is pushed once. Delete the file only when `main`'s `factory/stops.jsonl` holds every line of it; a record deleted before it was pushed is lost.

#### The disk record

`records/disk.jsonl` in the state directory `FACTORY_STATE` names (`/srv/factory/<instance>/state` on the VM) holds one JSON line each time the factory measures its folders: `at` (UTC with an offset), `occasion` (`start` or `acceptance`) and `folders`, a list of `{"path", "free_bytes", "used_bytes"}` for the work directory (the checkout's parent), the state directory and the process's temporary directory (`/tmp`), in that order. `free_bytes` is the free space of the file system the folder is on; `used_bytes` is the size of what is under it. A value the factory could not read is `null`.

The same record is one line in the factory log, for example `disk start: /srv/factory/vm 812.3 GB free, 0.7 GB used; /srv/factory/vm/state 812.3 GB free, 0.0 GB used; /tmp 812.3 GB free, 4.3 GB used`, each value in GB or `unknown`.

It is written at each start of the instance, before the first tick, and at each feature acceptance. No record is written at the end of a run. Compare the new line with the last one to see whether disk use grows. When the line cannot be written, the factory log gets `cannot write the disk record: <error>` and the run goes on. It is not committed; the factory uses only its last record that reads whole, to name the previous measure beside the new one at a feature acceptance.

The size of a folder counts only what the factory user can read. A folder under `/tmp` that another user made with mode `0700` is left out, while the free space of the file system still shows it.

The record cannot see the host. Read the host's own numbers by hand at the same moments and at the end of a run: the free space of the VM's disk, and the size of the pool (`zpool list`).

## Transcripts

A transcript is the whole conversation of one agent run: every file the agent read, every command's output and the agent's reasoning. It can hold what no scan of secrets finds, so it never goes to GitHub, not in a comment, not in a commit. The factory keeps it in a folder of the site's own.

### The setting

`FACTORY_TRANSCRIPT_DIR` names the folder: on a VM a local directory, in a Cloud Run job a Cloud Storage bucket mounted as a volume, so the factory needs no cloud client and knows only the folder. It must be an absolute path outside `FACTORY_WORKSPACE`, `FACTORY_CHECKOUT`, `FACTORY_STATE` and the agent home (`FACTORY_CLAUDE_HOME`); `read_settings` refuses any other with the variable's name. No container mounts the folder and no prompt names it.

Unset or empty keeps no transcript. That is no fault: the factory starts and runs as before, writes no `transcript:` line, and the preflight has no item for the folder.

### What is kept

After each agent run that has a session, and before the dataset is rolled back, the factory copies the session's transcript to

```
<FACTORY_TRANSCRIPT_DIR>/<work item>/<run id>.jsonl.gz
```

gzip-compressed, mode `0600` (the folders it creates get `0700`). `<work item>` is the id such as `F0050-S0005`, `<run id>` the run's id on its cost record. Claude Code's transcript is the session file under `.claude/projects/` in the agent's home on the dataset; opencode's is the JSON event stream its wrapper read as the run printed it, one event per line. Read one with `zcat <file>`.

A run that is resumed within itself (after a spent budget) keeps one file; the copy after the resume replaces the earlier one. A later run that continues an earlier run's session (after a provider limit) writes a file under its own run id.

The cost record refers to the file with `transcript`: `path` (relative to the folder, as above) and `sha256` (of the file as written, so that a reader can tell it is the file the record names). It is `null` when none was kept.

### When one is not kept

A transcript that cannot be found or copied (no session, no transcript file, a folder that cannot be written) writes one line to the factory log, `transcript: not kept for <run id>: <reason>`, and the record's `transcript` is `null`. The run, the stage and the factory go on.

### The site's part

- The folder must sit where only the site's own people can read it. The factory sets the file modes, but a mounted bucket or a shared disk has its own access rules.
- The factory deletes no transcript. Removing old ones is the site's: by hand on a VM, if ever needed, and a lifecycle rule on a bucket.

### On a VM

`vm/setup.sh` sets this up (steps 14 and 16 of *The steps* in [machine.md](machine.md)). It makes `/srv/factory/<instance>/transcripts`, owned by `factory`, mode `0700`, and writes `FACTORY_TRANSCRIPT_DIR=/srv/factory/<instance>/transcripts` into `factory.env`. A second run of the script finds both in place and changes nothing.

The VM keeps no retention: at about 5 MB per feature the folder grows too slowly to need one. There is no `tmpfiles.d` rule and no option for an age. Removing old transcripts is yours, by hand, if ever needed. Read a transcript as `factory` or root: `zcat /srv/factory/<instance>/transcripts/<work item>/<run id>.jsonl.gz`.

### In a Cloud Run job

The folder is a Cloud Storage bucket of your own project, mounted into the job as a volume. You make it once; the factory needs no Cloud Storage client and no new right, and `vm/job-start.sh` only checks that the folder can be written.

1. Make a bucket in the job's project and region, with uniform bucket-level access and public access prevented:

   ```bash
   gcloud storage buckets create gs://<bucket> --project=<project-id> --location=<region> \
     --uniform-bucket-level-access --public-access-prevention
   ```

2. Add a lifecycle rule that deletes objects after 30 days. Save `{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 30}}]}` as `lifecycle.json` and run:

   ```bash
   gcloud storage buckets update gs://<bucket> --lifecycle-file=lifecycle.json
   ```

3. Give the job's service account `roles/storage.objectUser` on that bucket only, not on the project:

   ```bash
   gcloud storage buckets add-iam-policy-binding gs://<bucket> \
     --member=serviceAccount:<job-service-account> --role=roles/storage.objectUser
   ```

4. Mount the bucket into the job and name the path:

   ```bash
   gcloud run jobs update <job> \
     --add-volume name=transcripts,type=cloud-storage,bucket=<bucket> \
     --add-volume-mount volume=transcripts,mount-path=<path> \
     --update-env-vars FACTORY_TRANSCRIPT_DIR=<path>
   ```

`<path>` is absolute and none of the four places *The setting* names. The bucket stays inside your site: only the job's service account and the people you allow read it. At these sizes (about 5 MB per feature) it costs a few cents a month. These commands create things in your cloud; they are not run by the factory or its tests.
