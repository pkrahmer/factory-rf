# The stage environment

This file covers the two interfaces through which the factory reaches the dataset a stage runs on and the containers its commands run in, and their fakes; read the index, `README.md`, first. The modules are `factory.application.snapshots`, `factory.application.containers`, `factory.domain.containers`, `factory.adapters.zfs_snapshots`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. Nothing in the factory uses them yet: nothing wires `ZfsSnapshots`, and the Podman runs and the stage that wires them come in later stories of the same feature.

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

A `Mount` has a `source` (an absolute host path), a `target` (a container path) and `read_only` (default false). A target starts with `/` and has no empty segment and no `..` segment, so `/`, `a/b`, `/a//b`, `/a/` and `/a/../b` are refused with `ValidationError`; `/a/./b` is accepted. The dataset is the fixed `/work` mount of every run, so both operations raise `ValueError` for a mount whose target is `/work` or lies under it, and for a command without words.

`ContainerError(command, detail)` is the interface's `BoundaryError`, with the message `container command <command> failed: <detail>`. `ContainerCall` records one call as it was asked; only the fake uses it.

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
