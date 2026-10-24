# The stage environment

This file covers the two interfaces through which the factory reaches the dataset a stage runs on and the containers its commands run in, and their fakes; read the index, `README.md`, first. The modules are `factory.application.stage_environment`, `factory.application.snapshots`, `factory.application.containers`, `factory.application.take`, `factory.domain.containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.podman_runs`, `factory.adapters.printed_output`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. The stage protocol calls the stage environment (*The stage environment*, first below). Its inline implementation is what runs: the container environment (*The container environment*, after the take) is built and tested on the fakes, but nothing wires `ZfsSnapshots`, `PodmanRuns` or the two new `Boundaries` fields yet, so no instance chooses it.

## The stage environment

`StageEnvironment` (`factory.application.stage_environment`) is the one object the stage protocol calls for the cycle of a stage: it prepares the place the agent works in, runs the agent there, and takes the result back into the factory's work tree. It is an abstract base class with three operations; the stage protocol knows no `podman`, `zfs` or `sudo`.

### The three operations

- `prepare(commit, branch, *, sync_time_limit)`: makes the place hold `branch` at `commit`, its tools synced. `SnapshotError` or `ContainerError` when that cannot be done; the sync's container gets `sync_time_limit`.
- `run_agent(request, *, run=None)`: runs the request's agent in this environment and returns a `SealedRun` (`factory.application.sealed_runs`: the `result` and the `nested_repositories` removed after it). With `run` the environment calls it once instead of the boundaries' runtime; whatever it does inside, such as the resumes of `PatientRuns` after a provider limit, happens in the same prepared place.
- `take(stage_start, work_item_path)`: brings the agent's result into the work tree as far as the role may write, and returns a `TakeReport` (`left`, `restored_work_item`; see *The take*). `WorkItemFormatError` naming `work_item_path` when the work item is absent or unreadable at the stage-start commit; the work tree is then left untouched.

### The inline environment

`InlineEnvironment(boundaries)` is v1.1's way, the agent in the factory's own checkout:

- `prepare` does nothing and reads nothing: the claim has left the checkout on the branch at the stage-start commit. Its arguments are accepted and ignored.
- `run_agent` is `run_sealed(boundaries, request, run=run)`: the checkout's git folder is sealed around the run, the agent home is reset, the nested repositories and the ignored paths are removed (see `watching.md`, *Boundaries*).
- `take` is `UndoService(boundaries).undo(stage_start, work_item_path)` (see *The undo*, `write-guard.md`) turned into a report: `left` is the undo's `reverted` and `deleted` paths, joined, sorted, each once; `restored_work_item` is the undo's.

`InlineEnvironment` is the only module that calls `run_sealed` and `UndoService` for a stage. `StallService` reaches the undo only through this environment: its stall takes like `AfterAgent` does.

`stage_environment_of(boundaries)` gives the environment the boundaries describe. It gives a `ContainerEnvironment` when `boundaries.snapshots` and `boundaries.containers` are both set, and an `InlineEnvironment` when one or both is `None` (see *The container environment*).

### Who calls what

- `StageLauncher.launch`, after the claim is pushed and the pull request ensured and before the cost record begins: `prepare(stage_start.commit, branch, sync_time_limit=...)`, then `run_agent(request, run=PatientRuns(boundaries).run)`. An error from `prepare` ends the launch like one from the agent runtime, after the claim and before any run or cost record.
- `AfterAgent.process`: `take(started.stage_start, started.path)` at the point where the undo was, once the result and the decision are accepted. `AgentAftermath.take` carries the report, and the entry's closing paragraph names `take.left` (see `stages.md`, *After the agent run*).
- `agent_run_probe_item` (the preflight): `stage_environment_of(boundaries).run_agent(request)`. `factory.application.preflight` does not import `run_sealed`, so the probe cannot bypass the environment; a test pins that.
- `StallService.stall`, with a stage start, after the checkout is put back on the work item's branch: `take(context.stage_start, context.path)`, whatever the reason (`check_red` included), and its report is `StallResult.take`. A stall after `AfterAgent`'s take is a second take within one stage. `StageFinisher` takes only through its stall service: the checks go through `boundaries.project_commands`.

### The sync time limit

`StageLauncher` takes the limit from the pipeline definition: the `time_limit` of its `sync` project command, in minutes, and when the definition has no `sync` command the default of a project command, `ProjectCommandDefinition().time_limit` (10 minutes). The inline environment ignores it.

### The sync command

`make sync` is the fourth target of the project contract (`processes-and-checks.md`, *Project commands*). For a project it must bring the checkout's tools up to date and nothing else: `uv sync --frozen` in the template, the project's own command in another stack. It must work on a checkout without ignored state and end with its usual green line. The sync container's time limit is the `time_limit` of the `sync` project command, as *The sync time limit* says.

### One environment per runner

`StageLauncher`, `AfterAgent`, `StageFinisher` and `StallService` take an optional keyword `stage_environment`; `None` means `stage_environment_of(boundaries)`. `StageRunner` builds one environment and gives it to all four, so that the object that saw a stage's `prepare` sees its `take`.

Tests: `tests/application/test_stage_environment.py` (the interface and the inline environment against `run_sealed` and the undo), `tests/application/test_stage_environment_calls.py` (a stand-in environment that records its calls, given to `StageLauncher` and `AfterAgent`), and the interface's row in `tests/application/test_interfaces.py`.

## The snapshots

`Snapshots` (`factory.application.snapshots`) stands for one dataset and its base snapshot. It is an abstract base class like every interface (see `CLAUDE.md`), so another snapshot tool can implement it later. Its members:

- `mount_point` (property): the dataset's path on the host. `changed_paths` are relative to it.
- `reset()`: puts the dataset back to the base.
- `advance()`: moves the base to the dataset's current state; what the base held before is gone.
- `changed_paths()`: every non-directory entry that differs from the base, as `ChangedPath` (`factory.domain.git`: `path` and `change`, one of `added`, `modified`, `deleted`), sorted by path.

`changed_paths` lists files and symbolic links. It never lists a directory, also an empty one, and a rename is a deletion and an addition. `reset` and `changed_paths` need a base: without one they raise `SnapshotError`.

`SnapshotError(command, detail)` (`factory.domain.errors`, a `BoundaryError`) is the one error of the interface: a snapshot command failed, could not start or reached its time limit. The message is `snapshot command <command> failed: <detail>`; `command` and `detail` are attributes.

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

## The container runs

`ContainerRuns` (`factory.application.containers`) runs one command at a time in a fresh container on the dataset. The dataset is mounted at `/work` in every container. `factory.domain.containers` names its places: `WORK` (`/work`), `WORK_CHECKOUT` (`/work/checkout`) and `WORK_HOME` (`/work/home`).

Both operations take the command words and, by keyword, `mounts`, `environment`, `time_limit` and `working_directory`:

- `launch(...)` returns a `ContainerLaunch`: the `argv`, the `env` and the `time_limit` that start the command in a container. It runs nothing. A caller that starts the process itself, for example under the write guard, uses it. `env` of `None` means the process's own environment.
- `run(...)` runs the command until it ends or reaches `time_limit` and returns a `ContainerResult`: `exit_status`, the merged `output`, `timed_out` and `duration`. `exit_status` is `None` exactly when `timed_out` is true (a model validator). A command that fails or times out is a result; `ContainerError` means the container could not be started.

A `Mount` has a `source` (an absolute host path), a `target` (a container path) and `read_only` (default false). A target starts with `/` and has no empty segment and no `..` segment, so `/`, `a/b`, `/a//b`, `/a/` and `/a/../b` are refused with `ValidationError`; `/a/./b` is accepted. The dataset is the fixed `/work` mount of every run, so both operations raise `ValueError` for a mount whose target is `/work` or lies under it, and for a command without words. `check_container_call` (`factory.domain.containers`) is that rule; the fake and the podman adapter both call it.

`ContainerError(command, detail)` is the interface's `BoundaryError`, with the message `container command <command> failed: <detail>`. `ContainerCall` records one call as it was asked; only the fake uses it.

## The podman adapter

`PodmanRuns(executable, image, workspace, *, time_limit=PODMAN_TIME_LIMIT)` (`factory.adapters.podman_runs`) implements `ContainerRuns` with the `podman` executable: every command runs in a throwaway container of `image`, `workspace` (the dataset's mount point) mounted at `/work`. `executable` is run as given, so an operator can pass a wrapper script. `time_limit` bounds only `version` and `image_exists`; `PODMAN_TIME_LIMIT` is two minutes.

### The command line

`launch` builds these words, in this order:

```
<executable> run --rm --userns=keep-id --timeout <seconds>
    --env NAME=value ...
    --volume <workspace>:/work --volume <source>:<target>[:ro] ...
    --workdir <working_directory> <image> <command...>
```

- `--rm`: the container is removed when it ends, so nothing of one command is left for the next.
- `--userns=keep-id`: rootless podman maps the container's user to the host user that runs podman, the `factory` user. Files the command writes into `/work` belong to that user on the host.
- `--timeout <seconds>`: the container runtime ends the container at the limit. The seconds are the limit rounded up (`30s` is `30`, 1.5 seconds is `2`).
- `--env NAME=value`: one pair per entry of `environment`, in its order. These are the only variables the command gets besides the image's own. Podman does not pass the factory's environment into the container, so a token or a path the factory holds reaches a command only when a caller names it here.
- `--volume`: the workspace at `/work` comes first, then the given mounts in their order. A read-only mount gets `:ro`. A rootless container cannot write a `:ro` bind mount, and that is the whole protection of the host's repository and of the login files: a command can read them and never change them. The tests pin the words, `:ro` above all.
- `--workdir`: the command's working directory in the container.
- the image, then the command words, which are never joined into a string.

`launch` returns `ContainerLaunch(argv, env=None, time_limit=<limit> + CONTAINER_GRACE)`. `env` is `None`: the `podman` program itself runs with the factory's environment (`HOME`, `XDG_RUNTIME_DIR` and `PATH` it needs), as `version` does.

### The grace

`CONTAINER_GRACE` is 30 seconds. The process request carries the limit plus the grace, so podman's `--timeout` fires first and the factory's own kill is the second line, for a podman that does not end. A `timed_out` result therefore usually comes from podman's kill, not the factory's.

### Reading the end

`run` starts the launch's words through `run_process` (`factory.adapters.process`; `tests/test_wrapper_search.py` names the module) with the working directory `/` (podman reads no file from it; a missing workspace is podman's own fault, 125), the factory's environment and standard error merged into `output`.

- `timed_out` is true when `run_process` says so, or when the exit status is in `KILL_STATUSES` (`factory.adapters.agent_launch`: 137 and -9) and the run lasted at least `time_limit`: podman's `--timeout` sent the kill. `exit_status` is then `None`.
- The same statuses before the limit are the command's own, as is any other status at or after the limit.
- Otherwise `exit_status` is podman's, which is the command's. Podman exits 125 for its own faults, such as a missing image; the result says 125 and podman's message is in `output`.
- That podman exits 137 for a container its `--timeout` ended is an assumption; it is measured on the VM (F0043, story 4).
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

No test runs a real `podman`; it runs only on the VM. `tests/podman_support.py` writes a stand-in `podman` into `tmp_path`. It records its arguments, environment and working directory; it prints planned output, waits and exits with a planned status, or, when its arguments hold the image, runs the words after the image on the host, so that a command's own exit status and output pass through. Tests of the default limit and of the kill rule replace the module's `run_process` with the `Recorder` of `tests/run_process_recorder.py`. The tests are `tests/adapters/test_podman_runs.py` (the command line) and `tests/adapters/test_podman_runs_results.py` (results and faults).

## The take

In the container environment the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the take copies. `TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` (`factory.application.take`) is the write-path refusal of the undo (see *The undo*, `write-guard.md`) applied the other way round: what the role may write goes from the dataset at `mount_point` into the work tree `boundaries.checkout`, the rest stays in the dataset. `changed_paths` are those of `Snapshots.changed_paths()`, relative to `mount_point`. `ContainerEnvironment.take` calls it (see *The container environment*).

### The seven steps

1. The baseline: the work item at `stage_start.commit`, read as the undo reads it. When it is absent or unreadable there, `take` raises `WorkItemFormatError` naming `work_item_path`, before anything changes.
2. The write paths: `WritePathService(boundaries).at(stage_start, work_item_path)`.
3. The candidates: only paths under `checkout/` count, with that prefix removed. A path with a `.git` segment is dropped, and so is every path that `Git.ignored` names (`.venv/...`, `.reports/...`). The ignore rules asked are those of the factory's own repository on the host, never the dataset's git. A path under `home/` or anywhere else is dropped. A dropped path is neither taken nor listed.
4. The refused: a candidate is refused when `refusal(path, settings)` is not `None` (outside the write paths, or protected), or when it lies directly in an `in-progress/` folder of a feature and is not the stage's own work item (the undo's second rule). `is_refused` is the undo's own function, shared. A refused path is listed in `left` and not copied; the dataset is never written.
5. The taken: every other candidate is copied with `copy_changed(mount_point / "checkout", boundaries.checkout, ...)`.
6. The work item: its state and journal are put back from the baseline with `restore_state_and_journal`, the agent's edits to its sections kept (the undo's `restore_work_item`, shared, not copied). A work item that was deleted, or whose front matter cannot be read, comes back whole from the stage-start commit. `restored_work_item` is true in all those cases and false when nothing changed. A work item the role may not write is refused like any path: it is in `left`, not copied, not restored, and `restored_work_item` is false.
7. `TakeReport(left, restored_work_item)`, frozen: `left` is sorted and holds each path once.

The service makes no commit, runs no git command on the dataset and never writes under `mount_point`. `read_baseline`, `restore_work_item` and `is_refused` were private to `factory.application.undo` and are now public for this; the undo's behaviour did not change.

### copy_changed

`copy_changed(source, target, changed)` mirrors each `ChangedPath` from the tree at `source` into the tree at `target`. The take uses it, and so does the check container's copy of the work tree (*The checks* below). Every path is first checked with `check_repository_path`: an absolute path or one with a `..` segment raises `ValueError` naming it, before anything is copied.

- `added` or `modified`: the entry at `target / path` is removed first (a link as the link, a folder with what it holds), then the source's entry is placed. A regular file arrives with its bytes and mode, so an executable bit stays. A symbolic link arrives as a link with the same target text and is never followed.
- `deleted`: the entry at `target / path` is removed, a link as the link with its target untouched. A missing entry, a dangling link included, is no fault.
- Parent folders: nothing is ever written or removed outside the target tree. For `added` or `modified`, each parent from `target` down is checked with `lstat`; a parent that is a link or no folder is removed (a link as the link) and made a real folder, so the entry lands inside the target. For `deleted`, a parent that is a link or missing means the entry is not in the tree: nothing is removed and nothing is followed.

### Errors

`WorkItemFormatError` (step 1), `ValueError` from `copy_changed`, and `GitError` from `ignored` (see *The git wrapper*, `git-and-hosting.md`). A `ValueError` or `GitError` can come after the baseline was read but before step 5 copies anything.

Tests: `tests/application/test_take.py` and `tests/application/test_take_edges.py`, built on `tests/undo_support.py` and `tests/take_support.py` with a dataset folder in `tmp_path`; `tests/adapters/test_git_cli_check_ignore.py` for `ignored`.

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
4. fetches `+refs/heads/*:refs/heads/*` from `$3` with `--prune` and `--update-head-ok`: every branch, not only the stage's, because a detached checkout would leave the agent without `main` and the branch, and the coder's and reviewer's instructions read `git diff main` and the branch's log (decision 5); `--prune` drops a branch deleted on the host; `--update-head-ok` because git refuses to fetch into the checked-out branch, an unborn one included, as a fresh `git init` has;
5. `git checkout -q -f "$5"` and `git reset -q --hard "$6"`, so `HEAD` is on the branch at the stage-start commit and never detached;
6. `make sync` (see *The sync command*).

The first `prepare` on a dataset creates the repository; the next ones reuse it, and objects of earlier stages stay in it.

### What a fault leaves behind

- `reset` fails (`SnapshotError`, for example a dataset without a base): nothing else ran, `containers` was not called.
- The sync fails or times out: the dataset holds whatever the script did, and the base did **not** move. `snapshots.changed_paths()` is not empty, and the next `reset()` empties the dataset again. The stage ends with the error before any agent runs.
- The commit is no commit: `git reset` fails, the detail is git's message.
- The durations of a failed `prepare` are not kept: the timing line keeps those of the last successful one (the stage stops at the error, so no `take` follows).

### `run_agent`

`run_agent(request, *, run=None)` calls `(run or boundaries.agent_runtime.run)(request)` and returns `SealedRun(result=<it>, nested_repositories=[])`. There is no seal of the git folder, no home reset, no search for nested repositories and no removal of ignored paths: the dataset is rolled back by the next `prepare`, so nothing the agent leaves survives.

### The agent's container

Step 5 of the cycle belongs to the agent runtimes, not to `ContainerEnvironment`: a runtime built with a `ContainerRuns` starts each call through `ContainerRuns.launch` (`container_launch` in `factory.adapters.agent_launch`) in a container of the stage image, with `/work` mounted, the login and instructions files mounted read-only at their own paths, the request's allow-list environment as `--env` entries and `/work/checkout` as the working directory, and it reads the kill at `--timeout` as `time_limit`. What it gets and what it lacks (`sudo`, `factory-confine`, a rules file, leftovers, a temporary folder) is in `agents.md`, *Calls in a container*. The wiring that gives a `container` instance's runtimes their `PodmanRuns` is a later story's.

### `take`

`take(stage_start, work_item_path)` is `TakeService(boundaries, snapshots.mount_point).take(stage_start, work_item_path, snapshots.changed_paths())` (see *The take*): `src/new.py` written in the dataset's checkout reaches the host when the role may write it, a changed file outside the write paths stays in `left`, and nothing of `.venv` (ignored on the host) or of `home/` is taken. The report is returned as the service gives it; a second `take` without a `prepare` between runs the service again on the dataset's changes then.

### The timing line

After the first take of a stage, one line goes to the factory log through `boundaries.log.line` (`TIMING_LINE`):

```text
2026-10-24T18:00:07Z stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s
```

Each duration is in seconds with one decimal (Python's rounding). `reset`, `sync` and `advance` are those of the last successful `prepare` of the same object (replaced by each, never added), `take` is the time of this `take`, `changed_paths` included. A `take` without a `prepare` on the object writes `0.0` for the first three. One line per stage: the first `take` after a `prepare` on the object writes it (or the first `take` on an object without a `prepare`), none after `prepare` alone. A stall after `AfterAgent`'s take (an empty entry, a broken form, a red check) is a second take: it takes again from the dataset, as the first did, and writes no line. To read the plan's measures, take the lines from `/state/factory.log`: `reset` and `advance` are the cost of the snapshots, `sync` the cost of the container with `make sync`, `take` the cost of listing the changes and copying them. The inline environment writes no such line.

### Wiring and tests

`Boundaries.snapshots` and `Boundaries.containers` (see `watching.md`, *Boundaries*) default to `None`; `stage_environment_of` picks the container environment only when both are set. `StageRunner` builds one environment per runner, as *One environment per runner* says.

The suite runs it on `FakeSnapshots(workspace, base)` and `FakeContainerRuns(workspace)` under `tmp_path`, the host checkout of the `boundaries` fixture as the upstream, with real `git` and `make` as child processes on the host (the container is played, not run). `tests/container_support.py` holds the helpers: `container_dataset`, `push_main` and `sync_makefile` (a `Makefile` whose `sync` writes a marker), `dataset_git`, `local_branches` and `timing_lines`. Tests: `tests/application/test_container_environment.py` (`prepare` and `run_agent`), `tests/application/test_container_environment_take.py` (the take, the timing line and a whole stage through `StageRunner`), `tests/application/test_stage_environment_of.py`, `tests/domain/test_checks_last_line.py` and `tests/adapters/test_make_last_line_shared.py`. The real tools come with the wiring of a later story.

## The checks

Step 7 of the cycle in `planning/v1.2-plan.md` ("The cycle of a stage"): the stage's checks see the taken result on a clean base. `ContainerMakeCommands` (`factory.adapters.make_commands`) does it for every project command: it rolls the dataset back to the base, copies in the files the take brought into the host's work tree, and runs `make sync && make <command>` in a container with the command's time limit. The steps, the environment and the faults are in `processes-and-checks.md`, *Container project commands*. A file a check makes stays in its container's dataset and is reset away by the next run; it never reaches the host.

What is copied is what differs from `HEAD` on the host (`git.changed_paths("HEAD")`), not a list the take kept. After the take that is the taken files, the restored work item and the factory's cost record; at the preflight's `lint` on `main` it is nothing. Nothing is remembered between the take and the checks (decision 7 of the feature): `HEAD` and the host's work tree already say what the take brought, so no list is kept that could disagree with them. The copy is `copy_changed`, the take's own mirror, so the two directions share one rule for links, modes, deletions and refused paths.

## The fakes

Both fakes let the suite and the smoke tests run without `zfs` and `podman`.

`FakeSnapshots(folder, base)` keeps the base as a copy of `folder` at `base`. `advance` replaces `base` with a copy (folders, files with their bytes and mode, symbolic links as links, never followed). `reset` replaces the contents of `folder` with a copy of `base`; `folder` itself stays, as a mount point does. `changed_paths` walks both trees and compares bytes, mode and link target. It starts no process. Without a `base` folder, `reset` and `changed_paths` raise `SnapshotError("reset" or "changed_paths", "no base at <base>")` and `reset` changes nothing.

`FakeContainerRuns(workspace)` plays a container as a child process on the host, through `run_process` (`factory.adapters.process`; the structural test `tests/test_wrapper_search.py` names this module as one that reaches it). It maps container paths to host folders:

- The mounts given plus a fixed mount of `workspace` at `/work`. A command word, an `environment` value or the `working_directory` that equals a target, or starts with the target and a `/`, has that target replaced by the mount's `source`. The longer target wins; `/workspace` is not under `/work`. Keys of `environment` are never mapped.
- `launch` returns `/bin/sh -c 'cd "$1" && shift && exec "$@"' fake-container <working directory> <command...>`, all mapped, with the time limit as given.
- `run` starts those words with the mapped working directory and environment and the merged output. A program the shell cannot find is a result with exit status 127. A child that cannot be started, such as a working directory that does not exist, is `ContainerError(command[0], <operating system's message>)`.
- `calls` lists every accepted `launch` and `run` as `ContainerCall`, before the mapping. A call refused with `ValueError` is not recorded.

What the fake cannot do: it does not enforce `read_only` (a mount is only a path mapping), isolates nothing, and the command sees the host's programs.

Tests: `tests/domain/test_containers.py`, `tests/domain/test_errors_environment.py`, `tests/application/test_snapshots_interface.py`, `tests/application/test_containers_interface.py` (and the two interfaces in `tests/application/test_interfaces.py`), `tests/adapters/test_fake_snapshots.py` and `tests/adapters/test_fake_containers.py`. The fakes' tests work in `tmp_path` and start only `/bin/sh` and `printf`.
