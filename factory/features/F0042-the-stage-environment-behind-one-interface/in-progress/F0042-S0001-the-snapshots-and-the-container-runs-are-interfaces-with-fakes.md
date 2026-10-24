---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 407
comments_read: [6383665028]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T11:28:00.785243Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T11:28:00.792135Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T11:28:27.473945Z'
  stage: intake
  run: 2aa2e15d4c0247088365607baa43d949
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T11:30:48.737650Z'
  stage: intake
---

# The snapshots and the container runs are interfaces with fakes

## Description

v1.2 runs every stage on one ZFS dataset and in throwaway Podman containers (`planning/v1.2-plan.md`, "The cycle of a stage"). The factory must reach both through interfaces, so that the suite and the smoke tests run without `zfs` and `podman`, on Windows and in v1.1's container alike, and so that another snapshot tool can stand behind the same interface later (the human's decision 7). This story adds the two interfaces as abstract base classes in `factory.application`, the data they exchange in `factory.domain`, the two errors, and the two fakes in `factory.adapters`. `Snapshots` puts a dataset back to its base (`reset`), moves the base to the dataset's current state (`advance`) and lists what differs from the base (`changed_paths`); it also names the dataset's path on the host (`mount_point`). `ContainerRuns` gives the words that start one command in a fresh container on the dataset (`launch`) and runs one (`run`), with mounts, an environment, a time limit and a working directory. `FakeSnapshots` works on a folder whose base is a copy; `FakeContainerRuns` runs the command as a child process on the host with the container paths of its mounts mapped to host folders, as `FakeAgentRuntime` stands in for the runtimes today. Nothing uses the new modules yet: the real adapters are S0002 (ZFS snapshots) and S0003 (podman runs), the take S0004, the environment S0005 and S0007.

## Interface

`factory.domain.containers` (`domain`), new:

```python
WORK = "/work"
WORK_CHECKOUT = "/work/checkout"
WORK_HOME = "/work/home"


class Mount(BaseModel):
    """A host path mounted into a container: its source, its target, read-only or not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: AbsolutePath
    target: str
    read_only: bool = False


class ContainerLaunch(BaseModel):
    """The words, environment and time limit that start one command in a container."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    argv: Annotated[list[str], Field(min_length=1)]
    env: dict[str, str] | None  # `None`: the process's own environment (decision 11)
    time_limit: Annotated[timedelta, Field(gt=timedelta(0))]


class ContainerResult(BaseModel):
    """What one container run left: the command's exit status, its merged output, its end."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exit_status: int | None
    output: str
    timed_out: bool
    duration: timedelta


class ContainerCall(BaseModel):
    """One command a `ContainerRuns` was asked to launch or run, as it was asked."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: list[str]
    mounts: list[Mount]
    environment: dict[str, str]
    time_limit: timedelta
    working_directory: str
```

- `AbsolutePath` is the one of `factory.domain.agent_runs`. `Mount.target` is a container path: it starts with `/`, names at least one segment, and has no `..` segment, no empty segment and no trailing slash; `/work` and `/work/x` are accepted, `/` alone, `a/b`, `/a/../b`, `/a//b` and `/a/` are refused with `ValidationError`. The constants are the dataset's places in every container: the mount point, the checkout, the agent's home.
- `ContainerResult`: `exit_status` is `None` exactly when `timed_out` is true (a model validator; `ValidationError` otherwise).

`factory.domain.errors` (`domain`), two new `BoundaryError`s beside `ProjectCommandError`:

```python
class SnapshotError(BoundaryError):
    """A snapshot command failed, could not start or reached its time limit."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None: ...
    # The message: f"snapshot command {command} failed: {detail}"


class ContainerError(BoundaryError):
    """A container command failed, could not start or reached its time limit."""

    command: str
    detail: str

    def __init__(self, command: str, detail: str) -> None: ...
    # The message: f"container command {command} failed: {detail}"
```

`factory.application.snapshots` (`application`), new:

```python
class Snapshots(ABC):
    """One dataset and its base snapshot: the reset to it, the move of it, the diff against it."""

    @property
    @abstractmethod
    def mount_point(self) -> Path:
        """The dataset's path on the host; `changed_paths` are relative to it."""

    @abstractmethod
    def reset(self) -> None:
        """Put the dataset back to the base; `SnapshotError` without a base or on a tool fault."""

    @abstractmethod
    def advance(self) -> None:
        """Move the base to the dataset's current state; `SnapshotError` when the tool fails."""

    @abstractmethod
    def changed_paths(self) -> list[ChangedPath]:
        """Every non-directory entry that differs from the base, relative to the mount point.

        Sorted by path. Added, modified and deleted entries; a rename is a deletion and an addition.
        `SnapshotError` when there is no base or the tool fails.
        """
```

`factory.application.containers` (`application`), new:

```python
class ContainerRuns(ABC):
    """One command at a time in a fresh container on the dataset, which is mounted at `/work`."""

    @abstractmethod
    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """The words, environment and time limit that start `command` in a container.

        `ValueError` for a mount whose target is `/work` or lies under it, or for no command words.
        """

    @abstractmethod
    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Run `command` in a container until it ends or reaches `time_limit`; its output merged.

        A failing or timed-out command is a result; `ContainerError` means it could not start.
        `ValueError` as for `launch`.
        """
```

- Both interfaces follow `CLAUDE.md`: abstract base classes, every operation an `@abstractmethod` whose body is its docstring alone, no state, no `typing.Protocol`. `ChangedPath` is the model of `factory.domain.git` (`path`, `change` in `added`, `modified`, `deleted`).

`factory.adapters.fake_snapshots` (`adapters`), new:

```python
class FakeSnapshots(Snapshots):
    """Snapshots on a folder: the base is a copy of it beside it."""

    def __init__(self, folder: Path, base: Path) -> None: ...
```

- `mount_point` is `folder`.
- `advance()` replaces `base` with a copy of `folder`: every folder, regular file (bytes and mode) and symbolic link (as a link, not followed) under it; a missing `base` is made; what `base` held before is gone.
- `reset()` replaces the contents of `folder` with a copy of `base` the same way: an entry only in `folder` is removed, one only in `base` comes back, one in both takes the base's bytes and mode. `folder` itself stays (it is a mount point). Without a `base` folder it raises `SnapshotError("reset", f"no base at {base}")` and changes nothing.
- `changed_paths()` walks both trees and compares every non-directory entry by its path relative to the root: in `folder` only is `added`; in `base` only is `deleted`; in both with different bytes, a different mode or a different link target is `modified`; equal entries are left out. A directory is never listed, also an empty one. Paths use `/`, sorted by path. Without a `base` folder: `SnapshotError("changed_paths", f"no base at {base}")`.

`factory.adapters.fake_containers` (`adapters`), new:

```python
class FakeContainerRuns(ContainerRuns):
    """Container runs played on the host: a child process, the mounts' paths mapped to folders."""

    def __init__(self, workspace: Path) -> None: ...

    @property
    def calls(self) -> list[ContainerCall]:
        """Every call of `launch` and `run` that was not refused with `ValueError`, in order."""
```

- The mapping: the mounts given plus the fixed `Mount(source=workspace, target="/work")`. A word of `command`, a value of `environment` and the `working_directory` that equals a mount's `target`, or starts with the target followed by `/`, gets the mount's `source` (as a string) in the target's place; where two targets match, the longer one wins; anything else stays as it is. Keys of `environment` are never mapped.
- `launch(...)` returns `ContainerLaunch(argv=["/bin/sh", "-c", 'cd "$1" && shift && exec "$@"', "fake-container", <mapped working directory>, *<mapped command>], env=<mapped environment>, time_limit=time_limit)`: the time limit as given, no grace.
- `run(...)` runs `launch(...)` through `run_process` of `factory.adapters.process` with `cwd` the mapped working directory, `env` the mapped environment, `time_limit` as given and `merge_stderr` true, and returns `ContainerResult(exit_status=<the process's, or None when it timed out>, output=<the merged output>, timed_out=<the process's>, duration=<the process's>)`. A child that cannot be started (`OSError` from `run_process`: no `/bin/sh`, or a mapped working directory that does not exist) is `ContainerError(command[0], <the operating system's message>)`; a program the shell cannot find inside is a result with the shell's exit status 127, not an error.
- Both raise `ValueError` before any call is recorded or started for a mount whose target is `/work` or starts with `/work/`, and for an empty `command`. Every other call is appended to `calls` as the `ContainerCall` it was asked with (the command, mounts, environment, time limit and working directory as given, before the mapping).
- `fake_containers` imports the process module; the structural test `tests/test_wrapper_search.py` names it (decision 18 a of `feature.md`). `fake_snapshots` starts no process.

Tests (the tester writes them): `tests/domain/test_containers.py` (the four models), `tests/domain/test_errors_environment.py` (the two errors), `tests/application/test_snapshots_interface.py` and `tests/application/test_containers_interface.py` (the interfaces; `tests/application/test_interfaces.py` gains the two, decision 18 a), `tests/adapters/test_fake_snapshots.py`, `tests/adapters/test_fake_containers.py`. The fakes' tests work in `tmp_path`; the child processes are `/bin/sh` and `printf`, nothing a stage installs.

## Acceptance criteria

1. `Mount.target` (rows of one parametrized test): `/work`, `/work/checkout` and `/etc/factory/claude` are accepted as given; `/`, `work/x`, `/a/../b`, `/a//b`, `` (empty) and `/a/` are refused with `ValidationError`. `Mount.source` must be absolute (`/srv/x` accepted, `srv/x` refused), and `read_only` defaults to `False`.
2. `ContainerLaunch` refuses an empty `argv` and a `time_limit` of 0 and of -1 second, and accepts one word and 1 second (rows of one parametrized test). `ContainerResult` (rows of one parametrized test): `exit_status=None, timed_out=True` and `exit_status=0, timed_out=False` and `exit_status=137, timed_out=False` are accepted; `exit_status=None, timed_out=False` and `exit_status=137, timed_out=True` are refused with `ValidationError`.
3. `SnapshotError("zfs rollback -r tank/f@base", "dataset is busy")` has `command` and `detail` as given and `str()` `snapshot command zfs rollback -r tank/f@base failed: dataset is busy`; `ContainerError("podman", "[Errno 2] No such file or directory")` likewise with `container command podman failed: [Errno 2] No such file or directory`; both are `BoundaryError`s and `FactoryError`s (rows of one parametrized test over the two classes).
4. `Snapshots` and `ContainerRuns` are abstract base classes whose abstract members are exactly `{"mount_point", "reset", "advance", "changed_paths"}` and `{"launch", "run"}`; neither can be instantiated (`TypeError`); a subclass that leaves one out cannot be constructed and one that implements all is an instance of the interface; neither module names `Protocol` (rows of the parametrized tests of `tests/application/test_interfaces.py`, which gains the two interfaces, and two assertions in its operations test).
5. `FakeSnapshots.advance()` then `changed_paths()` is `[]`; after `advance()`, writing a new file `b/new.txt`, changing the bytes of `a.txt`, removing `gone.txt` and making `empty/` gives `changed_paths()` `[ChangedPath("a.txt", "modified"), ChangedPath("b/new.txt", "added"), ChangedPath("gone.txt", "deleted")]`: the folder `empty/` and the folder `b/` are not listed, the order is by path.
6. After `advance()`, a mode change alone (`chmod` of `a.txt` from `0o644` to `0o755`) is `modified`; a symbolic link whose target text changed is `modified`; a symbolic link that is new is `added` and is listed as a link, not as the file it points to (rows of one parametrized test).
7. `reset()` after the changes of criterion 5, with a symbolic link `link` to `a.txt` made before `advance()` and removed after it, puts the folder back: `a.txt` has the base's bytes and mode, `b/new.txt` and `empty/` are gone, `gone.txt` is back, `link` is back as a link to `a.txt`, `changed_paths()` is `[]`, and `folder` itself still exists. `reset()` with no `base` folder raises `SnapshotError` whose `command` is `reset` and whose `detail` is `no base at <base>`, and the folder is unchanged; `changed_paths()` with no `base` raises it with `command` `changed_paths` (rows of one parametrized test).
8. `advance()` a second time replaces the base: after `advance()`, a change, `advance()` again, `changed_paths()` is `[]` and `reset()` keeps the change. `mount_point` is the folder given.
9. `FakeContainerRuns(workspace).launch(["/bin/sh", "-c", 'echo "$1" "$HOME"', "x", "/work/checkout/src"], mounts=[Mount(source=<tmp>/state/runs/i.md, target="/state/runs/i.md", read_only=True)], environment={"HOME": "/work/home", "PATH": "/usr/bin:/bin"}, time_limit=10 s, working_directory="/work/checkout")` returns `argv` `["/bin/sh", "-c", 'cd "$1" && shift && exec "$@"', "fake-container", "<workspace>/checkout", "/bin/sh", "-c", 'echo "$1" "$HOME"', "x", "<workspace>/checkout/src"]`, `env` `{"HOME": "<workspace>/home", "PATH": "/usr/bin:/bin"}` and `time_limit` 10 seconds; a word `/state/runs/i.md` maps to `<tmp>/state/runs/i.md`, a word `/workspace` (not `/work/...`) stays `/workspace`, `/work` alone maps to `<workspace>` (rows of one parametrized test over words), and a key of `environment` is never mapped: `environment={"/work": "/work"}` gives `env` `{"/work": "<workspace>"}`.
10. The longer target wins: with the mounts `target="/mnt"` and `target="/mnt/deep"`, the word `/mnt/deep/x` maps to the deep mount's source, `/mnt/other` to the shallow one's, and `/mnt/deeper` (no slash after `/mnt/deep`) to the shallow one's too (rows of one parametrized test).
11. `run(["/bin/sh", "-c", 'pwd; printf "%s\n" "$HOME"; echo "$1"; echo err >&2', "x", "/work/checkout"], mounts=[], environment={"HOME": "/work/home"}, time_limit=10 s, working_directory="/work/checkout")` on a `workspace` whose `checkout/` exists gives `exit_status` 0, `timed_out` false and `output` the three mapped lines `<workspace>/checkout`, `<workspace>/home`, `<workspace>/checkout` and then `err` (stderr merged); `run(["/bin/sh", "-c", "exit 3"], ...)` gives `exit_status` 3; `run(["/bin/sh", "-c", "sleep 30"], ..., time_limit=1 s)` gives `timed_out` true and `exit_status` `None` after at least 1 and less than 25 seconds (rows of one parametrized test); `run(["/nowhere/program"], ...)` gives `exit_status` 127, `timed_out` false and an `output` that contains `/nowhere/program` (the shell starts and cannot find the program inside); `run(["/bin/sh", "-c", "true"], ..., working_directory="/work/missing")` on a `workspace` without `missing/` raises `ContainerError` whose `command` is `/bin/sh` and whose `detail` starts with `[Errno 2]`.
12. `launch` and `run` raise `ValueError` for a mount with target `/work` and for one with target `/work/checkout`, and for a `command` of `[]`, and `calls` records nothing of those (rows of one parametrized test); after one `launch` and one `run` that were accepted, `calls` holds two `ContainerCall`s with the command, mounts, environment, time limit and working directory exactly as given, in order.
13. `make check` stays green.
14. docs: a new guide file `docs/project-guide/stage-environment.md`, with its title and a sentence on what it covers, named in `docs/project-guide/README.md`, *The files*, with the modules it describes (`factory.application.snapshots`, `factory.application.containers`, `factory.domain.containers`, `factory.adapters.fake_snapshots`, `factory.adapters.fake_containers`) and its sections: *The snapshots* (the interface, the base, what `changed_paths` lists and does not), *The container runs* (the interface, `launch` against `run`, the fixed `/work` mount and the refused targets), *The fakes* (the folder and the copy, the path mapping and what the fake cannot do: a read-only mount), each naming the errors and the tests. `docs/project-guide/README.md`, *Errors*: `SnapshotError` and `ContainerError` beside `ProjectCommandError`. `docs/decisions.md`: none in this story (S0005 writes the entry "One snapshot instead of many layers").

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run python - "$d" <<'EOF'
import os
import sys
from datetime import timedelta
from pathlib import Path

from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.domain.containers import Mount
from factory.domain.errors import SnapshotError

d = Path(sys.argv[1])
work = d / "work"
(work / "checkout").mkdir(parents=True)
(work / "checkout" / "a.txt").write_text("one\n", encoding="utf-8")
(work / "checkout" / "gone.txt").write_text("x\n", encoding="utf-8")
snapshots = FakeSnapshots(work, d / "base")
try:
    snapshots.reset()
except SnapshotError as error:
    print(error.command, error.detail == f"no base at {d / 'base'}")
snapshots.advance()
(work / "checkout" / "a.txt").write_text("two\n", encoding="utf-8")
(work / "checkout" / "new.txt").write_text("n\n", encoding="utf-8")
(work / "checkout" / "gone.txt").unlink()
(work / "home").mkdir()
print([(c.path, c.change) for c in snapshots.changed_paths()])
snapshots.reset()
print(snapshots.changed_paths(), sorted(p.name for p in (work / "checkout").iterdir()))
containers = FakeContainerRuns(work)
result = containers.run(
    ["/bin/sh", "-c", 'pwd; echo "$HOME"; echo "$1"; echo err >&2', "x", "/work/checkout/a.txt"],
    mounts=[Mount(source=d / "login", target="/login", read_only=True)],
    environment={"HOME": "/work/home", "PATH": os.environ["PATH"]},
    time_limit=timedelta(seconds=10),
    working_directory="/work/checkout",
)
print(result.exit_status, result.timed_out, result.output.replace(str(work), "W").splitlines())
print(len(containers.calls), containers.calls[0].mounts[0].read_only, containers.calls[0].working_directory)
EOF
```
Expect: five lines: `reset True`; `[('checkout/a.txt', 'modified'), ('checkout/gone.txt', 'deleted'), ('checkout/new.txt', 'added')]`; `[] ['a.txt', 'gone.txt']`; `0 False ['W/checkout', 'W/home', 'W/checkout/a.txt', 'err']`; `1 True /work/checkout`

```bash
uv run pytest tests/application/test_interfaces.py tests/adapters/test_fake_snapshots.py tests/adapters/test_fake_containers.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says `FakeContainerRuns.launch` and `run` raise `ValueError` for a mount whose target "is `/work` or starts with `/work/`". Criterion 12 covers only the refused side (`/work`, `/work/checkout`). Nothing says that a mount with target `/workspace` or `/work-x` is accepted (and recorded in `calls`). Criterion 9 only maps a word `/workspace`, not a mount. Should I add a criterion, in the rows of criterion 12, that a mount with target `/workspace` is accepted? I would add it.

   2. `ContainerLaunch.env` is `dict[str, str] | None`, and the Interface comment says `None` means "the process's own environment (decision 11)". Criterion 2 tests only `argv` and `time_limit`. Nothing checks that `env=None` is accepted, or that `ContainerLaunch` keeps `env` as given. Should I add `env=None` and `env={}` as accepted rows of criterion 2? I would add them.

   3. `run(...)` returns `duration=<the process's>`. No criterion checks it. A coder could return a constant and pass every test. Should I add a criterion, in the timeout row of criterion 11, that `duration` is at least 1 second and under 25 seconds, and that it is greater than 0 for the successful run? I would add it.

   4. Criterion 8 says `advance()` replaces the base, "what `base` held before is gone". Only the changed-then-advanced case is tested. A file that is in the old base but no longer in the folder is not covered. Should I add a row where a file is deleted, then `advance()` is called, and then `reset()` does not bring it back? I would add it.

   The format check passed. The smoke test's pytest command passes no `-q`, and `addopts` already sets one, so the `passed in` line will be there. The architecture and the feature's scope check out, so I would accept once these four are settled.
4. 2026-10-24 human: All four as you propose, in your exact words:

   1. Yes: add to the rows of criterion 12 that a mount with target `/workspace` is accepted and recorded in `calls` (the near side of "is `/work` or starts with `/work/`").
   2. Yes: add `env=None` and `env={}` as accepted rows of criterion 2, and that `ContainerLaunch` keeps `env` as given.
   3. Yes: add to the timeout row of criterion 11 that `duration` is at least 1 second and under 25 seconds, and that it is greater than 0 for the successful run.
   4. Yes: add a row to criterion 8 where a file is deleted, then `advance()` is called, and then `reset()` does not bring it back.

   You have leave to edit the Acceptance criteria for exactly these four additions; the Interface and the Description stay as they are.
