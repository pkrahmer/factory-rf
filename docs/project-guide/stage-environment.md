# The stage environment

This file covers the two interfaces through which the factory reaches the dataset a stage runs on and the containers its commands run in, and their fakes; read the index, `README.md`, first. The modules are `factory.application.stage_environment`, `factory.application.snapshots`, `factory.application.containers`, `factory.application.take`, `factory.domain.containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.podman_runs`, `factory.adapters.printed_output`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. The stage protocol calls the stage environment (*The cycle* lists its steps, *The stage environment* the interface). There is one environment, the dataset and the containers: v1.1's `inline` environment and its setting went with F0044-S0008 (*The settings and the wiring*). The wiring also lives in `factory.domain.settings` and `factory.entry.wiring`.

## The cycle

A stage runs in the order below (`planning/v1.2-plan.md`, "The cycle of a stage"). Each step names the section that describes it. The sections for the details are *The stage environment* and *The container environment*.

1. The factory claims the stage and commits the claim, outside the environment (`stages.md`).
2. `prepare` rolls the dataset back to `@base` (*The snapshots*, *The container environment*).
3. `prepare` syncs the checkout in a sync container (*The sync command*, *The container runs*).
4. `prepare` moves `@base` forward to the synced dataset (*The snapshots*).
5. `run_agent` runs the agent in its own container (*The agent's container*).
6. `take` copies what the role may write into the factory's work tree (*The take*).
7. The stage's checks run on a clean base with the taken files (*The checks*).
8. The factory commits and pushes what it took, and decides the stage (`stages.md`).

## The snapshots

`Snapshots` (`factory.application.snapshots`) stands for one dataset and its base snapshot. It is an abstract base class like every interface (see `CLAUDE.md`), so another snapshot tool can implement it later. Its members:

- `mount_point` (property): the dataset's path on the host. `changed_paths` are relative to it.
- `reset()`: puts the dataset back to the base.
- `advance()`: moves the base to the dataset's current state; what the base held before is gone.
- `changed_paths()`: every non-directory entry that differs from the base, as `ChangedPath` (`factory.domain.git`: `path` and `change`, one of `added`, `modified`, `deleted`), sorted by path.

`changed_paths` lists files and symbolic links. It never lists a directory, also an empty one, and a rename is a deletion and an addition. `reset` and `changed_paths` need a base: without one they raise `SnapshotError`.

`SnapshotError(command, detail)` (`factory.domain.errors`, a `BoundaryError`) is the one error of the interface: a snapshot command failed, could not start or reached its time limit. The message is `snapshot command <command> failed: <detail>`; `command` and `detail` are attributes.

## The container runs

`ContainerRuns` (`factory.application.containers`) runs one command at a time in a fresh container on the dataset. The dataset is mounted at `/work` in every container. `factory.domain.containers` names its places: `WORK` (`/work`), `WORK_CHECKOUT` (`/work/checkout`) and `WORK_HOME` (`/work/home`).

Both operations take the command words and, by keyword, `mounts`, `environment`, `time_limit` and `working_directory`:

- `launch(...)` returns a `ContainerLaunch`: the `argv`, the `env` and the `time_limit` that start the command in a container. It runs nothing. A caller that starts the process itself uses it. `env` of `None` means the process's own environment.
- `run(...)` runs the command until it ends or reaches `time_limit` and returns a `ContainerResult`: `exit_status`, the merged `output`, `timed_out` and `duration`. `exit_status` is `None` exactly when `timed_out` is true (a model validator). A command that fails or times out is a result; `ContainerError` means the container could not be started.

A `Mount` has a `source` (an absolute host path), a `target` (a container path) and `read_only` (default false). A target starts with `/` and has no empty segment and no `..` segment, so `/`, `a/b`, `/a//b`, `/a/` and `/a/../b` are refused with `ValidationError`; `/a/./b` is accepted. The dataset is the fixed `/work` mount of every run, so both operations raise `ValueError` for a mount whose target is `/work` or lies under it, and for a command without words. `check_container_call` (`factory.domain.containers`) is that rule; the fake and the podman adapter both call it.

`ContainerError(command, detail)` is the interface's `BoundaryError`, with the message `container command <command> failed: <detail>`. `ContainerCall` records one call as it was asked; only the fake uses it.

## The fakes

Both fakes let the suite and the smoke tests run without `zfs` and `podman`.

`FakeSnapshots(folder, base)` keeps the base as a copy of `folder` at `base`. `advance` replaces `base` with a copy (folders, files with their bytes and mode, symbolic links as links, never followed). `reset` replaces the contents of `folder` with a copy of `base`; `folder` itself stays, as a mount point does. `changed_paths` walks both trees and compares bytes, mode and link target. It starts no process. Without a `base` folder, `reset` and `changed_paths` raise `SnapshotError("reset" or "changed_paths", "no base at <base>")` and `reset` changes nothing.

`FakeContainerRuns(workspace)` plays a container as a child process on the host, through `run_process` (`factory.adapters.process`; the structural test `tests/test_wrapper_search.py` names this module as one that reaches it). It maps container paths to host folders:

- The mounts given plus a fixed mount of `workspace` at `/work`. A command word, an `environment` value or the `working_directory` that equals a target, or starts with the target and a `/`, has that target replaced by the mount's `source`. The longer target wins; `/workspace` is not under `/work`. Keys of `environment` are never mapped.
- `launch` returns `/bin/sh -c 'cd "$1" && shift && exec "$@"' fake-container <working directory> <command...>`, all mapped, with the time limit as given.
- `run` starts those words with the mapped working directory and environment and the merged output. A program the shell cannot find is a result with exit status 127. A child that cannot be started, such as a working directory that does not exist, is `ContainerError(command[0], <operating system's message>)`.
- `calls` lists every accepted `launch` and `run` as `ContainerCall`, before the mapping. A call refused with `ValueError` is not recorded.

The suite's stages run on these fakes (*Wiring and tests*). Because the agent's request names the dataset's checkout as its working directory whenever the boundaries hold snapshots (`agent_working_directory` in `factory.application.take`: `snapshots.mount_point / "checkout"`, else `boundaries.checkout`; `TaskComposer` and the preflight's probe use it), `FakeAgentRuntime` writes where a real agent writes and the take brings the result in. A real runtime in a container ignores the field: the container's working directory is `/work/checkout`.

What the fake cannot do: it does not enforce `read_only` (a mount is only a path mapping), isolates nothing, and the command sees the host's programs.

Tests: `tests/domain/test_containers.py`, `tests/domain/test_errors_environment.py`, `tests/application/test_snapshots_interface.py`, `tests/application/test_containers_interface.py` (and the two interfaces in `tests/application/test_interfaces.py`), `tests/adapters/test_fake_snapshots.py` and `tests/adapters/test_fake_containers.py`. The fakes' tests work in `tmp_path` and start only `/bin/sh` and `printf`.

## The ZFS adapter

`ZfsSnapshots(dataset, mount_point, *, executable="zfs", time_limit=SNAPSHOT_TIME_LIMIT)` (`factory.adapters.zfs_snapshots`) implements `Snapshots` for a ZFS dataset such as `tank/factory/vm`, mounted at `mount_point` (returned as given). Its base is the one snapshot `<dataset>@base` (`BASE_SNAPSHOT`). `SNAPSHOT_TIME_LIMIT` is ten minutes. The adapter runs the one executable it is given, so an operator can pass a wrapper script (a `sudo` call, for instance) in place of `zfs`.

### The commands

Every command runs through `run_process` (`factory.adapters.process`; `tests/test_wrapper_search.py` names the module) with the working directory `/`, the factory's own environment, the time limit and standard error merged into the output.

| Member | Runs | When |
| --- | --- | --- |
| `reset()` | `zfs rollback -r <dataset>@base` | always; `-r` removes any later snapshot |
| `advance()` | `zfs list -H -o name -t snapshot <dataset>@base`, then `zfs destroy <dataset>@base`, then `zfs snapshot <dataset>@base` | `destroy` only when `list` exits 0; exit 1 means there is no base yet and `destroy` is skipped |
| `changed_paths()` | `zfs diff -FH <dataset>@base` | always |
| `version()` | `zfs --version` | the preflight |
| `dataset_exists()` | `zfs list -H -o name <dataset>` | the preflight |

### Reading `zfs diff -FH`

Each non-blank line is tab-separated: `<change> <kind> <path>`, or for `R` `<change> <kind> <old path> <new path>`. A field after those (`(+1)`, the link count of a hard link) is ignored.

- Changes: `M` is `modified`, `+` is `added`, `-` is `deleted`. `R` is `deleted` for the old path and `added` for the new one.
- Kind `/` is a directory and is left out, whatever the change. The mount point itself, which `zfs diff` lists as a directory, is therefore no fault. Every other kind (files, links) is listed.
- Every path must be the mount point or lie under it; `/srv/x/workx/a` is outside `/srv/x/work`. Paths are made relative to the mount point with `/` separators.
- `zfs` writes each byte outside printable ASCII, and the backslash, as `\ooo` in octal (`\040` a space, `\303\251` an `é`, `\134` a backslash). The adapter decodes them to bytes and reads the bytes as UTF-8.
- A path that two lines name, one removing it and one adding it (a file made anew, a rename onto a removed path), is listed once, as `added`, in either order.
- The result is sorted by path; an empty output is `[]`.

### Faults

Every fault is `SnapshotError(command, detail)`. `command` is the words run joined by a space, executable first (`zfs rollback -r tank/factory/vm@base`). `detail` is:

- the last non-blank line of the output, or `exit status <n>` when there is none, for a command that failed. Failed means an exit status other than 0, except for the two `list` commands, where only a status other than 0 or 1 fails;
- `no end within <n> s` when the time limit was reached, `n` the limit's seconds rounded up;
- the operating system's message (`[Errno 2] ...`) when the executable could not start;
- for `diff` only: `cannot read the line <line>` for an unknown change, too few fields, or a path that is not UTF-8, and `<path> is outside <mount point>`.

### For the preflight

`version()` returns the first non-blank line of `zfs --version`, stripped (`zfs-2.2.2-0ubuntu9.1`); no such line is a fault with `printed nothing`. `dataset_exists()` is `True` when `list` exits 0 and names the dataset, `False` on exit 1, and a fault otherwise: `named <line>, not <dataset>` for another name, `printed nothing` for none.

### The stand-in

No test runs a real `zfs`; it runs only on the VM. `tests/zfs_support.py` writes a stand-in `zfs` into `tmp_path`. It records its arguments, environment and working directory, then answers by a plan keyed on its first argument (`rollback`, `list`, `destroy`, `snapshot`, `diff`, `--version`): planned output and exit status, or a sleep past a short limit. The limit itself cannot be seen from the stand-in, so tests of the default limit and its rounding replace the module's `run_process` with the `Recorder` of `tests/run_process_recorder.py`. The tests are `tests/adapters/test_zfs_snapshots.py` and `tests/adapters/test_zfs_snapshots_diff.py`.

## The podman adapter

`PodmanRuns(executable, image, workspace, *, time_limit=PODMAN_TIME_LIMIT)` (`factory.adapters.podman_runs`) implements `ContainerRuns` with the `podman` executable: every command runs in a throwaway container of `image`, `workspace` (the dataset's mount point) mounted at `/work`. `executable` is run as given, so an operator can pass a wrapper script. `time_limit` bounds only `version` and `image_exists`; `PODMAN_TIME_LIMIT` is two minutes.

### The command line

`launch` builds these words, in this order:

```
<executable> run --rm --userns=keep-id --timeout <seconds>
    --cap-drop=all --security-opt=no-new-privileges
    --pids-limit=4096 --memory=4g
    --env NAME=value ...
    --volume <workspace>:/work --volume <source>:<target>[:ro] ...
    --workdir <working_directory> <image> <command...>
```

- `--rm`: the container is removed when it ends, so nothing of one command is left for the next.
- `--userns=keep-id`: rootless podman maps the container's user to the host user that runs podman, the `factory` user. Files the command writes into `/work` belong to that user on the host.
- `--timeout <seconds>`: the container runtime ends the container at the limit. The seconds are the limit rounded up (`30s` is `30`, 1.5 seconds is `2`).
- `--cap-drop=all`: the container has no capability. Code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) cannot use the rights root has inside its namespace.
- `--security-opt=no-new-privileges`: a set-uid program cannot give a process rights it was not started with.
- `--pids-limit=4096`: a fork bomb ends at the limit and does not fill the machine's process table.
- `--memory=4g`: a runaway process is killed in its container and does not take the machine's memory.
- `--env NAME=value`: one pair per entry of `environment`, in its order. These are the only variables the command gets besides the image's own. Podman does not pass the factory's environment into the container, so a token or a path the factory holds reaches a command only when a caller names it here.
- `--volume`: the workspace at `/work` comes first, then the given mounts in their order. A read-only mount gets `:ro`. A rootless container cannot write a `:ro` bind mount, and that is the whole protection of the host's repository and of the login files: a command can read them and never change them. The tests pin the words, `:ro` above all.
- `--workdir`: the command's working directory in the container.
- the image, then the command words, which are never joined into a string.

There is no `--network` word, so every container keeps podman's default network: the sync needs the package index, the check runs `make sync` first, which needs the index when the take changed `uv.lock` or `pyproject.toml`, and the agent needs the model's API. Cutting the network is a later step, for example an allow-list (decision *Every container runs without rights and within limits*).

The limits are the constants `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"`, read on every call of `launch`. 4096 processes leave room for the test suite's workers under `-n auto` on the VM's cores and what each starts; 4 GB lets one container run at a time on a machine of 8 GB. A container the kernel kills for its memory before the time limit is an ordinary result with its exit status, not a time-out: a command that fails with make's status 2 when the kernel ended one of its children, 137 when it ended the container's first process.

Measured on 2026-10-24 on the local VM (Ubuntu 24.04, podman 4.9.3, rootless as `factory`): podman accepts all four words; the container's effective capabilities are `0000000000000000`; a write to the dataset still works under `--userns=keep-id`; `--pids-limit=50` stops the 49th fork with "can't fork: Resource temporarily unavailable"; `--memory=64m` sets the container's `memory.max` to 67108864; and the user's systemd delegates the `cpu memory pids` controllers.

`launch` returns `ContainerLaunch(argv, env=None, time_limit=<limit> + CONTAINER_GRACE)`. `env` is `None`: the `podman` program itself runs with the factory's environment (`HOME`, `XDG_RUNTIME_DIR` and `PATH` it needs), as `version` does.

### The grace

`CONTAINER_GRACE` is 30 seconds. The process request carries the limit plus the grace, so podman's `--timeout` fires first and the factory's own kill is the second line, for a podman that does not end. A `timed_out` result therefore usually comes from podman's kill, not the factory's.

### Reading the end

`run` starts the launch's words through `run_process` (`factory.adapters.process`; `tests/test_wrapper_search.py` names the module) with the working directory `/` (podman reads no file from it; a missing workspace is podman's own fault, 125), the factory's environment and standard error merged into `output`.

- `timed_out` is true when `run_process` says so, or when the exit status is in `CONTAINER_KILL_STATUSES` (`factory.adapters.agent_launch`: 137, -9 and 255) and the run lasted at least `time_limit`: podman's `--timeout` sent the kill. `exit_status` is then `None`.
- The same statuses before the limit are the command's own, as is any other status at or after the limit.
- Otherwise `exit_status` is podman's, which is the command's. Podman exits 125 for its own faults, such as a missing image; the result says 125 and podman's message is in `output`.
- Podman's `--timeout` ends a container with exit status 255, not 137 (`PODMAN_TIMEOUT_STATUS`; podman 4.9.3, measured 2026-10-24 on the local VM: `podman run --rm --timeout 3 ... sleep 30` ended after 3.04 s with 255). The factory therefore reads 137, -9 or 255 at or after the limit as the time limit for a container call, and only 137 or -9 (`KILL_STATUSES`) for any other call, where 255 is no kill. 255 before the limit stays an ordinary exit status: a command can exit 255 by itself, and only the elapsed time tells that podman's timeout was the cause.
- A `podman` that cannot start is `ContainerError(command[0], <operating system's message>)`: the first word of the command asked for, not `podman`.
- `launch` and `run` raise `ValueError` as the interface says (`check_container_call`).

### For the preflight

`version()` returns the first non-blank line of `<podman> --version` (`podman version 4.9.3`). `image_exists()` runs `<podman> image exists <image>`: exit status 0 is `True`, 1 is `False`. Both run with `workspace` as working directory and the constructor's `time_limit`, and every other outcome is `ContainerError(<command words joined by a space>, <detail>)`:

- an exit status other than 0 (for `image_exists`, other than 0 or 1): the last non-blank output line, or `exit status <n>`;
- `no end within <n> s`, `n` the limit rounded up;
- `printed nothing`, for `version` only, when exit status 0 comes with no output;
- the operating system's message when the executable cannot start.

The preflight reads a missing `podman` from this error. The line helpers (`first_printed_line`, `failure_detail`, `no_end_detail`) are in `factory.adapters.printed_output`, shared with `ZfsSnapshots`.

### The stand-in

No test runs a real `podman`; it runs only on the VM. `tests/podman_support.py` writes a stand-in `podman` into `tmp_path`. It records its arguments, environment and working directory; it prints planned output, waits and exits with a planned status, or, when its arguments hold the image, runs the words after the image on the host, so that a command's own exit status and output pass through. Tests of the default limit and of the kill rule replace the module's `run_process` with the `Recorder` of `tests/run_process_recorder.py`. The tests are `tests/adapters/test_podman_runs.py` (the command line), `tests/adapters/test_podman_runs_fence.py` (the four words and the constants) and `tests/adapters/test_podman_runs_results.py` (results and faults).

## The stage environment

`StageEnvironment` (`factory.application.stage_environment`) is the one object the stage protocol calls for the cycle of a stage: it prepares the place the agent works in, runs the agent there, and takes the result back into the factory's work tree. It is an abstract base class with three operations; the stage protocol knows no `podman`, `zfs` or `sudo`.

### The three operations

- `prepare(commit, branch, *, sync_time_limit)`: makes the place hold `branch` at `commit`, its tools synced. `SnapshotError` or `ContainerError` when that cannot be done; the sync's container gets `sync_time_limit`.
- `run_agent(request, *, run=None)`: runs the request's agent in this environment and returns its `AgentRunResult`. With `run` the environment calls it once instead of the boundaries' runtime; whatever it does inside, such as the resumes of `PatientRuns` after a provider limit, happens in the same prepared place.
- `take(stage_start, work_item_path)`: brings the agent's result into the work tree as far as the role may write, and returns a `TakeReport` (`left`, `restored_work_item`; see *The take*). `WorkItemFormatError` naming `work_item_path` when the work item is absent or unreadable at the stage-start commit; the work tree is then left untouched.

`stage_environment_of(boundaries)` gives the `ContainerEnvironment` on `boundaries.snapshots` and `boundaries.containers`, both required (see *The container environment*). `StallService` reaches the take only through the environment it is given: its stall takes like `AfterAgent` does.

### Who calls what

- `StageLauncher.launch`, after the claim is pushed and the pull request ensured and before the cost record begins: `prepare(stage_start.commit, branch, sync_time_limit=...)`, then `run_agent(request, run=PatientRuns(boundaries).run)`. An error from `prepare` ends the launch like one from the agent runtime, after the claim and before any run or cost record.
- `AfterAgent.process`: `take(started.stage_start, started.path)` once the result and the decision are accepted. `AgentAftermath.take` carries the report, and the entry's closing paragraph names `take.left` (see `stages.md`, *After the agent run*).
- `agent_run_probe_item` (the preflight): `stage_environment_of(boundaries).run_agent(request)`. The probe reports no fault for a nested repository the run leaves.
- `StallService.stall`, with a stage start, after the checkout is put back on the work item's branch: `take(context.stage_start, context.path)`, whatever the reason (`check_red` included), and its report is `StallResult.take`. A stall after `AfterAgent`'s take is a second take within one stage. `StageFinisher` takes only through its stall service: the checks go through `boundaries.project_commands`.

### The sync time limit

`StageLauncher` takes the limit from the pipeline definition: the `time_limit` of its `sync` project command, in minutes, and when the definition has no `sync` command the default of a project command, `ProjectCommandDefinition().time_limit` (10 minutes).

### One environment per runner

`StageLauncher`, `AfterAgent`, `StageFinisher` and `StallService` take an optional keyword `stage_environment`; `None` means `stage_environment_of(boundaries)`. `StageRunner` builds one environment and gives it to all four, so that the object that saw a stage's `prepare` sees its `take`.

Tests: `tests/application/test_stage_environment_of.py` (the environment of the boundaries), `tests/application/test_stage_environment_calls.py` (a stand-in environment that records its calls, given to `StageLauncher` and `AfterAgent`), and the interface's row in `tests/application/test_interfaces.py`.

## The container environment

`ContainerEnvironment(boundaries, snapshots, containers)` (`factory.application.stage_environment`) is v1.2's `StageEnvironment`: the agent works on the dataset of `Snapshots`, the sync runs in a container of `ContainerRuns`, and the take copies back what the role may write. It runs steps 2 to 4 and 6 of the cycle in `planning/v1.2-plan.md` ("The cycle of a stage"). The agent's own container (step 5) is not here: `run_agent` runs the request through the boundaries' runtime, which starts the container itself (below, *The agent's container*).

### `prepare`

`prepare(commit, branch, *, sync_time_limit)` does four things in this order, each timed with `boundaries.clock`:

1. `snapshots.reset()`: the dataset goes back to its base. `SnapshotError` propagates as it is, and no container has run.
2. The sync container: `containers.run(["/bin/sh", "-c", <script>, "factory-sync", "/work/checkout", "/work/home", "/upstream", "/etc/factory/claude", branch, commit], ...)` with these mounts, both read-only: the host checkout's `.git` at `/upstream` (`UPSTREAM`) and `settings.agent_home` at `/etc/factory/claude` (`AGENT_FILES`). The environment is `SYNC_ENVIRONMENT` (`PATH=/usr/local/bin:/usr/bin:/bin`, `HOME=/work/home`), the time limit is `sync_time_limit` and the working directory is `/work`. `/work` is the dataset, so `/work/checkout` and `/work/home` are its two folders.
3. The result is judged. A timeout is `ContainerError("sync", "no end within <n> s")`, `n` the limit in seconds rounded up (1.2 s gives 2, 3 s gives 3). An exit status other than 0 is `ContainerError("sync", <detail>)`: the last non-blank line of the output that is no make message (`factory.domain.checks.last_line`, the rule `MakeProjectCommands` uses too: a line starting `make:` or `make[` is skipped, so a failed recipe's own last line is the detail), or `exit status <n>` when no such line exists.
4. `snapshots.advance()`: the base moves to the synced dataset.

#### The sync script

The script is one literal, `_SYNC_SCRIPT`. Every container path reaches it as an argument (`$1` checkout, `$2` home, `$3` upstream, `$4` agent files, `$5` branch, `$6` commit) and none is written in its text, so that `FakeContainerRuns`, which maps paths in the command words, can play it on the host. With `set -eu` it stops at the first failure and:

1. makes `$1` and `$2` when missing;
2. replaces `$2/.claude` with a copy of `$4`: the copy replaces the folder, it does not merge, so an agent file removed on the host is gone in the next stage and one run cannot widen the tools of the next (decision 6 of F0042; the factory process copies no files itself);
3. in `$1`, runs `git init -q` when there is no `.git`;
4. fetches `+refs/heads/*:refs/heads/*` and `+refs/heads/*:refs/remotes/origin/*` from `$3` in one `git fetch` with `--prune` and `--update-head-ok`: every branch, not only the stage's, because a detached checkout would leave the agent without `main` and the branch, and the coder's and reviewer's instructions read `git diff main` and the branch's log (decision 5); `--prune` drops a branch deleted on the host; `--update-head-ok` because git refuses to fetch into the checked-out branch, an unborn one included, as a fresh `git init` has. The second refspec makes the checkout know `origin/main` and `origin/<branch>` as a clone would, because the project's commands read `origin/main`: `make secrets` limits itself to the files a branch changed by it, and without it scanned every tracked file. On the first VM stage (F0043-S0004) the coder's `make check` stopped there on old hex values in finished acceptance reports the branch never touched, and the same would have ended every stage on a `container` instance, the factory's own check included;
5. `git checkout -q -f "$5"` and `git reset -q --hard "$6"`, so `HEAD` is on the branch at the stage-start commit and never detached;
6. `make sync` (see *The sync command*).

The first `prepare` on a dataset creates the repository; the next ones reuse it, and objects of earlier stages stay in it.

### What a fault leaves behind

- `reset` fails (`SnapshotError`, for example a dataset without a base): nothing else ran, `containers` was not called.
- The sync fails or times out: the dataset holds whatever the script did, and the base did **not** move. `snapshots.changed_paths()` is not empty, and the next `reset()` empties the dataset again. The stage ends with the error before any agent runs.
- The commit is no commit: `git reset` fails, the detail is git's message.
- The durations of a failed `prepare` are not kept: the timing line keeps those of the last successful one (the stage stops at the error, so no `take` follows).

### `run_agent`

`run_agent(request, *, run=None)` calls `(run or boundaries.agent_runtime.run)(request)` and returns the result. Nothing is sealed, searched or removed: the dataset is rolled back by the next `prepare`, so nothing the agent leaves survives.

### `take`

`take(stage_start, work_item_path)` is `TakeService(boundaries, snapshots.mount_point).take(stage_start, work_item_path, snapshots.changed_paths())` (see *The take*): `src/new.py` written in the dataset's checkout reaches the host when the role may write it, a changed file outside the write paths stays in `left`, and nothing of `.venv` (ignored on the host) or of `home/` is taken. The report is returned as the service gives it; a second `take` without a `prepare` between runs the service again on the dataset's changes then.

### The timing line

After the first take of a stage, one line goes to the factory log through `boundaries.log.line` (`TIMING_LINE`):

```text
2026-10-24T18:00:07Z stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s
```

Each duration is in seconds with one decimal (Python's rounding). `reset`, `sync` and `advance` are those of the last successful `prepare` of the same object (replaced by each, never added), `take` is the time of this `take`, `changed_paths` included. A `take` without a `prepare` on the object writes `0.0` for the first three. One line per stage: the first `take` after a `prepare` on the object writes it (or the first `take` on an object without a `prepare`), none after `prepare` alone. A stall after `AfterAgent`'s take (an empty entry, a broken form, a red check) is a second take: it takes again from the dataset, as the first did, and writes no line. To read the plan's measures, take the lines from `/state/factory.log`: `reset` and `advance` are the cost of the snapshots, `sync` the cost of the container with `make sync`, `take` the cost of listing the changes and copying them.

### Wiring and tests

`Boundaries.snapshots` and `Boundaries.containers` (see `watching.md`, *Boundaries*) default to `None`; `stage_environment_of` picks the container environment only when both are set. `StageRunner` builds one environment per runner, as *One environment per runner* says.

The suite's stages run on it: the `boundaries` fixture holds `FakeSnapshots(workspace, base)` and `FakeContainerRuns(workspace)` under `tmp_path` (an empty base), and `container_dataset` takes them from the fixture. The host checkout of the fixture is the upstream, with real `git` and `make` as child processes on the host (the container is played, not run). `tests/container_support.py` holds the helpers: `container_dataset`, `push_main` and `sync_makefile` (a `Makefile` whose `sync` writes a marker), `dataset_git`, `local_branches` and `timing_lines`, and the whole stage on a dataset (`whole_stage`, `assert_taken_and_pushed`). Tests: `tests/application/test_container_environment.py` (`prepare` and `run_agent`), `tests/application/test_container_environment_take.py` (the take, the timing line and a whole stage through `StageRunner` with the host's project commands), `tests/application/test_container_stage_checks.py` (the whole stage through the check container: `ContainerMakeCommands` runs the sync container and one check container per check on the taken result, and the next `prepare` starts from the pushed head with nothing left over), `tests/application/test_stage_environment_of.py`, `tests/domain/test_checks_last_line.py` and `tests/adapters/test_make_last_line_shared.py`. The wiring of the real tools is *The settings and the wiring*.

## The sync command

`make sync` is the fourth target of the project contract (`processes-and-checks.md`, *Project commands*). For a project it must bring the checkout's tools up to date and nothing else: `uv sync --frozen` in the template, the project's own command in another stack. It must work on a checkout without ignored state and end with its usual green line. The sync container's time limit is the `time_limit` of the `sync` project command, as *The sync time limit* (under *The stage environment*) says. It runs in the sync container of `prepare` and before every check.

## The agent's container

Step 5 of the cycle belongs to the agent runtimes, not to `ContainerEnvironment`: a runtime built with a `ContainerRuns` starts each call through `ContainerRuns.launch` (`container_launch` in `factory.adapters.agent_launch`) in a container of the stage image, with `/work` mounted, the login and instructions files mounted read-only at their own paths, the request's allow-list environment as `--env` entries and `/work/checkout` as the working directory, and it reads the kill at `--timeout` as `time_limit`. What it gets and what it lacks (`sudo`) is in `agents.md`, *Calls in a container*. `build_boundaries` gives the runtime of `FACTORY_AGENT_RUNTIME` its `PodmanRuns` for a `container` instance (*The settings and the wiring*).

## The take

In the container environment the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the take copies. `TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` (`factory.application.take`) applies the write paths' refusal rule (see *The take's rule*, `write-guard.md`): what the role may write goes from the dataset at `mount_point` into the work tree `boundaries.checkout`, the rest stays in the dataset. `changed_paths` are those of `Snapshots.changed_paths()`, relative to `mount_point`. `ContainerEnvironment.take` calls it (see *The container environment*).

### The seven steps

1. The baseline: the work item at `stage_start.commit`, read at the stage-start commit. When it is absent or unreadable there, `take` raises `WorkItemFormatError` naming `work_item_path`, before anything changes.
2. The write paths: `WritePathService(boundaries).at(stage_start, work_item_path)`.
3. The candidates: only paths under `checkout/` count, with that prefix removed. A path with a `.git` segment is dropped, and so is every path that `Git.ignored` names (`.venv/...`, `.reports/...`). The ignore rules asked are those of the factory's own repository on the host, never the dataset's git. A path under `home/` or anywhere else is dropped. A dropped path is neither taken nor listed.
4. The refused: a candidate is refused when `refusal(path, settings)` is not `None` (outside the write paths, or protected), or when it lies directly in an `in-progress/` folder of a feature and is not the stage's own work item (the in-progress rule). `is_refused` is the function of the rule, in `factory.application.take`. A refused path is listed in `left` and not copied; the dataset is never written.
5. The taken: every other candidate is copied with `copy_changed(mount_point / "checkout", boundaries.checkout, ...)`.
6. The work item: its state and journal are put back from the baseline with `restore_state_and_journal`, the agent's edits to its sections kept (`restore_work_item`, in `factory.application.take`). A work item that was deleted, or whose front matter cannot be read, comes back whole from the stage-start commit. `restored_work_item` is true in all those cases and false when nothing changed. A work item the role may not write is refused like any path: it is in `left`, not copied, not restored, and `restored_work_item` is false.
7. `TakeReport(left, restored_work_item)`, frozen: `left` is sorted and holds each path once.

The service makes no commit, runs no git command on the dataset and never writes under `mount_point`.

### copy_changed

`copy_changed(source, target, changed)` mirrors each `ChangedPath` from the tree at `source` into the tree at `target`. The take uses it, and so does the check container's copy of the work tree (*The checks* below). Every path is first checked with `check_repository_path`: an absolute path or one with a `..` segment raises `ValueError` naming it, before anything is copied.

- `added` or `modified`: the entry at `target / path` is removed first (a link as the link, a folder with what it holds), then the source's entry is placed. A regular file arrives with its bytes and mode, so an executable bit stays. A symbolic link arrives as a link with the same target text and is never followed.
- `deleted`: the entry at `target / path` is removed, a link as the link with its target untouched. A missing entry, a dangling link included, is no fault.
- Parent folders: nothing is ever written or removed outside the target tree. For `added` or `modified`, each parent from `target` down is checked with `lstat`; a parent that is a link or no folder is removed (a link as the link) and made a real folder, so the entry lands inside the target. For `deleted`, a parent that is a link or missing means the entry is not in the tree: nothing is removed and nothing is followed.

### Errors

`WorkItemFormatError` (step 1), `ValueError` from `copy_changed`, and `GitError` from `ignored` (see *The git wrapper*, `git-and-hosting.md`). A `ValueError` or `GitError` can come after the baseline was read but before step 5 copies anything.

Tests: `tests/application/test_take.py` and `tests/application/test_take_edges.py`, built on `tests/undo_support.py` and `tests/take_support.py` with a dataset folder in `tmp_path`; `tests/adapters/test_git_cli_check_ignore.py` for `ignored`.

## The checks

Step 7 of the cycle in `planning/v1.2-plan.md` ("The cycle of a stage"): the stage's checks see the taken result on a clean base. `ContainerMakeCommands` (`factory.adapters.make_commands`) does it for every project command: it rolls the dataset back to the base, copies in the files the take brought into the host's work tree, and runs `make sync && make <command>` in a container with the command's time limit. The steps, the environment and the faults are in `processes-and-checks.md`, *Container project commands*. A file a check makes stays in its container's dataset and is reset away by the next run; it never reaches the host.

What is copied is what differs from `HEAD` on the host (`git.changed_paths("HEAD")`), not a list the take kept. After the take that is the taken files, the restored work item and the factory's cost record; at the preflight's `lint` on `main` it is nothing. Nothing is remembered between the take and the checks (decision 7 of the feature): `HEAD` and the host's work tree already say what the take brought, so no list is kept that could disagree with them. The copy is `copy_changed`, the take's own mirror, so the two directions share one rule for links, modes, deletions and refused paths.

## The settings and the wiring

An instance names its dataset, workspace and stage image in its environment variables (`factory.domain.settings`; the operator guide, *Configuration*, has the table).

| Variable | `InstanceSettings` field | Default |
|---|---|---|
| `FACTORY_DATASET` | `dataset` | none |
| `FACTORY_WORKSPACE` | `workspace` (`Path`) | none |
| `FACTORY_STAGE_IMAGE` | `stage_image` | none |
| `FACTORY_PODMAN` | `podman_executable` | `podman` |
| `FACTORY_ZFS` | `zfs_executable` | `zfs` |

`read_settings` strips each value and reads a blank one as unset. It raises no fault for a missing dataset, workspace or image. It refuses a relative workspace (`SettingsInvalid(FACTORY_WORKSPACE, "is not an absolute path")`) and then a `checkout` and then a `state_directory` that is the workspace or lies inside it (`Path.is_relative_to`, by path parts): `SettingsInvalid(FACTORY_CHECKOUT, "<checkout> lies inside FACTORY_WORKSPACE")`, or the same for `FACTORY_STATE`.

One function, `workspace_overlap_fault(workspace, checkout, state_directory)` (`factory.domain.settings`), holds that rule and gives `None` for a `None` workspace. `read_settings` calls it, and so does the model validator of `InstanceSettings`, so a model built directly refuses the same combinations with a `ValidationError` (the validator's message is `<variable>: <fault>`; it is not turned back into a `SettingsInvalid`).

`build_boundaries(settings, token, *, hosting=None)` (`factory.entry.wiring`) refuses an incomplete instance first, before it builds anything and before PyGithub's `get_repo` is called: `_container_adapters` raises `SettingsInvalid(FACTORY_DATASET, "missing")`, then `SettingsInvalid(FACTORY_WORKSPACE, "missing")`, then `SettingsInvalid(FACTORY_STAGE_IMAGE, "missing")`, the first of the three that is `None`. Then it builds:

| Boundary | Built as |
|---|---|
| `snapshots`, `containers` | `ZfsSnapshots(dataset, workspace, executable=zfs_executable)` and `PodmanRuns(podman_executable, stage_image, workspace)` |
| `agent_runtime` | the runtime of `FACTORY_AGENT_RUNTIME` given `containers` |
| `project_commands` | `RecordingProjectCommands` around `ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout)` |

`build_boundaries` takes no `which`. It runs no tool: `zfs` and `podman` start only when a stage uses them. `RecordingProjectCommands.inner` is the implementation it records, which the wiring's tests read.

`agent_run_environment(settings, base)` copies `base` and sets `HOME` to `/work/home` (`WORK_HOME_ENVIRONMENT`), on the dataset, whatever the settings; the dict it is given is unchanged. The preflight's items are in *The preflight* below. Tests: `tests/domain/test_settings_stage_environment.py`, `tests/domain/test_settings_one_environment.py`, `tests/entry/test_wiring_stage_environment.py` and `tests/entry/test_wiring_one_environment.py`.

## The preflight

The preflight (`factory.application.preflight`; the tick, the stamp and the stops are in `watching.md`) has one list of items. `machine_extras` (`factory.entry.wiring`) gives, in this order: `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode` under opencode only, `agent-run-probe`. It builds a `ZfsSnapshots` and a `PodmanRuns` of its own through `_container_adapters`, the function `build_boundaries` also calls, because `boundaries.snapshots` and `boundaries.containers` are typed as the interfaces and nothing narrows them. Building them runs no command.

The four items that reach the machine take callables, so `application` knows no adapter:

| Item | Function | Callable | Fails with |
|---|---|---|---|
| `podman`, `zfs` | `tool_version_item(name, version)` | `PodmanRuns.version`, `ZfsSnapshots.version` | `<name> does not answer --version: <error>` on `SnapshotError` or `ContainerError`; passes with the printed line as its detail |
| `dataset` | `dataset_item(dataset, exists)` | `ZfsSnapshots.dataset_exists` | `the dataset <dataset> does not exist; make it with zfs create, and its base with zfs snapshot <dataset>@base`, or `cannot list the dataset <dataset>: <error>` on `SnapshotError` |
| `stage-image` | `stage_image_item(image, exists)` | `PodmanRuns.image_exists` | `the stage image <image> is not built; build it with podman build`, or `cannot look for the stage image <image>: <error>` on `ContainerError` |

`MachineChecks.run` checks `REQUIRED_TOOLS` (`git`, `uv`) and asks for no runtime executable on the host: no `tool:make` (it runs only in the sync and check containers) and no `tool:claude` or `tool:opencode` (the executable is the stage image's; `agent-runtime-version` runs it there and is the check of its presence). There is no `agent-environment` item: the agent's `HOME` is a path inside the container. `opencode_item(settings, agent_models)` checks the aliases only.

Both probes go through the environment like a stage. `agent_run_probe_item` resolves `origin/main` (none fails the item with `no origin/main to prepare the stage environment from`, and no run starts), calls `stage_environment_of(boundaries).prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)` and then `run_agent` on the same object; `SnapshotError` and `ContainerError` from `prepare` fail the item with their message. `Preflight._run_probe` calls the same `prepare` after it puts the checkout on `main` and before `lint`; `Preflight.run` catches both errors beside `GitError` and `ProjectCommandError` and stops with `the probe on main could not run: <error>`.

Tests: `tests/application/test_container_items.py`, `test_opencode_item_container.py`, `test_machine_checks_container.py`, `test_agent_run_probe_environment.py`, `test_preflight_run_environment.py` and `tests/entry/test_wiring_container_extras.py`.
