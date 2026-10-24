# The stage environment

This file covers the two interfaces through which the factory reaches the dataset a stage runs on and the containers its commands run in, and their fakes; read the index, `README.md`, first. The modules are `factory.application.snapshots`, `factory.application.containers`, `factory.domain.containers`, `factory.adapters.fake_snapshots` and `factory.adapters.fake_containers`. Nothing in the factory uses them yet: the real adapters (ZFS snapshots, Podman runs) and the stage that wires them come in later stories of the same feature.

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
