# The stage environment

This file covers the two interfaces through which the factory reaches the dataset a stage runs on and the containers its commands run in, and their fakes; read the index, `README.md`, first. The modules are `factory.application.stage_environment`, `factory.application.snapshots`, `factory.application.containers`, `factory.application.take`, `factory.domain.containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.podman_runs`, `factory.adapters.printed_output`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. The stage protocol already calls the stage environment (*The stage environment*, first below), but only its inline implementation exists: nothing wires `ZfsSnapshots` or `PodmanRuns`, and the container environment that will use them comes in a later story of the same feature.

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

`InlineEnvironment` is the only module that calls `run_sealed` and `UndoService` for a stage. `StallService` still calls the undo itself after a stall; the stall's take under the container environment is a later story.

`stage_environment_of(boundaries)` gives the environment the boundaries describe. For now it is always an `InlineEnvironment`; the container environment will be chosen here.

### Who calls what

- `StageLauncher.launch`, after the claim is pushed and the pull request ensured and before the cost record begins: `prepare(stage_start.commit, branch, sync_time_limit=...)`, then `run_agent(request, run=PatientRuns(boundaries).run)`. An error from `prepare` ends the launch like one from the agent runtime, after the claim and before any run or cost record.
- `AfterAgent.process`: `take(started.stage_start, started.path)` at the point where the undo was, once the result and the decision are accepted. `AgentAftermath.take` carries the report, and the entry's closing paragraph names `take.left` (see `stages.md`, *After the agent run*).
- `agent_run_probe_item` (the preflight): `stage_environment_of(boundaries).run_agent(request)`. `factory.application.preflight` does not import `run_sealed`, so the probe cannot bypass the environment; a test pins that.
- `StageFinisher` does not use the environment: the checks go through `boundaries.project_commands`.

### The sync time limit

`StageLauncher` takes the limit from the pipeline definition: the `time_limit` of its `sync` project command, in minutes, and when the definition has no `sync` command the default of a project command, `ProjectCommandDefinition().time_limit` (10 minutes). The inline environment ignores it.

### One environment per runner

`StageLauncher` and `AfterAgent` take an optional keyword `stage_environment`; `None` means `stage_environment_of(boundaries)`. `StageRunner` builds one environment and gives it to both, so that the object that saw a stage's `prepare` sees its `take`.

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

In the container environment the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the take copies. `TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` (`factory.application.take`) is the write-path refusal of the undo (see *The undo*, `write-guard.md`) applied the other way round: what the role may write goes from the dataset at `mount_point` into the work tree `boundaries.checkout`, the rest stays in the dataset. `changed_paths` are those of `Snapshots.changed_paths()`, relative to `mount_point`. Nothing calls the service yet; the container environment will.

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

`copy_changed(source, target, changed)` mirrors each `ChangedPath` from the tree at `source` into the tree at `target`. The take uses it, and so will the check container's copy of the work tree. Every path is first checked with `check_repository_path`: an absolute path or one with a `..` segment raises `ValueError` naming it, before anything is copied.

- `added` or `modified`: the entry at `target / path` is removed first (a link as the link, a folder with what it holds), then the source's entry is placed. A regular file arrives with its bytes and mode, so an executable bit stays. A symbolic link arrives as a link with the same target text and is never followed.
- `deleted`: the entry at `target / path` is removed, a link as the link with its target untouched. A missing entry, a dangling link included, is no fault.
- Parent folders: nothing is ever written or removed outside the target tree. For `added` or `modified`, each parent from `target` down is checked with `lstat`; a parent that is a link or no folder is removed (a link as the link) and made a real folder, so the entry lands inside the target. For `deleted`, a parent that is a link or missing means the entry is not in the tree: nothing is removed and nothing is followed.

### Errors

`WorkItemFormatError` (step 1), `ValueError` from `copy_changed`, and `GitError` from `ignored` (see *The git wrapper*, `git-and-hosting.md`). A `ValueError` or `GitError` can come after the baseline was read but before step 5 copies anything.

Tests: `tests/application/test_take.py` and `tests/application/test_take_edges.py`, built on `tests/undo_support.py` and `tests/take_support.py` with a dataset folder in `tmp_path`; `tests/adapters/test_git_cli_check_ignore.py` for `ignored`.

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
