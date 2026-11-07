# The machine: the stage environment and the project commands

This file covers the area `machine`: the places a [stage](glossary.md) runs in, behind interfaces, and the [project commands](glossary.md). Read the index, [README.md](README.md), first. The exact detail (every command line, fault message and setting) is in the *Reference* at the end.

## The cycle

A stage runs in eight steps, and the [stage environment](glossary.md) does steps 2 to 4 and 6. The factory claims the stage, then asks the environment to prepare a place, run the agent there and take the result back. The sections below describe each step.

1. The factory claims the stage and commits the [claim](glossary.md), outside the environment (see [pipeline.md](pipeline.md)).
2. `prepare` rolls the [dataset](glossary.md) back to its [base](glossary.md) (*The snapshots*, *The container environment*).
3. `prepare` syncs the checkout in a sync container (*The sync command*, *The container runs*).
4. `prepare` moves the base forward to the synced dataset (*The snapshots*).
5. `run_agent` runs the agent in its own container (*The agent's container*).
6. `take` copies what the [role](glossary.md) may write into the factory's work tree, the [take](glossary.md) (*The take*).
7. The stage's checks run on a clean base with the taken files (*The checks*).
8. The factory commits and pushes what it took, and decides the stage (see [pipeline.md](pipeline.md)).

There is one environment: the dataset and the containers. The settings that choose the tools are in *The settings and the wiring*, and the operator's side is in [machine.md](../operator-guide/machine.md) of the operator guide.

## The snapshots

The dataset a stage runs on has one snapshot, the base. Before each stage the factory puts the dataset back to the base, so nothing an earlier run left is read. `Snapshots` stands for the dataset and its base, in [snapshots.py](../../src/factory/machine/application/snapshots.py), the module `factory.machine.application.snapshots`. It is an abstract base class, so another snapshot tool can implement it. Two real classes implement it: `ZfsSnapshots` (*The ZFS adapter*) and `CopySnapshots` (*The copy snapshots*). `FACTORY_SNAPSHOTS` chooses between them.

    Snapshots.mount_point -> Path
    Snapshots.reset() -> None
    Snapshots.advance() -> None
    Snapshots.changed_paths() -> list[ChangedPath]

- `mount_point` is the dataset's path on the host. `changed_paths` are relative to it.
- `reset()` puts the dataset back to the base.
- `advance()` moves the base to the dataset's current state. What the base held before is gone.
- `changed_paths()` lists every non-directory entry that differs from the base, sorted by path. Each is a `ChangedPath` with `path` and `change`, one of `added`, `modified`, `deleted`, defined in [git.py](../../src/factory/hosting/domain/git.py) (`factory.hosting.domain.git`).
- It lists files and symbolic links. It never lists a directory, an empty one included, and a rename is a deletion and an addition.
- `reset` and `changed_paths` need a base. Without one they raise `SnapshotError`.
- `SnapshotError(command, detail)` in [errors.py](../../src/factory/shared/domain/errors.py) is a `BoundaryError` and the one error of the interface: a snapshot command failed, could not start or reached its time limit. The message is `snapshot command <command> failed: <detail>`, and `command` and `detail` are attributes.

See also: *The ZFS adapter*, *The copy snapshots* and *The fakes*.

## The container runs

Every command of a stage runs in a fresh container with the dataset mounted at `/work`. `ContainerRuns` runs one command at a time. It is in [containers.py](../../src/factory/machine/application/containers.py), the module `factory.machine.application.containers`. The places of a container are named in [containers.py](../../src/factory/machine/domain/containers.py) (`factory.machine.domain.containers`): `WORK` (`/work`), `WORK_CHECKOUT` (`/work/checkout`) and `WORK_HOME` (`/work/home`).

    ContainerRuns.launch(command, *, mounts, environment, time_limit, working_directory) -> ContainerLaunch
    ContainerRuns.run(command, *, mounts, environment, time_limit, working_directory) -> ContainerResult
    Mount(source, target, read_only=False)
    check_container_call(command, mounts) -> None

- `launch` returns a `ContainerLaunch` (`argv`, `env` and `time_limit`) that starts the command in a container, and runs nothing. A caller that starts the process itself uses it. An `env` of `None` means the process's own environment.
- `run` runs the command until it ends or reaches `time_limit`. It returns a `ContainerResult`: `exit_status`, the merged `output`, `timed_out` and `duration`.
- `exit_status` is `None` exactly when `timed_out` is true (a model validator).
- A command that fails or times out is a result. `ContainerError` means the container could not be started.
- `ContainerError(command, detail)` is a `BoundaryError` with the message `container command <command> failed: <detail>`.
- A `Mount` has a `source` (an absolute host path), a `target` (a container path) and `read_only` (default false).
- A target starts with `/` and has no empty segment and no `..` segment. `/`, `a/b`, `/a//b`, `/a/` and `/a/../b` are refused with `ValidationError`; `/a/./b` is accepted.
- Both operations raise `ValueError` for a mount whose target is `/work` or lies under it, because the dataset is the fixed `/work` mount of every run, and for a command without words.
- `check_container_call` is that rule. The fake and the podman adapter both call it.
- `ContainerCall` records one call as it was asked. Only the fake uses it.

See also: *The podman adapter* and *The fakes*.

## The copy snapshots

On a file system without snapshots, such as a Cloud Run job's, the base is a plain copy of the dataset's folder. `CopySnapshots` in [copy_snapshots.py](../../src/factory/machine/adapters/copy_snapshots.py) (`factory.machine.adapters.copy_snapshots`) implements `Snapshots` this way. It starts no process.

    CopySnapshots(folder, base)

- `advance` replaces `base` with a copy of `folder`: folders, files with their bytes and mode, and symbolic links as links, never followed.
- `reset` empties `folder` and copies `base` into it. `folder` itself stays, as a mount point does.
- `changed_paths` walks both trees and compares mode, bytes and link target. The bytes are read in chunks of at most 1 MiB (`_CHUNK_BYTES`), so memory does not grow with a file's size.
- An `OSError` of `reset` or `advance` is `SnapshotError("reset" or "advance", <the operating system's message>)`. `changed_paths` turns none.
- Without a `base` directory, `reset` and `changed_paths` raise `SnapshotError("reset" or "changed_paths", "no base at <base>")`, and `reset` changes nothing. A `base` that is a file counts as no base.
- The cost is a full copy per `reset` and `advance`. [machine.md](../operator-guide/machine.md), *Without ZFS*, has the figures.

See also: *The snapshots* and *The fakes*.

## The fakes

Two fakes let the suite and the smoke tests run without `zfs` and `podman`.

    FakeSnapshots(folder, base)
    FakeContainerRuns(workspace)

`FakeSnapshots` in [fake_snapshots.py](../../src/factory/machine/adapters/fake_snapshots.py) is a subclass of `CopySnapshots` with the same constructor and no code of its own. The suite's fake and the real copy adapter are one implementation, so a rule of the copy is tested by both.

`FakeContainerRuns` in [fake_containers.py](../../src/factory/machine/adapters/fake_containers.py) plays a container as a child process on the host. It starts the child through `run_process` in [process.py](../../src/factory/shared/adapters/process.py). [test_wrapper_search.py](../../tests/guards/test_wrapper_search.py) names this module as one that reaches it.

- It maps container paths to host folders. The mounts given plus a fixed mount of `workspace` at `/work` form the table.
- A command word, an `environment` value or the `working_directory` that equals a target, or starts with the target and a `/`, has that target replaced by the mount's `source`. The longer target wins, and `/workspace` is not under `/work`. Keys of `environment` are never mapped.
- `launch` returns `/bin/sh -c 'cd "$1" && shift && exec "$@"' fake-container <working directory> <command...>`, all mapped, with the time limit as given.
- `run` starts those words with the mapped working directory and environment and the merged output.
- A program the shell cannot find is a result with exit status 127. A child that cannot be started, such as a working directory that does not exist, is `ContainerError(command[0], <operating system's message>)`.
- `calls` lists every accepted `launch` and `run` as `ContainerCall`, before the mapping. A call refused with `ValueError` is not recorded.
- It does not enforce `read_only` (a mount is only a path mapping), isolates nothing, and the command sees the host's programs.
- The suite's stages run on these fakes (*Wiring and tests* under *The container environment*). The agent's request names the dataset's checkout as its working directory. So `FakeAgentRuntime` writes where a real agent writes, and the take brings the result in. `agent_working_directory` in [take.py](../../src/factory/pipeline/application/take.py) gives it: `boundaries.snapshots.mount_point / "checkout"`. `TaskComposer` and the preflight's probe use it. A real runtime in a container ignores the field, because the container's working directory is `/work/checkout`.

Tests:

- [test_fake_snapshots.py](../../tests/machine/adapters/test_fake_snapshots.py) runs the rules through the fake.
- [test_copy_snapshots.py](../../tests/machine/adapters/test_copy_snapshots.py) uses a real tree in `tmp_path`, the chunked read and the operating system's faults.
- [test_containers.py](../../tests/machine/domain/test_containers.py), [test_errors_environment.py](../../tests/shared/domain/test_errors_environment.py), [test_snapshots_interface.py](../../tests/machine/application/test_snapshots_interface.py), [test_containers_interface.py](../../tests/machine/application/test_containers_interface.py) and [test_fake_containers.py](../../tests/machine/adapters/test_fake_containers.py) cover the other parts.
- [test_interfaces.py](../../tests/machine/application/test_interfaces.py) holds the row of each interface.

They work in `tmp_path` and start only `/bin/sh` and `printf`.

See also: *The snapshots*, *The container runs*, *The copy snapshots* and *The container environment*.

## The ZFS adapter

On the VM the dataset is a ZFS dataset such as `tank/factory/vm`, and the base is the snapshot `<dataset>@base`. `ZfsSnapshots` in [zfs_snapshots.py](../../src/factory/machine/adapters/zfs_snapshots.py) (`factory.machine.adapters.zfs_snapshots`) implements `Snapshots` with the `zfs` program.

    ZfsSnapshots(dataset, mount_point, *, drop_caches, executable="zfs", time_limit=SNAPSHOT_TIME_LIMIT)
    ZfsSnapshots.version() -> str
    ZfsSnapshots.dataset_exists() -> bool

- `mount_point` is returned as given. The base is the snapshot `<dataset>@<BASE_SNAPSHOT>`, and `BASE_SNAPSHOT` is `base`.
- `SNAPSHOT_TIME_LIMIT` is ten minutes.
- The adapter runs the one executable it is given, so an operator can pass a wrapper script, such as a `sudo` call, in place of `zfs`.
- `drop_caches` is required. It is the command, program first, that `reset()` runs after the rollback. An empty tuple raises `ValueError`.
- `DROP_CACHES_COMMAND` is `("sudo", "-n", "/usr/local/bin/factory-drop-caches")`. Only [wiring.py](../../src/factory/entry/wiring.py) (`factory.entry.wiring`) constructs the adapter, with `drop_caches=DROP_CACHES_COMMAND`.
- The reason for the drop is in *The reset drops the page cache after the rollback* of [decisions.md](../decisions.md).
- `version()` and `dataset_exists()` serve the preflight.

No test runs a real `zfs`; it runs only on the VM. The stand-in and the tests are in the *Reference*, under *The ZFS stand-in*.

See also: *The ZFS commands, diff and faults* in the *Reference*.

## The podman adapter

Each command of a stage runs in a throwaway container of the stage image, with the dataset at `/work`. The container has no capability, a process limit and a memory limit. `PodmanRuns` in [podman_runs.py](../../src/factory/machine/adapters/podman_runs.py) (`factory.machine.adapters.podman_runs`) implements `ContainerRuns` with the `podman` program.

    PodmanRuns(executable, image, workspace, *, instance, time_limit=PODMAN_TIME_LIMIT, profile="rootless")
    PodmanRuns.version() -> str
    PodmanRuns.image_exists() -> bool

- `executable` is run as given, so an operator can pass a wrapper script.
- `workspace` is the dataset's mount point, mounted at `/work`.
- `instance` is required. It is the name that the label of every container carries.
- `time_limit` bounds only `version` and `image_exists`. `PODMAN_TIME_LIMIT` is two minutes.
- `--rm` removes the container when it ends, so nothing of one command is left for the next.
- `--userns=keep-id` makes files the command writes into `/work` belong to the host user that runs podman.
- `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g` keep code in the checkout from using rights, forking without end or taking the machine's memory.
- The container keeps podman's default network: the sync and the check need the package index, and the agent needs the model's API.
- A read-only mount gets `:ro`. A rootless container cannot write it, and that is the whole protection of the host's repository and of the login files.
- Podman does not pass the factory's environment into the container. A token or a path the factory holds reaches a command only when a caller names it in `environment`.
- `launch` returns `ContainerLaunch(argv, env=None, time_limit=<limit> + CONTAINER_GRACE)`. The `podman` program itself runs with the factory's environment, and it needs `HOME`, `XDG_RUNTIME_DIR` and `PATH` from it.
- `CONTAINER_GRACE` is 30 seconds. The factory's own kill is the second line behind podman's `--timeout`, so a `timed_out` result usually comes from podman's kill.
- A `podman` that cannot start is `ContainerError(command[0], <operating system's message>)`: the first word of the command asked for, not `podman`.
- `launch` and `run` raise `ValueError` as `check_container_call` says.
- The profile `job` is for a managed sandbox such as a Cloud Run job. It changes two things: the options before `run`, and `--userns=keep-id` giving way to `--http-proxy=false --network=host`.

No test runs a real `podman`; it runs only on the VM.

See also: *The podman command line*, *The job profile*, *Reading the end of a run* and *The podman stand-in* in the *Reference*.

## The stage environment

The stage protocol calls one object for the cycle of a stage: it prepares the place the agent works in, runs the agent there and takes the result back into the factory's work tree. `StageEnvironment` is that object's abstract base class, in [stage_environment.py](../../src/factory/machine/application/stage_environment.py) (`factory.machine.application.stage_environment`). The stage protocol knows no `podman`, `zfs` or `sudo`.

    StageEnvironment.prepare(commit, branch, *, sync_time_limit) -> None
    StageEnvironment.run_agent(request, *, run=None) -> AgentRunResult
    StageEnvironment.take(stage_start, work_item_path) -> TakeReport
    stage_environment_of(boundaries) -> StageEnvironment

- `prepare` makes the place hold `branch` at `commit`, its tools synced. It raises `SnapshotError` or `ContainerError` when that cannot be done. The sync's container gets `sync_time_limit`.
- `run_agent` runs the request's agent in this environment. With `run` the environment calls it once instead of the boundaries' runtime. Whatever it does inside, such as the resumes of `PatientRuns` after a provider limit, happens in the same prepared place.
- `take` brings the agent's result into the work tree as far as the role may write, and returns a `TakeReport` (`left`, `restored_work_item`).
- `take` raises `WorkItemFormatError` naming `work_item_path` when the [work item](glossary.md) is absent or unreadable at the stage-start commit. The work tree is then left untouched.
- `stage_environment_of(boundaries)` gives the `ContainerEnvironment` on `boundaries.snapshots` and `boundaries.containers`, both required.
- `StageLauncher`, `AfterAgent`, `StageFinisher` and `StallService` take an optional keyword `stage_environment`. `None` means `stage_environment_of(boundaries)`.
- `StageRunner` builds one environment and gives it to all four, so that the object that saw a stage's `prepare` sees its `take`.
- `StallService` (it handles a [stall](glossary.md)) reaches the take only through the environment it is given. `StageFinisher` takes only through its stall service, and its checks go through `boundaries.project_commands`.
- The sync's time limit is the `time_limit` of the `sync` project command in the [pipeline definition](glossary.md), in minutes. Without a `sync` command it is the default of a project command, `ProjectCommandDefinition().time_limit`, 10 minutes. `StageLauncher` reads it.

### Who calls what

- `StageLauncher.launch` calls `prepare(stage_start.commit, branch, sync_time_limit=...)` and then `run_agent(request, run=PatientRuns(boundaries).run)`. It does so after the claim is pushed and the pull request ensured, and before the [cost record](glossary.md) begins.
- An error from `prepare` ends the launch like one from the agent runtime: after the claim, before any run or cost record.
- `AfterAgent.process` calls `take(started.stage_start, started.path)` once the result and the decision are accepted. `AgentAftermath.take` carries the report, and the entry's closing paragraph names `take.left` (see *After the agent run* in [pipeline.md](pipeline.md)).
- `agent_run_probe_item`, the preflight's probe, calls `stage_environment_of(boundaries).run_agent(request)` and no `take`. Nothing of its run reaches the checkout.
- `StallService.stall`, with a stage start, calls `take(context.stage_start, context.path)` after the checkout is put back on the work item's branch, whatever the reason (`check_red` included). Its report is `StallResult.take`. A stall after `AfterAgent`'s take is a second take within one stage.

Tests:

- [test_stage_environment_of.py](../../tests/pipeline/application/test_stage_environment_of.py) covers the environment of the boundaries.
- [test_stage_environment_calls.py](../../tests/pipeline/application/test_stage_environment_calls.py) gives `StageLauncher` and `AfterAgent` a stand-in environment that records its calls.
- `test_interfaces.py` holds the interface's row.

See also: *The container environment*, *The take* and *Starting a stage* in [pipeline.md](pipeline.md).

## The container environment

The container environment is the one real stage environment. The agent works on the dataset of `Snapshots`, the sync runs in a container of `ContainerRuns`, and the take copies back what the role may write. It runs steps 2 to 4 and 6 of the cycle. The agent's own container (step 5) is not here: `run_agent` runs the request through the boundaries' runtime, which starts the container itself (*The agent's container*).

    ContainerEnvironment(boundaries, snapshots, containers, *, extra_environment={}, ca_bundle=None)

It is in `stage_environment.py`, beside the interface.

### prepare

`prepare(commit, branch, *, sync_time_limit)` does four things in this order, each timed with `boundaries.clock`.

1. `snapshots.reset()` puts the dataset back to its base. A `SnapshotError` propagates as it is, and no container has run.
2. The sync container runs the sync script (*The sync script* in the *Reference*) with `/work/checkout` and `/work/home` as its folders.
3. The result is judged. A timeout is `ContainerError("sync", "no end within <n> s")`, `n` the limit in seconds rounded up. An exit status other than 0 is `ContainerError("sync", <detail>)`.
4. `snapshots.advance()` moves the base to the synced dataset.

- The detail of a failed sync is the last non-blank line of the output that is no make message, or `exit status <n>` when none exists. `last_line` in [checks.py](../../src/factory/pipeline/domain/checks.py) (`factory.pipeline.domain.checks`) holds that rule, and `MakeProjectCommands` uses it too. A line starting `make:` or `make[` is skipped, so a failed recipe's own last line is the detail.
- If `reset` fails, for example on a dataset without a base, nothing else ran and `containers` was not called.
- If the sync fails or times out, the dataset holds whatever the script did and the base did not move. `snapshots.changed_paths()` is not empty, and the next `reset()` empties the dataset again. The stage ends with the error before any agent runs.
- If the commit is no commit, `git reset` fails and the detail is git's message.
- The durations of a failed `prepare` are not kept. The timing line keeps those of the last successful one, because the stage stops at the error and no `take` follows.
- The first `prepare` on a dataset creates the repository. The next ones reuse it, and objects of earlier stages stay in it.

### run_agent

`run_agent(request, *, run=None)` calls `(run or boundaries.agent_runtime.run)(request)` and returns the result. Nothing is sealed, searched or removed. The dataset is rolled back by the next `prepare`, so nothing the agent leaves survives.

### take

`take(stage_start, work_item_path)` is `TakeService(boundaries, snapshots.mount_point).take(stage_start, work_item_path, snapshots.changed_paths())` (*The take*). A file written in the dataset's checkout, in a source folder reaches the host when the role may write it. A changed file outside the write paths stays in `left`. Nothing of `.venv`, which the host ignores, or of `home/` is taken. The report is returned as the service gives it. A second `take` without a `prepare` between runs the service again on the dataset's changes then.

### The timing line

After the first take of a stage, one line goes to the factory log through `boundaries.log.line` (`TIMING_LINE`):

```text
2026-10-24T18:00:07Z stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s
```

- Each duration is in seconds with one decimal (Python's rounding).
- `reset`, `sync` and `advance` are those of the last successful `prepare` of the same object. Each `prepare` replaces them and never adds.
- `take` is the time of this `take`, `changed_paths` included.
- A `take` without a `prepare` on the object writes `0.0` for the first three.
- There is one line per stage: the first `take` after a `prepare` on the object writes it, or the first `take` on an object without a `prepare`. None follows `prepare` alone.
- A stall after `AfterAgent`'s take (an empty entry, a broken form, a red check) is a second take. It takes again from the dataset and writes no line.
- To read the cost of each part, take the lines from `/state/factory.log`: `reset` and `advance` are the cost of the snapshots, `sync` the cost of the container with `make sync`, and `take` the cost of listing the changes and copying them.

### Wiring and tests

`Boundaries.snapshots` and `Boundaries.containers` (see *Boundaries* in [pipeline.md](pipeline.md)) are required fields. `stage_environment_of` always builds the container environment from them. *The settings and the wiring* says how the real tools are built.

The suite's stages run on the fakes. The `boundaries` fixture holds `FakeSnapshots(workspace, base)` and `FakeContainerRuns(workspace)` under `tmp_path`, with an empty base, and `container_dataset` takes them from the fixture. The host checkout of the fixture is the upstream, with real `git` and `make` as child processes on the host: the container is played, not run.

[container_support.py](../../tests/support/container_support.py) holds the helpers: `container_dataset`, `push_main`, `sync_makefile` (a `Makefile` whose `sync` writes a marker), `dataset_git`, `local_branches`, `timing_lines`, and the whole stage on a dataset (`whole_stage`, `assert_taken_and_pushed`).

Tests:

- [test_container_environment.py](../../tests/machine/application/test_container_environment.py) covers `prepare` and `run_agent`.
- [test_container_environment_take.py](../../tests/pipeline/application/test_container_environment_take.py) covers the take, the timing line and a whole stage through `StageRunner` with the host's project commands.
- [test_container_stage_checks.py](../../tests/pipeline/application/test_container_stage_checks.py) runs a whole stage through the check container. `ContainerMakeCommands` runs the sync container and one check container per check on the taken result. The next `prepare` starts from the pushed head with nothing left over.
- [test_checks_last_line.py](../../tests/pipeline/domain/test_checks_last_line.py) and [test_make_last_line_shared.py](../../tests/pipeline/adapters/test_make_last_line_shared.py) cover the last-line rule.

See also: *The stage environment*, *The take* and *The checks*.

## The sync command

The sync brings a checkout's tools up to date after a checkout, so that an agent and a check start from a checkout that works. `make sync` is the fourth target of the project contract (*Project commands*). For a project it must bring the checkout's tools up to date and nothing else: `uv sync --frozen` in the template, the project's own command in another stack.

- It must work on a checkout without ignored state and end with its usual green line.
- It runs in the sync container of `prepare` and before every check.
- The sync container's time limit is the `time_limit` of the `sync` project command (*The stage environment*).

See also: *The sync script* in the *Reference*.

## The agent's container

Step 5 of the cycle belongs to the agent runtimes, not to `ContainerEnvironment`. A runtime built with a `ContainerRuns` starts each call through `ContainerRuns.launch`, in a container of the stage image. `container_launch` in [agent_launch.py](../../src/factory/agents/adapters/agent_launch.py) (`factory.agents.adapters.agent_launch`) builds the call.

- `/work` is mounted, and the login and instructions files are mounted read-only at their own paths.
- The request's allow-list environment becomes `--env` entries, and `/work/checkout` is the working directory.
- The runtime reads the kill at `--timeout` as `time_limit`.
- What the container gets and what it lacks (`sudo`) is in *Calls in a container* in [agents.md](agents.md).
- `build_boundaries` gives the runtime of `FACTORY_AGENT_RUNTIME` its `PodmanRuns` (*The settings and the wiring*).

See also: *The podman adapter* and *The take*.

## The take

In the container environment the agent works on the dataset and may write anywhere it reaches. Nothing of that survives but what the take copies. `TakeService` in `take.py` (`factory.pipeline.application.take`) applies the write paths' refusal rule: what the role may write goes from the dataset into the work tree `boundaries.checkout`, and the rest stays in the dataset.

    TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths) -> TakeReport
    copy_changed(source, target, changed) -> None
    TakeReport(left, restored_work_item)

- `changed_paths` are those of `Snapshots.changed_paths()`, relative to `mount_point`.
- A path goes back when the role's [write paths](glossary.md) allow it and no protected path forbids it. The rule is *The take's rule* in [pipeline.md](pipeline.md), and `is_refused` is its function.
- A refused path is listed in `left` and not copied. The dataset is never written.
- The work item's state and [journal](glossary.md) are put back from the baseline, the agent's edits to its sections kept. A work item the role may not write is refused like any path: it is in `left`, not copied, not restored.
- `TakeReport` is frozen. `left` is sorted and holds each path once.
- The service makes no commit, runs no git command on the dataset and never writes under `mount_point`.
- `ContainerEnvironment.take` calls the service.
- Errors: `WorkItemFormatError` (baseline), `ValueError` from `copy_changed`, and `GitError` from `ignored` (see *The git wrapper* in [hosting.md](hosting.md)). A `ValueError` or `GitError` can come after the baseline was read but before anything is copied.

`copy_changed` mirrors each `ChangedPath` from the tree at `source` into the tree at `target`. The take uses it, and so does the check container's copy of the work tree (*The checks*). Every path is first checked with `check_repository_path`: an absolute path or one with a `..` segment raises `ValueError` naming it, before anything is copied.

- For `added` or `modified`, the entry at `target / path` is removed first (a link as the link, a folder with what it holds), then the source's entry is placed.
- A regular file arrives with its bytes and mode, so an executable bit stays. A symbolic link arrives as a link with the same target text and is never followed.
- For `deleted`, the entry at `target / path` is removed, a link as the link with its target untouched. A missing entry, a dangling link included, is no fault.
- Nothing is ever written or removed outside the target tree. For `added` or `modified`, each parent from `target` down is checked with `lstat`. A parent that is a link or no folder is removed (a link as the link) and made a real folder, so the entry lands inside the target.
- For `deleted`, a parent that is a link or missing means the entry is not in the tree. Nothing is removed and nothing is followed.

Tests: [test_take.py](../../tests/pipeline/application/test_take.py) and [test_take_edges.py](../../tests/pipeline/application/test_take_edges.py), built on [undo_support.py](../../tests/support/undo_support.py) and [take_support.py](../../tests/support/take_support.py) with a dataset folder in `tmp_path`; [test_git_cli_check_ignore.py](../../tests/hosting/adapters/test_git_cli_check_ignore.py) for `ignored`.

See also: *The seven steps of the take* in the *Reference*, and *The take's rule* in [pipeline.md](pipeline.md).

## The checks

The stage's checks see the taken result on a clean base. `ContainerMakeCommands` in [make_commands.py](../../src/factory/machine/adapters/make_commands.py) (`factory.machine.adapters.make_commands`) does it for every project command.

    ContainerMakeCommands(..., extra_environment={}, ca_bundle=None)

- It rolls the dataset back to the base, copies in the files the take brought into the host's work tree, and runs `make sync && make <command>` in a container with the command's time limit.
- The container gets `{**extra_environment, **CHECK_ENVIRONMENT, "PATH": path}`. The constants and the image's `path` win.
- `ca_bundle` is mounted read-only at its own path. `build_boundaries` hands it the same extras as the sync and the agent.
- A file a check makes stays in its container's dataset and is reset away by the next run. It never reaches the host.
- What is copied is what differs from `HEAD` on the host (`git.changed_paths("HEAD")`), not a list the take kept. After the take that is the taken files, the restored work item and the factory's cost record. At the preflight's `lint` on `main` it is nothing.
- Nothing is remembered between the take and the checks: `HEAD` and the host's work tree already say what the take brought, so no list is kept that could disagree with them.
- The copy is `copy_changed`, so the take and the checks share one rule for links, modes, deletions and refused paths.

See also: *The take*, *Known results* and *Project commands*.

## The settings and the wiring

An [instance](glossary.md) names its dataset, workspace and stage image in environment variables. `read_settings` reads them in [settings.py](../../src/factory/shared/domain/settings.py) (`factory.shared.domain.settings`), and `build_boundaries` in `wiring.py` builds the tools from them. [install.md](../operator-guide/install.md), *Configuration*, has the operator's table. The table of every field is in *The settings of the stage environment* in the *Reference*.

    build_boundaries(settings, token, *, hosting=None, images=None) -> Boundaries
    workspace_overlap_fault(workspace, checkout, state_directory) -> tuple[str, str] | None
    snapshot_base_fault(snapshots, base, workspace, checkout, state_directory) -> str | None
    agent_run_environment(settings, base) -> dict[str, str]

- `read_settings` strips each value and reads a blank one as unset. It raises no fault for a missing dataset, workspace or image.
- It refuses a relative workspace, and a `checkout` or a `state_directory` that is the workspace or lies inside it.
- `FACTORY_SNAPSHOTS` unset or blank is `zfs`. `zfs` and `copy` are accepted.
- `workspace_overlap_fault` holds the rule on the workspace. It gives the variable and the fault of a relative workspace or of a path inside it, and `None` for a `None` workspace. `read_settings` calls it, and so does the model validator of `InstanceSettings`, so a model built directly refuses the same combinations with a `ValidationError`.
- `snapshot_base_fault` holds the rule on the base, for `read_settings` and for the model validator.
- `build_boundaries` refuses an incomplete instance first, before it builds anything and before PyGithub's `get_repo` is called.
- It runs no tool. `zfs` and `podman` start only when a stage uses them.
- It computes `extra = extra_environment(settings, os.environ)` once and hands the same mapping to the agent runtime, to `ContainerMakeCommands` and to `Boundaries.container_extra_environment`. `stage_environment_of` builds the sync's `ContainerEnvironment` from that field and from `settings.ca_bundle`.
- `RecordingProjectCommands.inner` is the implementation it records, which the wiring's tests read.
- `agent_run_environment` copies `base` and sets `HOME` to `/work/home` (`WORK_HOME_ENVIRONMENT`), on the dataset, whatever the settings. The dict it is given is unchanged.

Tests: [test_settings_snapshots.py](../../tests/shared/domain/test_settings_snapshots.py) and [test_wiring_copy_snapshots.py](../../tests/entry/test_wiring_copy_snapshots.py) for the copy snapshots; [test_settings_stage_environment.py](../../tests/shared/domain/test_settings_stage_environment.py), [test_settings_one_environment.py](../../tests/shared/domain/test_settings_one_environment.py), [test_wiring_stage_environment.py](../../tests/entry/test_wiring_stage_environment.py) and [test_wiring_one_environment.py](../../tests/entry/test_wiring_one_environment.py).

See also: *The preflight*.

## The project's stage image

A project adds a layer to the stage image with the file `<project>/factory/stage.Containerfile` on its `main`. The operator's side is in [machine.md](../operator-guide/machine.md), *The project's stage file*. The factory builds the layer when the file is valid and uses the result for every container run.

    stage_layer(text, base_identity) -> StageLayer
    Images.build(layer, base, tag, time_limit) -> ImageBuild
    Images.path(image) -> str
    chosen_image(settings, git, images, stops, *, report=None) -> ChosenImage | None
    project_image_settings(...)

- The rule is `stage_layer` in [stage_layer.py](../../src/factory/machine/domain/stage_layer.py) (`factory.machine.domain.stage_layer`). It returns a `StageLayer` (`text`, `digest`, `identity` = `<base identity>+<digest>`) or raises `StageLayerRefused`, whose `str()` is the reason.
- `STAGE_FILE` and `project_image_tag(stage_image)` (`<stage image>-project`) are defined there once.
- `Images` is the interface, in [images.py](../../src/factory/machine/application/images.py) (`factory.machine.application.images`). `build` returns an `ImageBuild` (`passed`, `duration`, `output_tail`: the last 20 lines, and `warnings`: the count of output lines that warn, 0 by default).
- `IMAGE_BUILD_TIME_LIMIT` is the one 30-minute limit.
- `PodmanImages` in [podman_images.py](../../src/factory/machine/adapters/podman_images.py) is the implementation. It builds with `--build-arg FACTORY_BASE=<base>`, `--network=host`, `-t <tag>` and an empty context folder, then runs `image prune -f`. `FakeImages` in [fake_images.py](../../src/factory/machine/adapters/fake_images.py) is the fake the tests use.
- `path` reads `image inspect --format '{{json .Config.Env}}'` and raises `ContainerError` when podman fails or prints no JSON. `PodmanImages` reaches podman through `run_podman` and puts the job profile's global options before each subcommand.
- The one place where the image in use is chosen is `chosen_image` in `factory.entry.wiring`. It returns a `ChosenImage` (the settings, and the image sizes measured once) or `None`. `project_image_settings` is a wrapper around it that returns only the settings.
- It returns the settings unchanged without a stage file.
- When the file builds, it returns the settings with `stage_image` = the project tag and `image` = the layer's identity.
- It raises the machine [stop](glossary.md) `stage_image_failed` and returns `None` when the file breaks the rule or does not build.
- No [tick](glossary.md) is built until a `main` with another file.
- A check that finds a valid file, or none, clears the stop.
- The boundaries are built a second time from the chosen settings, so every container run and the preflight's stamp take the project image.
- The `PATH` comes from `images.path(<the image in use>)` in `build_boundaries`, kept in `Boundaries.image_path`. The sync environment, `ContainerMakeCommands` and the agent environment (`production_environment(boundaries.image_path)`, the scripts folder first) take it. An image whose `path` raises gives `SYSTEM_PATH`.
- `run_instance` has `_ProjectImageStart` call `chosen_image` once the checkout is ready, and again whenever the stage file changes on a new `origin/main`. *How the stage file is followed* in the *Reference* has the exact order.

See also: *The preflight* and *The podman adapter*.

## The preflight

Before a stage may start, the preflight checks the machine: the tools, the dataset, the stage image and a probe run of the agent. It lives in [preflight.py](../../src/factory/machine/application/preflight.py) (`factory.machine.application.preflight`). The tick, the stamp and the stops are in [pipeline.md](pipeline.md).

    machine_extras(boundaries, settings, environment)
    tool_version_item(name, version) -> PreflightItem
    dataset_item(dataset, exists) -> PreflightItem
    snapshots_item(workspace, base) -> PreflightItem
    stage_image_item(image, exists) -> PreflightItem
    metadata_block_item(probe) -> PreflightItem
    opencode_item(settings, agent_models) -> PreflightItem
    agent_run_probe_item(boundaries, settings, environment) -> PreflightItem

- `machine_extras` in `factory.entry.wiring` gives one list of items. With `zfs`: `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `metadata-block`, `opencode`, `agent-run-probe`. With `copy`, `dataset` and `zfs` give way to `snapshots` after `podman`.
- `metadata-block` is there under `FACTORY_CONTAINER_PROFILE=job` only, and `opencode` under opencode only.
- It builds the snapshots and a `PodmanRuns` of its own through `_container_adapters`, which `build_boundaries` also calls.
- The reason: `boundaries.snapshots` and `boundaries.containers` are typed as the interfaces, and nothing narrows them.
- Building them runs no command.
- The items that reach the machine take callables, so `application` knows no adapter.
- `MachineChecks.run` checks `REQUIRED_TOOLS` (`git`, `uv`). It asks for no runtime executable on the host.
- There is no `tool:make`, because `make` runs only in the sync and check containers.
- There is no `tool:claude` or `tool:opencode`, because the executable is the stage image's, and `agent-runtime-version` runs it there.
- There is no `agent-environment` item, because the agent's `HOME` is a path inside the container.
- `opencode_item` checks the aliases only.
- Both probes go through the environment like a stage.
- `agent_run_probe_item` resolves `origin/main`. Without one the item fails with `no origin/main to prepare the stage environment from`, and no run starts.
- It then calls `stage_environment_of(boundaries).prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)` and `run_agent` on the same object.
- `SnapshotError` and `ContainerError` from `prepare` fail the item with their message.
- `Preflight._run_probe` calls the same `prepare` after it puts the checkout on `main` and before `lint`. `Preflight.run` catches both errors beside `GitError` and `ProjectCommandError` and stops with `the probe on main could not run: <error>`.

Tests: [test_preflight_metadata_block.py](../../tests/machine/application/test_preflight_metadata_block.py), [test_wiring_metadata_block.py](../../tests/entry/test_wiring_metadata_block.py), [test_container_items.py](../../tests/machine/application/test_container_items.py), [test_opencode_item_container.py](../../tests/machine/application/test_opencode_item_container.py), [test_machine_checks_container.py](../../tests/machine/application/test_machine_checks_container.py), [test_agent_run_probe_environment.py](../../tests/hosting/application/test_agent_run_probe_environment.py), [test_preflight_run_environment.py](../../tests/machine/application/test_preflight_run_environment.py) and [test_wiring_container_extras.py](../../tests/entry/test_wiring_container_extras.py).

See also: *The items of the preflight* in the *Reference*.

## Project commands

The factory reaches a project's build only through one interface, so another stack can bring its own tool. `ProjectCommands` is an abstract base class in [project_commands.py](../../src/factory/machine/application/project_commands.py) (`factory.machine.application.project_commands`). `MakeProjectCommands` in `make_commands.py` is the first implementation, and `ContainerMakeCommands` is the second (*The checks*). The pipeline uses the results, and so does the preflight's probe.

    ProjectCommands.run(command, *, time_limit) -> CheckResult
    MakeProjectCommands(directory, kill_points=None, *, executable="make")

- `run` starts `<executable> --no-print-directory <command>` in `directory` through `run_process`, with stderr merged into stdout. `directory` is where make finds the project's Makefile.
- The environment is the current one less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. Without that, a run inside `make check` (where `MAKELEVEL` is set) would print `make[N]: Entering directory` lines that a run on its own does not.
- `MakeProjectCommands` runs `make` as the factory's own user. Every instance runs a project command in a check container, and `MakeProjectCommands` stays for the suite.
- The string `"make"` appears in `make_commands.py` alone. [test_make_search.py](../../tests/guards/test_make_search.py) allows exactly that one.
- The contract between a project and the factory is four make targets: `check`, `lint`, `test` and `sync`.
- `sync` brings a checkout's tools up to date (`uv sync --frozen` for Python; another stack names its own command in the same target). The stage environment runs it, in its sync container before every agent run and in its check container before every check. It is never a stage's `checks` or `reports`, and `check` does not run it.
- [Makefile](../../operator/template/Makefile) in `operator/template/` has the target, and [pipeline.yml](../../operator/template/factory/pipeline.yml) there has the command `sync` with a time limit. This repository's own [Makefile](../../Makefile) has the target `sync` (`uv sync --frozen`), and its [pipeline.yml](../../factory/pipeline.yml) has the command `sync` with `time_limit: 5`.
- A project declares its own layers and checks them with a project command of its own.
- To add the layers check, the project adds a make target to its Makefile, for example `layers`, which calls its tool through uv.
- Where the check belongs in the gate, the project makes `check` depend on the target.
- The factory sees only that target's `CheckResult`: its status, `last_line` and `output_tail`.

```python
result = MakeProjectCommands(Path(".")).run("check", time_limit=timedelta(minutes=10))
if not result.passed:
    print(result.status, result.exit_status, result.last_line)
```

Tests write a Makefile into `tmp_path` and run the class against it; nothing is faked.

See also: *The checks*, *Known results* and *The sync command*.

### The record logs

The records go through `RecordLog[R]` in [files.py](../../src/factory/shared/application/files.py) (`factory.shared.application.files`), an interface for an append-only file of records. `JsonLinesRecordLog(path, model)` in [record_log_jsonl.py](../../src/factory/watching/adapters/record_log_jsonl.py) (`factory.watching.adapters.record_log_jsonl`) is its implementation.

    RecordLog.append(record) -> None
    RecordLog.read() -> list[R]
    JsonLinesRecordLog(path, model)

- `append` raises `OSError` when it cannot write.
- `read` gives the records in file order, `[]` without a file. It skips a blank line, a line that is not UTF-8 and a line that does not validate.
- It writes one `model_dump_json()` line per record, in one write to the file opened for appending, and creates the folder on the first append.
- It reads the file's bytes, splits them at `\n` alone and decodes each line on its own as strict UTF-8. A line cut inside a multibyte character by a kill is skipped, and a record holding U+2028, U+2029 or U+0085 stays whole (`str.splitlines` would cut it).
- A record appended after a torn line shares its line and is skipped with it.
- `build_boundaries` points it at `<state directory>/records/project-commands.jsonl`.
- Tests use `UnwritableRecordLog` in [record_support.py](../../tests/support/record_support.py) for a log that cannot be written.

### The disk record

The disk record uses the same log. `DiskRecord` in [disk.py](../../src/factory/machine/domain/disk.py) (`factory.machine.domain.disk`) is what `Boundaries.disk_records` holds, and `DiskRecorder` in [disk_records.py](../../src/factory/machine/application/disk_records.py) (`factory.machine.application.disk_records`) writes it.

    DiskRecord(at, occasion, folders)
    DiskUse(path, free_bytes, used_bytes)
    disk_line(record) -> str
    DiskRecorder(boundaries).record(occasion) -> DiskRecord
    DiskRecorder(boundaries).last() -> DiskRecord | None

- `occasion` is a `DiskOccasion`: `start` or `acceptance`. `folders` is a list of `DiskUse`, with `None` where a number is unknown.
- `disk_line(record)` is its factory log line.
- `DiskRecorder` measures the checkout's parent, the state directory and, when `InstanceSettings.temporary_directory` is set, that directory, through `DiskSpace`.
- `record(occasion)` appends the record, logs its line and returns it. A failed append is logged and the record still returned.
- `last()` gives the latest record whatever its occasion.
- `run_instance` records `start` once. `read_environment_settings` sets `temporary_directory`, `read_settings` does not.
- `build_boundaries` points the log at `<state directory>/records/disk.jsonl`.

### The tests' umask and login variables

The suite keeps the tests independent of the process that starts them: of its umask and of the agent's login.

- The tests run under the umask pytest was started with. No module under `tests/` sets one, except the fixture `umask_of` of [test_calls_as_the_factory_user.py](../../tests/agents/adapters/test_calls_as_the_factory_user.py), which sets a umask for one test and puts the earlier one back. Test: [test_tests_run_under_the_starting_umask.py](../../tests/guards/test_tests_run_under_the_starting_umask.py).
- The suite removes the agent's two login variables, `CLAUDE_CODE_OAUTH_TOKEN` and `ANTHROPIC_API_KEY` (`LOGIN_VARIABLE` and `API_LOGIN_VARIABLE` of `agent_launch.py`), from every test's environment. The autouse fixture `without_agent_login` in [conftest.py](../../tests/conftest.py) calls `monkeypatch.delenv` for each.
- The reason: an agent's run holds them.
- A child process that gets the process's own environment inherits them, as the `version()` calls of both runtimes do.
- An assertion message prints what it compares, so a failing test could print a key into the run's output.
- A test may still set either name with `monkeypatch.setenv`. `monkeypatch` restores the process's value afterwards.
- An assertion about an environment compares names, `set(environment)`, never the mapping, so that a failure prints names and no value. Test: [test_no_agent_login.py](../../tests/guards/test_no_agent_login.py).

See also: *The fakes* and [agents.md](agents.md).

## Known results

A check that passed on the same tree need not run again. `KnownResults` in [known_results.py](../../src/factory/pipeline/application/known_results.py) (`factory.pipeline.application.known_results`) is what `StageFinisher` runs a stage's checks and reports through (see *`StageFinisher.finish(aftermath)`* in [pipeline.md](pipeline.md)).

    KnownResults(boundaries, definition).run(command) -> CheckResult

- `run` works in the order given in *The order of `KnownResults.run`* in the *Reference*.
- Its records are `Boundaries.result_records`. `build_boundaries` points a `JsonLinesRecordLog` at `<state directory>/records/known-results.jsonl`.
- A known result is the last record of the key that is a real run, when its status is `passed`. A later failed run of the key ends it.
- `RecordingProjectCommands` sits under `boundaries.project_commands`. It records every real run and sees no key.
- The preflight's probe does not use `KnownResults`.

Tests: [test_known_results.py](../../tests/pipeline/domain/test_known_results.py), [test_command_line.py](../../tests/pipeline/domain/test_command_line.py), [test_known_results.py](../../tests/pipeline/application/test_known_results.py), [test_stage_known_results.py](../../tests/pipeline/application/test_stage_known_results.py) and [test_wiring_known_results.py](../../tests/entry/test_wiring_known_results.py).

See also: *The checks*, *Project commands* and *The order of `KnownResults.run`* in the *Reference*.

## Mutation testing

`make mutants` runs mutmut over the modules you name, to find tests that would not notice a change in the code. It is slow, so it is not part of `make check`. No stage and no agent runs it. It runs only as sweeps outside the factory, which the human starts (*Mutation testing runs only as sweeps outside the factory* and *The mutants target keeps only its sweep form* in [decisions.md](../decisions.md)). The cost is in [install.md](../operator-guide/install.md), *Mutation testing by sweep*.

Nothing is kept between runs. Every run removes `mutants/` first, so mutmut makes it anew, copies the other files under `src/` (the contract's schemas) afresh and runs its stats again. A run pays the stats every time.

- The modules come from `MODULES`, dotted modules or packages, each run by its pattern `<name>.*`.
- Or they come from `FEATURE=<id>`: the modules under `src/factory` that the [feature](glossary.md)'s [story](glossary.md) commits changed on `origin/main`. They are found from the commit subjects that start `work item <id>-S<nnnn>:`. The pattern of `FEATURE_MODULES` in the `Makefile` also matches older subjects that open with one other word in place of `work item`. It needs a checkout with its history.
- `MODULES` wins when both are given.
- With neither, the target prints `mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.machine.domain.disk or make mutants FEATURE=F0012` and fails.
- When the feature changed no module, it prints `mutants: no module under src/factory changed by <id>` and exits 0.
- `MUTANTS_SECONDS` stops mutmut with `timeout` after that many seconds. With it unset there is no stop. A stopped run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`.
- `MUTANTS_CHILDREN` passes `--max-children`. mutmut's default is every core the machine reports, also in a container limited to fewer.
- The recipe ends with `uv run mutmut results` without the `not checked` lines.
- mutmut generates mutants for every module, and those outside the chosen ones stay `not checked`.
- So the listing holds only this run's mutants that mutmut did not kill, and none that a stop left unreached.
- A module with no mutant is a run with nothing to check, not a failure. mutmut mutates only functions without a decorator, so a module of interfaces, models or constants has none.

These commands run in a checkout, with a long run time. Run a sweep like this:

```sh
make mutants MODULES='factory.machine.domain.disk factory.pipeline.application'
```

To read one survivor:

```sh
uv run mutmut show <name>
```

See also: *The temporary folder of a mutants run* in the *Reference*.

## Reference

### The ZFS commands, diff and faults

Every command of `ZfsSnapshots` runs through `run_process` (see [shared.md](shared.md); `test_wrapper_search.py` names the module) with the working directory `/`, the factory's own environment, the time limit and standard error merged into the output.

| Member | Runs | When |
| --- | --- | --- |
| `reset()` | `zfs rollback -r <dataset>@base`, then `drop_caches` | always; `-r` removes any later snapshot; the drop runs only after a rollback that exited 0, under the same time limit |
| `advance()` | `zfs list -H -o name -t snapshot <dataset>@base`, then `zfs destroy <dataset>@base`, then `zfs snapshot <dataset>@base` | `destroy` only when `list` exits 0; exit 1 means there is no base yet and `destroy` is skipped |
| `changed_paths()` | `zfs diff -FH <dataset>@base` | always |
| `version()` | `zfs --version` | the preflight |
| `dataset_exists()` | `zfs list -H -o name <dataset>` | the preflight |

**Reading `zfs diff -FH`.** Each non-blank line is tab-separated: `<change> <kind> <path>`, or for `R` `<change> <kind> <old path> <new path>`. A field after those (`(+1)`, the link count of a hard link) is ignored.

- Changes: `M` is `modified`, `+` is `added`, `-` is `deleted`. `R` is `deleted` for the old path and `added` for the new one.
- Kind `/` is a directory and is left out, whatever the change. The mount point itself, which `zfs diff` lists as a directory, is therefore no fault. Every other kind (files, links) is listed.
- Every path must be the mount point or lie under it. `/srv/x/workx/a` is outside `/srv/x/work`. Paths are made relative to the mount point with `/` separators.
- `zfs` writes each byte outside printable ASCII, and the backslash, as `\ooo` in octal (`\040` a space, `\303\251` an `é`, `\134` a backslash). The adapter decodes them to bytes and reads the bytes as UTF-8.
- A path that two lines name, one removing it and one adding it (a file made anew, a rename onto a removed path), is listed once, as `added`, in either order.
- The result is sorted by path. An empty output is `[]`.

**Faults.** Every fault is `SnapshotError(command, detail)`. `command` is the words run joined by a space, executable first (`zfs rollback -r tank/factory/vm@base`; for the drop, `sudo -n /usr/local/bin/factory-drop-caches`). The drop's faults are formed as the `zfs` commands' are, by the same runner (`_execute`). A rollback that fails raises its own fault and the drop is not run. `detail` is:

- the last non-blank line of the output, or `exit status <n>` when there is none, for a command that failed. Failed means an exit status other than 0, except for the two `list` commands, where only a status other than 0 or 1 fails;
- `no end within <n> s` when the time limit was reached, `n` the limit's seconds rounded up;
- the operating system's message (`[Errno 2] ...`) when the executable could not start;
- for `diff` only: `cannot read the line <line>` for an unknown change, too few fields, or a path that is not UTF-8, and `<path> is outside <mount point>`.

**For the preflight.** `version()` returns the first non-blank line of `zfs --version`, stripped (`zfs-2.2.2-0ubuntu9.1`). No such line is a fault with `printed nothing`. `dataset_exists()` is `True` when `list` exits 0 and names the dataset, `False` on exit 1, and a fault otherwise: `named <line>, not <dataset>` for another name, `printed nothing` for none.

### The ZFS stand-in

[zfs_support.py](../../tests/support/zfs_support.py) writes a stand-in `zfs` into `tmp_path`.

- `snapshots_on` also passes a drop stand-in that succeeds (`Drop` and `write_drop`).
- [test_zfs_snapshots_drop_caches.py](../../tests/machine/adapters/test_zfs_snapshots_drop_caches.py) uses stand-ins that append their words to one shared file, so a test reads the order of rollback and drop.
- The `zfs` stand-in records its arguments, environment and working directory, then answers by a plan keyed on its first argument (`rollback`, `list`, `destroy`, `snapshot`, `diff`, `--version`): planned output and exit status, or a sleep past a short limit.
- The limit itself cannot be seen from the stand-in, so tests of the default limit and its rounding replace the module's `run_process` with the `Recorder` of [run_process_recorder.py](../../tests/support/run_process_recorder.py).
- The tests are [test_zfs_snapshots.py](../../tests/machine/adapters/test_zfs_snapshots.py) and [test_zfs_snapshots_diff.py](../../tests/hosting/adapters/test_zfs_snapshots_diff.py).

### The podman command line

`launch` builds these words, in this order:

```text
<executable> run --rm --label factory.instance=<instance>
    --userns=keep-id --timeout <seconds>
    --cap-drop=all --security-opt=no-new-privileges
    --pids-limit=4096 --memory=4g
    --env NAME=value ...
    --volume <workspace>:/work --volume <source>:<target>[:ro] ...
    --workdir <working_directory> <image> <command...>
```

- `--rm`: the container is removed when it ends, so nothing of one command is left for the next.
- `--label factory.instance=<instance>`: the service's unit stops the containers by this label. Rootless podman places them outside the service's cgroup, so stopping the service alone would not end them.
- `--userns=keep-id`: rootless podman maps the container's user to the host user that runs podman, the `factory` user. Files the command writes into `/work` belong to that user on the host.
- `--timeout <seconds>`: the container runtime ends the container at the limit. The seconds are the limit rounded up (`30s` is `30`, 1.5 seconds is `2`).
- `--cap-drop=all`: the container has no capability. Code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) cannot use the rights root has inside its namespace.
- `--security-opt=no-new-privileges`: a set-uid program cannot give a process rights it was not started with.
- `--pids-limit=4096`: a fork bomb ends at the limit and does not fill the machine's process table.
- `--memory=4g`: a runaway process is killed in its container and does not take the machine's memory.
- `--env NAME=value`: one pair per entry of `environment`, in its order. These are the only variables the command gets besides the image's own.
- The operator's extras: the callers put the names of `FACTORY_CONTAINER_ENV` and the three CA variables of `FACTORY_CA_BUNDLE` (`extra_environment` in `factory.machine.domain.containers`) into `environment` beneath their own names, so a name the factory sets wins. The adapter treats them as any other pair.
- `--volume`: the workspace at `/work` comes first, then the given mounts in their order. A read-only mount gets `:ro`. The CA bundle is one such mount, at its own path (`bundle_mounts`). A command can read the host's repository and the login files and never change them. The tests pin the words, `:ro` above all.
- `--workdir`: the command's working directory in the container.
- The image, then the command words, which are never joined into a string.

There is no `--network` word under `rootless`, so every container keeps podman's default network (`job` uses the host's). The sync needs the package index. The check runs `make sync` first, which needs the index when the take changed `uv.lock` or `pyproject.toml`. The agent needs the model's API. Cutting the network is a later step, for example an allow-list (decision *Every container runs without rights and within limits* in [decisions.md](../decisions.md)).

The limits are the constants `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"`, read on every call of `launch`. 4096 processes leave room for the test suite's workers under `-n auto` on the VM's cores and what each starts. 4 GB lets one container run at a time on a machine of 8 GB. A container the kernel kills for its memory before the time limit is an ordinary result with its exit status, not a time-out: a command that fails with make's status 2 when the kernel ended one of its children, 137 when it ended the container's first process.

Measured on the local VM (Ubuntu 24.04, podman 4.9.3, rootless as `factory`) on 2026-10-24:

- podman accepts all four words;
- the container's effective capabilities are `0000000000000000`;
- a write to the dataset still works under `--userns=keep-id`;
- `--pids-limit=50` stops the 49th fork with "can't fork: Resource temporarily unavailable";
- `--memory=64m` sets the container's `memory.max` to 67108864;
- the user's systemd delegates the `cpu memory pids` controllers.

### The job profile

`profile` is `FACTORY_CONTAINER_PROFILE` (`InstanceSettings.container_profile`, passed by `_container_adapters` in `factory.entry.wiring`). `rootless`, the default, builds every word as above. `job` is for a managed sandbox such as a Cloud Run job ([machine.md](../operator-guide/machine.md), *The job profile*, has the measured reasons). It changes two things and nothing else:

- `JOB_PODMAN_OPTIONS` (`factory.machine.domain.containers`: `--runtime=runc`, `--cgroup-manager=cgroupfs`, `--storage-driver=overlay`; three words, no mount program, the storage's place being the machine's) go right after the executable, before `run`, in `launch`, `version` and `image_exists`, and in the command text of a `ContainerError`.
- In `launch`, `--userns=keep-id` gives way to `--http-proxy=false --network=host` (`_isolation_words`). All other words keep their order, so a `job` launch reads `<executable> <options> run --rm --label factory.instance=<instance> --http-proxy=false --network=host --timeout <seconds> --cap-drop=all ...`. It has no `--user` either: the container runs as the job's root.

Mounts, the grace, the reading of the end (255 at or after the limit is the time limit) and the `ValueError` rules are the same in both profiles. Test: [test_podman_runs_job_profile.py](../../tests/machine/adapters/test_podman_runs_job_profile.py).

### Reading the end of a run

`run` starts the launch's words through `run_process` with the working directory `/` (podman reads no file from it; a missing workspace is podman's own fault, 125), the factory's environment and standard error merged into `output`.

- `timed_out` is true when `run_process` says so, or when the exit status is in `CONTAINER_KILL_STATUSES` (`factory.agents.adapters.agent_launch`: 137, -9 and 255) and the run lasted at least `time_limit`: podman's `--timeout` sent the kill. `exit_status` is then `None`.
- The same statuses before the limit are the command's own, as is any other status at or after the limit.
- Otherwise `exit_status` is podman's, which is the command's. Podman exits 125 for its own faults, such as a missing image. The result says 125 and podman's message is in `output`.
- Podman's `--timeout` ends a container with exit status 255, not 137 (`PODMAN_TIMEOUT_STATUS`). Measured on the local VM on 2026-10-24 with podman 4.9.3: `podman run --rm --timeout 3 ... sleep 30` ended after 3.04 s with 255.
- For a container call, 137, -9 or 255 at or after the limit is the time limit.
- For any other call only 137 or -9 (`KILL_STATUSES`) is, because 255 is no kill there.
- 255 before the limit stays an ordinary exit status, because a command can exit 255 by itself.
- Only the elapsed time tells that podman's timeout was the cause.

**For the preflight.** `version()` returns the first non-blank line of `<podman> --version` (`podman version 4.9.3`). `image_exists()` runs `<podman> image exists <image>`: exit status 0 is `True`, 1 is `False`. Both run with `workspace` as working directory and the constructor's `time_limit`. Every other outcome is `ContainerError(<command words joined by a space>, <detail>)`:

- an exit status other than 0 (for `image_exists`, other than 0 or 1): the last non-blank output line, or `exit status <n>`;
- `no end within <n> s`, `n` the limit rounded up;
- `printed nothing`, for `version` only, when exit status 0 comes with no output;
- the operating system's message when the executable cannot start.

The preflight reads a missing `podman` from this error. The line helpers (`first_printed_line`, `failure_detail`, `no_end_detail`) are in [printed_output.py](../../src/factory/shared/adapters/printed_output.py) (`factory.shared.adapters.printed_output`), shared with `ZfsSnapshots`.

### The podman stand-in

[podman_support.py](../../tests/support/podman_support.py) writes a stand-in `podman` into `tmp_path`. It records its arguments, environment and working directory. It prints planned output, waits and exits with a planned status, or, when its arguments hold the image, runs the words after the image on the host, so that a command's own exit status and output pass through. Tests of the default limit and of the kill rule replace the module's `run_process` with the `Recorder` of `run_process_recorder.py`. The tests are [test_podman_runs.py](../../tests/machine/adapters/test_podman_runs.py) (the command line), [test_podman_runs_fence.py](../../tests/machine/adapters/test_podman_runs_fence.py) (the four words and the constants) and [test_podman_runs_results.py](../../tests/machine/adapters/test_podman_runs_results.py) (results and faults).

### The sync script

The script of `prepare` is one literal, `_SYNC_SCRIPT`. The sync container runs:

    containers.run(["/bin/sh", "-c", <script>, "factory-sync", "/work/checkout", "/work/home", "/upstream", "/etc/factory/agents", branch, commit], ...)

- The mounts, the first two read-only: the host checkout's `.git` at `/upstream` (`UPSTREAM`) and `settings.agent_home` at `/etc/factory/agents` (`AGENT_FILES`).
- The environment is `{**extra_environment, **SYNC_ENVIRONMENT, "PATH": boundaries.image_path}`: `HOME=/work/home`, and the `PATH` of the image in use (`/usr/local/bin:/usr/bin:/bin` when it sets none). These win over the operator's extras.
- The CA bundle, when `ca_bundle` is set, is a third read-only mount at its own path.
- The time limit is `sync_time_limit` and the working directory is `/work`. `/work` is the dataset, so `/work/checkout` and `/work/home` are its two folders.

Every container path reaches the script as an argument (`$1` checkout, `$2` home, `$3` upstream, `$4` agent files, `$5` branch, `$6` commit), and none is written in its text, so that `FakeContainerRuns`, which maps paths in the command words, can play it on the host. With `set -eu` it stops at the first failure and:

1. makes `$1` and `$2` when missing;
2. replaces `$2/.claude` with a copy of `$4`. The copy replaces the folder, it does not merge, so an agent file removed on the host is gone in the next stage and one run cannot widen the tools of the next. The factory process copies no files itself;
3. in `$1`, runs `git init -q` when there is no `.git`;
4. fetches `+refs/heads/*:refs/heads/*` and `+refs/heads/*:refs/remotes/origin/*` from `$3` in one `git fetch` with `--prune` and `--update-head-ok`;
5. runs `git checkout -q -f "$5"` and `git reset -q --hard "$6"`, so `HEAD` is on the branch at the stage-start commit and never detached;
6. runs `make sync` (*The sync command*).

Why the fetch is so wide:

- It takes every branch, not only the stage's, because a detached checkout would leave the agent without `main` and the branch, and the coder's and reviewer's instructions read `git diff main` and the branch's log.
- `--prune` drops a branch deleted on the host.
- `--update-head-ok` is needed because git refuses to fetch into the checked-out branch, an unborn one included, as a fresh `git init` has.
- The second refspec makes the checkout know `origin/main` and `origin/<branch>` as a clone would, because the project's commands read `origin/main`.
- `make secrets` limits itself to the files a branch changed against `origin/main`. Without that ref it scans every tracked file, and old hex values in finished acceptance reports would stop the check.

### The seven steps of the take

1. The baseline: the work item at `stage_start.commit`, read at the stage-start commit. When it is absent or unreadable there, `take` raises `WorkItemFormatError` naming `work_item_path`, before anything changes.
2. The write paths: `WritePathService(boundaries).at(stage_start, work_item_path)`.
3. The candidates: only paths under `checkout/` count, with that prefix removed. A path with a `.git` segment is dropped, and so is every path that `Git.ignored` names (the virtual environment, the reports folder). The ignore rules asked are those of the factory's own repository on the host, never the dataset's git. A path under `home/` or anywhere else is dropped. A dropped path is neither taken nor listed.
4. The refused: a candidate is refused when `refusal(path, settings)` is not `None` (outside the write paths, or protected), or when it lies directly in an `in-progress/` folder of a feature and is not the stage's own work item (the in-progress rule). `is_refused` is the function of the rule, in `take.py`. A refused path is listed in `left` and not copied. The dataset is never written.
5. The taken: every other candidate is copied with `copy_changed(mount_point / "checkout", boundaries.checkout, ...)`.
6. The work item: its state and journal are put back from the baseline with `restore_state_and_journal`, the agent's edits to its sections kept (`restore_work_item`, in `take.py`). A work item that was deleted, or whose front matter cannot be read, comes back whole from the stage-start commit. `restored_work_item` is true in all those cases and false when nothing changed. A work item the role may not write is refused like any path: it is in `left`, not copied, not restored, and `restored_work_item` is false.
7. `TakeReport(left, restored_work_item)`, frozen: `left` is sorted and holds each path once.

### The settings of the stage environment

An instance names its dataset, workspace and stage image in its environment variables.

| Variable | `InstanceSettings` field | Default |
|---|---|---|
| `FACTORY_DATASET` | `dataset` | none |
| `FACTORY_WORKSPACE` | `workspace` (`Path`) | none |
| `FACTORY_SNAPSHOTS` | `snapshots` (`"zfs"` or `"copy"`) | `zfs` |
| `FACTORY_SNAPSHOT_BASE` | `snapshot_base` (`Path`) | none |
| `FACTORY_STAGE_IMAGE` | `stage_image` | none |
| `FACTORY_PODMAN` | `podman_executable` | `podman` |
| `FACTORY_ZFS` | `zfs_executable` | `zfs` |

The refusals of `read_settings`:

- A relative workspace is `SettingsInvalid(FACTORY_WORKSPACE, "is not an absolute path")`.
- Then a `checkout`, and then a `state_directory`, that is the workspace or lies inside it (`Path.is_relative_to`, by path parts) is `SettingsInvalid(FACTORY_CHECKOUT, "<checkout> lies inside FACTORY_WORKSPACE")`, or the same for `FACTORY_STATE`.
- A `FACTORY_SNAPSHOTS` other than `zfs` or `copy` is `SettingsInvalid(FACTORY_SNAPSHOTS, "is neither zfs nor copy")`.
- `FACTORY_SNAPSHOT_BASE` is read like the other optional paths: blank is `None`, a relative path is refused.
- `snapshot_base_fault(snapshots, base, workspace, checkout, state_directory)` holds the rule on the base, for `read_settings` (as a `SettingsInvalid` on `FACTORY_SNAPSHOT_BASE`) and for the model validator (a `ValidationError`). With `zfs`, a base is `is only used with FACTORY_SNAPSHOTS=copy`. With `copy`, a base that is, holds or lies inside the workspace, the checkout or the state directory is `<base> overlaps <workspace|checkout|state>`, because every reset empties the workspace and the base must survive it. A missing base with `copy` is no fault of the settings; the wiring raises it.
- The model validator of `InstanceSettings` refuses the same combinations with a `ValidationError`. Its message is `<variable>: <fault>`, and it is not turned back into a `SettingsInvalid`.

`build_boundaries` refuses an incomplete instance before it builds anything: `_container_adapters` raises `SettingsInvalid(FACTORY_DATASET, "missing")`, then `SettingsInvalid(FACTORY_WORKSPACE, "missing")`, then `SettingsInvalid(FACTORY_STAGE_IMAGE, "missing")`, the first of the three that is `None`. With `FACTORY_SNAPSHOTS=copy` the dataset is not read and the first is `SettingsInvalid(FACTORY_SNAPSHOT_BASE, "missing")`, before the workspace and the image. Then it builds:

| Boundary | Built as |
|---|---|
| `snapshots`, `containers` | `ZfsSnapshots(dataset, workspace, drop_caches=DROP_CACHES_COMMAND, executable=zfs_executable)` (with `copy`: `CopySnapshots(workspace, snapshot_base)`) and `PodmanRuns(podman_executable, stage_image, workspace, instance=settings.instance, profile=settings.container_profile)` |
| `agent_runtime` | the runtime of `FACTORY_AGENT_RUNTIME` given `containers` |
| `project_commands` | `RecordingProjectCommands` around `ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout, extra_environment=extra, ca_bundle=settings.ca_bundle)` |

### How the stage file is followed

- `_ProjectImageStart` in [run.py](../../src/factory/entry/run.py) (`factory.entry.run`) calls `chosen_image` once the checkout is ready, after a fetch, and again whenever the stage file changes on a new `origin/main`.
- `_ProjectImageStart.prepare` fetches before every tick, beside where the preflight probes `main`. It reads the file with `stage_file_on_main` and compares its text with the one last handled. Equal text is equal digest, and it also covers a refused file, which has none.
- The same text builds nothing and does not retry a failed one.
- A different text calls `chosen_image`. It passes a `StageImageReport` (`stage_image_report`: log, clock, the commit's first 12 hex digits) when a stage file exists or at the start. A later follow without a stage file passes none. Given a report, `chosen_image` writes the `stage image:` lines and puts `at <commit>: ` before the stop's detail.
- A passed build gives a new tick on boundaries built from the chosen settings (image, identity and `Boundaries.image_path` change together). A tick that is running keeps its own, so the change takes effect between stages.
- `prepare` guards its fetch. `_follow_main` catches `FetchFailed` (any other `GitError` is not caught and reaches the scheduler's `iteration failed`), raises the repository stop `fetch_failed` with `str(error)` as its detail through `StopService`, and returns `False`. Then `prepare` returns `False` and no tick runs in that iteration. It reads no stage file then and leaves the image, identity, `PATH` and the stage file last handled as they were.
- A fetch that passes calls `clear_stop("fetch_failed")` and compares as above.
- This is the one fetch of the iteration. `_choose` builds the tick with `fetched=True` (`activity_tick(..., fetched=True)`), so `Tick.run` does not fetch again and does not raise or clear `fetch_failed` itself. `_follow_main` is the only place that does in `factory-run`.
- A failed build drops the tick: no tick runs while the stop stands.
- A removed file returns to the base and logs `back to the base`.
- `Images.build` removes the untagged images, so the previous project image goes.

### The items of the preflight

Each item takes the callable that reaches the machine.

| Item | Function | Callable | Fails with |
|---|---|---|---|
| `podman`, `zfs` | `tool_version_item(name, version)` | `PodmanRuns.version`, `ZfsSnapshots.version` | `<name> does not answer --version: <error>` on `SnapshotError` or `ContainerError`; passes with the printed line as its detail |
| `dataset` | `dataset_item(dataset, exists)` | `ZfsSnapshots.dataset_exists` | `the dataset <dataset> does not exist; make it with zfs create, and its base with zfs snapshot <dataset>@base`, or `cannot list the dataset <dataset>: <error>` on `SnapshotError` |
| `snapshots` (`copy` only) | `snapshots_item(workspace, base)` (it reads the file system with `Path.is_dir`) | none | `the workspace <w> is not a directory`, `the base <b> does not exist; make it empty with mkdir, the first advance fills it` or `the base <b> is not a directory`; passes with `workspace <w>, base <b>` |
| `stage-image` | `stage_image_item(image, exists)` | `PodmanRuns.image_exists` | `the stage image <image> is not built; build it with podman build`, or `cannot look for the stage image <image>: <error>` on `ContainerError` |
| `metadata-block` (`job` only) | `metadata_block_item(probe)`; `_container_items` adds it after `stage-image` | `_metadata_probe`: `PodmanRuns.run(list(METADATA_PROBE_COMMAND), mounts=[], environment={}, time_limit=30 s, working_directory=WORK)` | passes with `refused` when the last non-blank output line is `000`; fails, `timed_out` first, with `the metadata probe did not end within its limit`, `a container reached the metadata server (HTTP <code>); reject tcp port 80 to 169.254.169.254 in the job's firewall`, `the metadata probe could not tell (exit <status>): <line or "no output">`, or `cannot run the metadata probe: <error>` on `ContainerError`. The constants are in `factory.machine.domain.containers`, the line reader is [printed_lines.py](../../src/factory/shared/domain/printed_lines.py) |

### The order of `KnownResults.run`

1. It builds the `ResultKey`. The model is in [known_results.py](../../src/factory/pipeline/domain/known_results.py) (`factory.pipeline.domain.known_results`), frozen, with no unknown keys.
   - `command` is the command.
   - `tree` comes from `Git.work_tree_id(not_read)` with the command's `not_read`.
   - `definition` is `definition_digest(definition)`, a `DefinitionDigest`: the SHA-256 of `definition.model_dump_json()`, 64 lower-case hex characters, computed once in the constructor.
   - `image` comes from `settings.image`.
   - A `GitError` logs `known results: no key for <command>: <error>` and runs the command with no record.
2. It reads the records (an `OSError` logs `known results: cannot read the records: <error>` and counts as none) and asks `known_result(records, key)`: the last record of the key that is a real run (`reused` is `None`), when its status is `passed`; otherwise `None`. Reuse records are skipped, so a reuse never extends or ends a pass, and a later failed run of the key ends it.
3. A known result is not run again. A `ResultRecord` with `status` `passed`, `duration_seconds` 0 and `reused` the first run's `at` is appended, and the result is a `CheckResult` with exit status 0, duration 0, the earlier `last_line`, an empty `output_tail`, no `targets` and `reused=ReusedRun(tree, at)`.
4. Otherwise the command runs, the clock is read before it, and a `ResultRecord` (`key`, `at`, `status`, `last_line`, `duration_seconds`, `reused=None`) is appended. A failed append logs `known results: cannot write the record of <command>: <error>` and the result is still returned. A `ProjectCommandError` or `ValueError` of the run propagates and records nothing.

`ResultRecord` refuses a `reused` on a status other than `passed`. `ReusedRun` (in `checks.py`: `tree`, `at`) is the earlier run a reused `CheckResult` took. `command_line(result)` is the line of a result in an entry:

- `` `<command>`: <last line> `` and, for a reused result, `` (not run again: passed on tree <first 12 characters> at <UTC, whole seconds>) `` after it.
- For a result whose status is `time_limit`, the line ends with `` (stopped at its time limit after <s> s) ``, `<s>` being `int(duration.total_seconds())` (whole seconds, rounded down). With an empty `last_line` the note follows `` `<command>`: `` directly.
- A reused result is always `passed`, so the two notes never meet. A passed or failed result gets no note.

Tests: [test_command_line_time_limit.py](../../tests/pipeline/domain/test_command_line_time_limit.py) and [test_stage_time_limited_report.py](../../tests/pipeline/application/test_stage_time_limited_report.py).

### The temporary folder of a mutants run

- The recipe runs mutmut with `TMPDIR` set to a folder of its own, made by `mktemp -d`. Its `EXIT` trap opens that folder for its owner and removes it. This happens also after a stop (`MUTANTS_SECONDS`) and after a failed run, so a run leaves `/tmp/pytest-of-<user>` as it found it (*make mutants runs under a temporary root of its own* in [decisions.md](../decisions.md)).
- `timeout` puts mutmut into a process group of its own, but it stays in `make`'s session.
- A kill at the time limit of a `make mutants` run through `MakeProjectCommands.run` ends `make`'s process group only (*Reading output and killing a group* in [shared.md](shared.md)). A mutmut in a group of its own survives it.
- A caller that kills `make` itself, such as a shell's `timeout`, reaches only `make`'s group too.
- A run that the factory kills at its time limit ends `make`'s group with SIGKILL, which runs no `EXIT` trap. The temporary folder stays, under the `TMPDIR` of the caller of `make`, and the operator removes it by hand.
- A process that one of mutmut's tests started through `process.py` is not in that session, because the code under test starts every command in a session of its own (`start_new_session`).
- The kill does not reach it, and it runs on until it ends by itself. An example is the fake `claude` of `test_call_over_its_time_limit_is_killed_with_unknown_measures` in [test_claude_runtime.py](../../tests/agents/adapters/test_claude_runtime.py), which runs for up to 60 s after a kill.
