---
stage: done
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 407
comments_read: [6383665028]
handed_over: approval
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T11:31:06.820036Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T11:31:26.244219Z'
  stage: intake
  run: 1063050e89f740548207d6a2045ba47f
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T11:31:46.552456Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T11:36:30.531950Z'
  stage: tests
  run: ee5c2465faa04f918eacd1bcd6e8e185
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T11:36:51.269170Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T11:44:01.376474Z'
  stage: doing
  run: 5fd83f898f424823942b456888911249
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T11:44:23.125283Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T11:46:19.808017Z'
  stage: review
  run: 626c0b678e454eaab931856ddbd7bc41
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T11:46:40.491756Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T11:50:08.844469Z'
  stage: doing
  run: a7a0534a67a347b5b15153f9e83095c0
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T11:50:29.798511Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-24T11:51:34.837316Z'
  stage: review
  run: fb967a6118304eed8a27e13de2d22fae
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-24T11:51:55.237925Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-24T11:55:22.412432Z'
  stage: doing
  run: 593a404a9175496396985a2e27da90e2
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T11:55:43.253649Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-24T11:56:56.797029Z'
  stage: review
  run: 97a795eba6414b6ea423057d0ea41aec
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-24T11:57:18.432416Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-24T11:58:12.651484Z'
  stage: docs
  run: 9846f9ab16484bf786777d767bdd5f10
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-24T11:58:34.137156Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T11:59:16.148911Z'
  stage: smoke-test
  run: 0d4f792cc7ff4877a41cbb4f4ba9c8da
- number: 25
  speaker: factory
  kind: done
  at: '2026-10-24T12:01:39.977394Z'
  stage: approval
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
2. `ContainerLaunch` refuses an empty `argv` and a `time_limit` of 0 and of -1 second, and accepts one word and 1 second; it accepts `env=None` and `env={}` and keeps `env` as given (rows of one parametrized test). `ContainerResult` (rows of one parametrized test): `exit_status=None, timed_out=True` and `exit_status=0, timed_out=False` and `exit_status=137, timed_out=False` are accepted; `exit_status=None, timed_out=False` and `exit_status=137, timed_out=True` are refused with `ValidationError`.
3. `SnapshotError("zfs rollback -r tank/f@base", "dataset is busy")` has `command` and `detail` as given and `str()` `snapshot command zfs rollback -r tank/f@base failed: dataset is busy`; `ContainerError("podman", "[Errno 2] No such file or directory")` likewise with `container command podman failed: [Errno 2] No such file or directory`; both are `BoundaryError`s and `FactoryError`s (rows of one parametrized test over the two classes).
4. `Snapshots` and `ContainerRuns` are abstract base classes whose abstract members are exactly `{"mount_point", "reset", "advance", "changed_paths"}` and `{"launch", "run"}`; neither can be instantiated (`TypeError`); a subclass that leaves one out cannot be constructed and one that implements all is an instance of the interface; neither module names `Protocol` (rows of the parametrized tests of `tests/application/test_interfaces.py`, which gains the two interfaces, and two assertions in its operations test).
5. `FakeSnapshots.advance()` then `changed_paths()` is `[]`; after `advance()`, writing a new file `b/new.txt`, changing the bytes of `a.txt`, removing `gone.txt` and making `empty/` gives `changed_paths()` `[ChangedPath("a.txt", "modified"), ChangedPath("b/new.txt", "added"), ChangedPath("gone.txt", "deleted")]`: the folder `empty/` and the folder `b/` are not listed, the order is by path.
6. After `advance()`, a mode change alone (`chmod` of `a.txt` from `0o644` to `0o755`) is `modified`; a symbolic link whose target text changed is `modified`; a symbolic link that is new is `added` and is listed as a link, not as the file it points to (rows of one parametrized test).
7. `reset()` after the changes of criterion 5, with a symbolic link `link` to `a.txt` made before `advance()` and removed after it, puts the folder back: `a.txt` has the base's bytes and mode, `b/new.txt` and `empty/` are gone, `gone.txt` is back, `link` is back as a link to `a.txt`, `changed_paths()` is `[]`, and `folder` itself still exists. `reset()` with no `base` folder raises `SnapshotError` whose `command` is `reset` and whose `detail` is `no base at <base>`, and the folder is unchanged; `changed_paths()` with no `base` raises it with `command` `changed_paths` (rows of one parametrized test).
8. `advance()` a second time replaces the base: after `advance()`, a change, `advance()` again, `changed_paths()` is `[]` and `reset()` keeps the change. `mount_point` is the folder given. A file that is in the old base but was deleted from the folder before the second `advance()` is not brought back by `reset()` (a row of the same parametrized test).
9. `FakeContainerRuns(workspace).launch(["/bin/sh", "-c", 'echo "$1" "$HOME"', "x", "/work/checkout/src"], mounts=[Mount(source=<tmp>/state/runs/i.md, target="/state/runs/i.md", read_only=True)], environment={"HOME": "/work/home", "PATH": "/usr/bin:/bin"}, time_limit=10 s, working_directory="/work/checkout")` returns `argv` `["/bin/sh", "-c", 'cd "$1" && shift && exec "$@"', "fake-container", "<workspace>/checkout", "/bin/sh", "-c", 'echo "$1" "$HOME"', "x", "<workspace>/checkout/src"]`, `env` `{"HOME": "<workspace>/home", "PATH": "/usr/bin:/bin"}` and `time_limit` 10 seconds; a word `/state/runs/i.md` maps to `<tmp>/state/runs/i.md`, a word `/workspace` (not `/work/...`) stays `/workspace`, `/work` alone maps to `<workspace>` (rows of one parametrized test over words), and a key of `environment` is never mapped: `environment={"/work": "/work"}` gives `env` `{"/work": "<workspace>"}`.
10. The longer target wins: with the mounts `target="/mnt"` and `target="/mnt/deep"`, the word `/mnt/deep/x` maps to the deep mount's source, `/mnt/other` to the shallow one's, and `/mnt/deeper` (no slash after `/mnt/deep`) to the shallow one's too (rows of one parametrized test).
11. `run(["/bin/sh", "-c", 'pwd; printf "%s\n" "$HOME"; echo "$1"; echo err >&2', "x", "/work/checkout"], mounts=[], environment={"HOME": "/work/home"}, time_limit=10 s, working_directory="/work/checkout")` on a `workspace` whose `checkout/` exists gives `exit_status` 0, `timed_out` false and `output` the three mapped lines `<workspace>/checkout`, `<workspace>/home`, `<workspace>/checkout` and then `err` (stderr merged); `run(["/bin/sh", "-c", "exit 3"], ...)` gives `exit_status` 3; `run(["/bin/sh", "-c", "sleep 30"], ..., time_limit=1 s)` gives `timed_out` true and `exit_status` `None` after at least 1 and less than 25 seconds, with `duration` at least 1 second and under 25 seconds, and `duration` greater than 0 for the successful run (rows of one parametrized test); `run(["/nowhere/program"], ...)` gives `exit_status` 127, `timed_out` false and an `output` that contains `/nowhere/program` (the shell starts and cannot find the program inside); `run(["/bin/sh", "-c", "true"], ..., working_directory="/work/missing")` on a `workspace` without `missing/` raises `ContainerError` whose `command` is `/bin/sh` and whose `detail` starts with `[Errno 2]`.
12. `launch` and `run` raise `ValueError` for a mount with target `/work` and for one with target `/work/checkout`, and for a `command` of `[]`, and `calls` records nothing of those; a mount with target `/workspace` is accepted and recorded in `calls` (rows of one parametrized test); after one `launch` and one `run` that were accepted, `calls` holds two `ContainerCall`s with the command, mounts, environment, time limit and working directory exactly as given, in order.
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
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures are named (`factory.domain.containers`, `factory.domain.errors`, `factory.application.snapshots`, `factory.application.containers`, `factory.adapters.fake_snapshots`, `factory.adapters.fake_containers`). The behaviours in the Interface text are all covered by criteria.
   - Criteria: each can be tested by one parametrized test function. Each rule has its failing side: invalid `Mount.target` and `ContainerResult` combinations, empty `argv`, a zero or negative `time_limit`, no `base` for `reset` and `changed_paths`, `ValueError` for `/work` mounts and an empty command, and `ContainerError` for a missing working directory. Journal entry 4 (the human's answer to my four questions) is carried in as four additions, with no other change to the story. Criterion 2 gained `env=None` and `env={}` accepted and `env` kept as given. Criterion 8 gained the row where a file is deleted, `advance()` is called, and `reset()` does not bring it back. Criterion 11 gained `duration` at least 1 s and under 25 s on the timeout row, and greater than 0 on the successful run. Criterion 12 gained the row where a mount with target `/workspace` is accepted and recorded in `calls`.
   - Smoke test: both blocks are runnable. Each has an `Expect:` line that can be checked against the output. The pytest command passes no `-q`, because `addopts` already sets one, so the `passed in` summary line is printed.
   - Architecture: interfaces are ABCs in `application`, the DTOs are in `domain`, the fakes are in `adapters`, and the process module is used only through `run_process`. This matches the layering in `CLAUDE.md`.
   - Scope: the story is within F0042's scope as feature.md lists it for S0001. It touches no "Out of scope" item. The tests it changes (`tests/application/test_interfaces.py`, `tests/test_wrapper_search.py`) are covered by decision 18 a of feature.md.
7. factory: started tests as self.
8. tester: I wrote the red tests for every criterion, one test per criterion. Where a criterion has several cases, they are rows of one parametrized test. `make lint` is green. `make test` was run once: it fails at collection with ImportErrors, because the modules under test do not exist yet.

   - criterion 1: tests/domain/test_containers.py::test_a_mount_target_is_an_absolute_container_path, ::test_a_mount_source_must_be_absolute, ::test_a_mount_is_writable_by_default
   - criterion 2: tests/domain/test_containers.py::test_a_container_launch_needs_words_and_a_positive_limit_and_keeps_env, ::test_a_container_result_has_no_exit_status_exactly_when_it_timed_out
   - criterion 3: tests/domain/test_errors_environment.py::test_an_environment_error_names_its_command_and_detail
   - criterion 4: tests/application/test_interfaces.py (the `snapshots` and `container-runs` rows in INTERFACES, and two assertions added to ::test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract), tests/application/test_snapshots_interface.py::test_a_snapshots_subclass_must_implement_every_operation_to_be_constructed, tests/application/test_containers_interface.py::test_a_container_runs_subclass_must_implement_every_operation_to_be_constructed
   - criterion 5: tests/adapters/test_fake_snapshots.py::test_changed_paths_lists_added_modified_and_deleted_files_by_path
   - criterion 6: tests/adapters/test_fake_snapshots.py::test_a_mode_or_a_link_change_is_listed
   - criterion 7: tests/adapters/test_fake_snapshots.py::test_reset_puts_the_folder_back_to_the_base, ::test_without_a_base_the_operation_fails_and_leaves_the_folder
   - criterion 8: tests/adapters/test_fake_snapshots.py::test_a_second_advance_replaces_the_base, ::test_the_mount_point_is_the_folder_given
   - criterion 9: tests/adapters/test_fake_containers.py::test_launch_maps_the_words_environment_and_working_directory, ::test_a_word_maps_only_to_a_mount_it_equals_or_lies_under, ::test_an_environment_key_is_never_mapped
   - criterion 10: tests/adapters/test_fake_containers.py::test_the_longer_mount_target_wins
   - criterion 11: tests/adapters/test_fake_containers.py::test_run_returns_the_status_the_merged_output_and_the_end, ::test_a_program_the_shell_cannot_find_is_a_result_with_status_127, ::test_a_missing_working_directory_is_a_container_error
   - criterion 12: tests/adapters/test_fake_containers.py::test_a_mount_on_work_and_an_empty_command_are_refused_and_not_recorded (rows × launch/run), ::test_calls_records_each_accepted_call_as_given_in_order
   - criterion 13: the factory's `make check`. Criterion 14 (docs): no test.

   Files created: tests/domain/test_containers.py, tests/domain/test_errors_environment.py, tests/application/test_snapshots_interface.py, tests/application/test_containers_interface.py, tests/adapters/test_fake_snapshots.py, tests/adapters/test_fake_containers.py.

   Earlier test files changed:
   - tests/application/test_interfaces.py: criterion 4 names this change.
   - tests/test_wrapper_search.py: `factory.adapters.fake_containers` was added to the expected importers of the process module. The story's Interface names this change, citing decision 18 a of the feature. Every earlier test there keeps its name.

   Modules the test run could not import: factory.domain.containers, factory.application.snapshots, factory.application.containers, factory.adapters.fake_snapshots, factory.adapters.fake_containers, and `SnapshotError`/`ContainerError` from factory.domain.errors. tests/test_wrapper_search.py fails on a wrong result until fake_containers imports the process module.

   Two choices of mine, both within what the criteria say:
   - In criterion 7's reset test, a.txt's mode is also changed to 0o755 before `reset()`. Without that change, the check that `reset()` restores the base's mode would prove nothing.
   - Where a child must act before its limit (criteria 11 and 12), it gets `ROOMY_LIMIT` (10 s, the value criterion 11 gives). The timeout row keeps its 1 s limit and is bounded by `ROOMY_BOUND_SECONDS` (25 s).

   Nothing is open.

   `lint`: lint: green (0.7 s)
   `test`: ERROR tests/domain/test_errors_environment.py - ImportError while importing test module '/work/checkout/tests/domain/test_errors_environment.py'.
9. factory: started doing as self.
10. coder: I built the two interfaces, their data, the two errors and the two fakes, as the Interface describes. No test was changed. `make check` is green. The first smoke block gives the five expected lines.

    - `src/factory/domain/containers.py`: holds `WORK`, `WORK_CHECKOUT`, `WORK_HOME`, `Mount`, `ContainerLaunch`, `ContainerResult` (with a model validator: `exit_status` is `None` exactly when `timed_out`) and `ContainerCall`. `Mount.target` is a `ContainerPath`: it must start with `/`, and what follows must pass the existing `inside_home` of `factory.domain.agent_home` (no empty, `.` or `..` segment). I reused that helper instead of writing a second segment check. One side effect: a `.` segment (`/a/./b`) is refused too, which the Interface does not mention.
    - `src/factory/domain/errors.py`: `SnapshotError` and `ContainerError` sit beside the other `BoundaryError`s, shaped like `ProjectCommandError`.
    - `src/factory/application/snapshots.py` and `src/factory/application/containers.py`: the two abstract base classes, written as given.
    - `src/factory/adapters/fake_snapshots.py`:
      - `advance` removes the base, then copies the folder with `shutil.copytree(symlinks=True)`.
      - `reset` empties the folder (the folder itself stays), then copies the base back with `dirs_exist_ok=True`.
      - `changed_paths` compares two maps of relative path → (lstat mode, bytes or link target). It builds them with `os.walk`, so a link to a folder is listed as a link and not followed. Folders are never listed.
    - `src/factory/adapters/fake_containers.py`:
      - One private `_accept` checks the call (no command words, or a mount on `/work` or under it, raises `ValueError`), then records it. One private `_launch` maps the words, the environment values and the working directory. `launch` and `run` both use the two, so the checks and the recording are written only once.
      - `run` passes the launch through `run_process`, with `cwd` the mapped working directory and `merge_stderr=True`. An `OSError` there becomes `ContainerError(command[0], str(error))`.

    Main choice: the path mapping sorts every mount, the fixed `/work` one included, by target length (longest first) and takes the first that matches. I rejected a separate special case for `/work`: one list gives the "longer target wins" rule for both kinds of mount.

    Refactor: in `_entries` the relative path was computed twice, once per branch; it is now computed once. Nothing else needed changing.

    Noticed, not touched: `make duplicates` reports 8 new dead-code findings. They are the new classes, `mount_point`, `calls`, `read_only`, `WORK_CHECKOUT` and `WORK_HOME`, which nothing uses yet; S0002 to S0007 will use them. The documenter has criterion 14.

    `check`: check: green
    `duplicates`: duplicates: 8 new, 38 known, 0 gone
11. factory: started review as self.
12. reviewer: 1. `src/factory/domain/containers.py:16-19` (`_must_be_container_path`): the code refuses a `Mount.target` that the Interface accepts. The Interface gives the rule as: starts with `/`, names at least one segment, no `..` segment, no empty segment, no trailing slash. `/a/./b` meets every one of those conditions, so the Interface accepts it. The code checks targets with `inside_home` of `factory.domain.agent_home`, which also refuses a `.` segment, so `/a/./b` is refused. The coder's entry 10 names this side effect, but no criterion or answer from the human allows it, and no test pins it. Fix, either way: (a) refuse only what the Interface states, meaning an empty segment, a `..` segment and a trailing slash, so `/a/./b` is accepted; or (b) end with `question` and ask the human to add `.` segments to the Interface's refused list and a `/a/./b` row to criterion 1. Option (b) fits the reuse of `inside_home` and the refusal of `..`; option (a) is the story as written.

    I stopped at group 1, as the checklist says. The criteria tests I read do match criteria 1–12. The coder's journal entry 10 reports `check: green`.

    Earlier tests:
    - `tests/application/test_interfaces.py`: the human's leave in `feature.md` decision 18 (a). The story's Interface and criterion 4 name it. The diff stays within that leave: `INTERFACES` and `INTERFACE_IDS` each gain `Snapshots` and `ContainerRuns`, and `test_project_commands_and_agent_runtime_have_exactly_their_operations_abstract` gains the two assertions on `__abstractmethods__`. Every earlier test keeps its name.
    - `tests/test_wrapper_search.py`: the human's leave in `feature.md` decision 18 (a). The expected set gains `factory.adapters.fake_containers` and nothing else changes.
13. factory: started doing as self.
14. coder: Round 1. I fixed the reviewer's one finding with option (a), the story as written. No test was changed. `make check` is green.

    - `src/factory/domain/containers.py` (`_must_be_container_path`): `Mount.target` is no longer checked with `inside_home` of `factory.domain.agent_home`. The check now refuses only what the Interface states:
      - a target that does not start with `/`;
      - an empty segment, which also covers `/` alone, `/a//b` and a trailing slash;
      - a `..` segment.
      So `/a/./b` is now accepted, as the Interface says. The import of `inside_home` is gone. The new comment says why the path is split by hand: `PurePosixPath` would fold `/a//b` and `/a/` into valid paths.

    Main choice: I followed the Interface and did not ask. I rejected option (b), a question asking the human to add `.` segments to the refused list. It would widen the rule beyond the description just to keep one helper reused. I searched for an existing helper that refuses only empty and `..` segments. There are two `..` checks, in `factory.domain.git` and `factory.adapters.fake_agent_runtime`, but both go through `Path` parts, and `Path` folds `//`, so neither fits.

    Refactor: the diff is three lines, and nothing more needed changing.

    Noticed, not touched: no test pins `/a/./b` either way. If the reviewer wants that side pinned, it is a row for the tester in `tests/domain/test_containers.py`.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 8 new, 38 known, 0 gone
15. factory: started review as self.
16. reviewer: Round 1 review. Group 1 holds. Every criterion from 1 to 12 has a test that checks what it is named after. Each limit the Interface states is tested on both sides:
    - `Mount.target` accepted and refused rows
    - an empty `argv` refused and one word accepted
    - a time limit of 0 and -1 s refused, 1 s accepted
    - the four `exit_status`/`timed_out` combinations
    - `/work` and `/work/checkout` refused, `/workspace` accepted
    - the `/workspace` and `/mnt/deeper` words not mapped

    The round-0 finding is fixed: `src/factory/domain/containers.py:15-20` now refuses only what the Interface states, so `/a/./b` is accepted. Journal entry 14 reports `check: green`.

    Group 2 holds. The four layers are kept, both interfaces are ABCs whose method bodies are only their docstrings, and the DTOs live in `domain`. `fake_containers` reaches processes only through `run_process`, under decision 18 (a). Group 3 holds: no secrets and no silencing markers under `src/`. The test's `# noqa: PT011` gives its reason beside it, as `tests/domain/test_sessions.py:56` already does. Group 4 fails:

    1. `src/factory/adapters/fake_containers.py:115-116` (`_lies_under`): this is a second copy of the existing helper `_beneath_or_at` in `src/factory/domain/agent_home.py:51-52`. Both return `path == above or path.startswith(f"{above}/")`. Fix: move that helper to one public place in `factory.domain`. Either rename it in `agent_home` (for example `beneath_or_at`) or move it to a domain module that both callers import. Then use it in `fake_containers` for the `/work` refusal (line 83) and for the path mapping (line 110), and delete `_lies_under`. No test changes.

    Earlier tests:
    - `tests/application/test_interfaces.py`: the human's leave in `feature.md`, decision 18 (a), named by the story's Interface and criterion 4. `INTERFACES` and `INTERFACE_IDS` each gain the two interfaces. The operations test gains exactly the two `__abstractmethods__` assertions. Every earlier test keeps its name.
    - `tests/test_wrapper_search.py`: the human's leave in `feature.md`, decision 18 (a). The expected set gains `factory.adapters.fake_containers` and nothing else changes.

    Notes:
    - `tests/adapters/test_fake_containers.py`: `_run` (line 119) and `_run_with` (line 225) both call `runs.run` with nearly the same arguments, and `_launch` (line 216) repeats the pattern of `_launch_word` (line 29). One parametrized helper would do.
17. factory: started doing as self.
18. coder: Round 2. I fixed the reviewer's one finding from entry 16: `fake_containers` had a second copy of an existing helper. I changed no tests, and `make check` is green.

    - `src/factory/domain/agent_home.py`: the private helper `_beneath_or_at` is now public as `beneath_or_at`, with a one-line docstring. Its two callers in that module, `fate` and `removed_when_empty`, now use the new name. Its behaviour is unchanged.
    - `src/factory/adapters/fake_containers.py`: it now imports `beneath_or_at` and uses it for the `/work` mount refusal in `_accept` and for the path mapping in `_map`. I deleted the copy, `_lies_under`.

    Main choice: I made the helper public where it already was, in `factory.domain.agent_home`. I rejected moving it to another domain module such as `factory.domain.paths`. That would have touched more code for no gain. `agent_home` already gives the other path rule, `inside_home`, to callers outside the home (`factory.domain.settings`). Importing from it into an adapter is a downward import, which the layers allow.

    Refactor: I read the diff and found nothing else to change.

    Noticed, not touched:
    - In entry 16 the reviewer noted that the test helpers in `tests/adapters/test_fake_containers.py` repeat each other: `_run` and `_run_with`, and `_launch` and `_launch_word`. That is the tester's file, so I left it alone.
    - The module name `agent_home` is now a little narrow for a general path helper. Moving the helper is a restructuring outside this story.
    - The `.costs.jsonl` sidecar in the working tree is the factory's.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 8 new, 38 known, 0 gone
19. factory: started review as self.
20. reviewer: Round 2 review: no findings.

    - Round 1 finding fixed: `src/factory/domain/agent_home.py:51` makes the helper public as `beneath_or_at`, with a docstring. Its two callers in that module (`fate`, `removed_when_empty`) use the new name, and their behaviour is unchanged. `src/factory/adapters/fake_containers.py:84,111` uses it for the `/work` refusal and for the path mapping. The copy `_lies_under` is gone. Journal entry 18 reports `check: green`.
    - Group 1, the acceptance criteria: I read the tests again against criteria 1–12. Each criterion has a test that checks what it is named after. Each limit the Interface states is tested on both sides:
      - `Mount.target`: the accepted rows and the refused rows.
      - `Mount.source`: absolute and relative.
      - `argv`: `[]` refused, one word accepted.
      - `time_limit`: 0 s and -1 s refused, 1 s accepted.
      - `exit_status`/`timed_out`: all four combinations.
      - Mounts: `/work` and `/work/checkout` refused, `/workspace` accepted and recorded.
      - Words: `/workspace` and `/mnt/deeper` stay unmapped.
      - Also tested: environment keys are never mapped, and nothing is recorded for a refused call.
    - `run_process` gives `exit_status=None` exactly when the process timed out, so `ContainerResult`'s validator holds on the timeout path.
    - Group 2, architecture: the interfaces are ABCs in `application`, and their method bodies are only the docstrings. The DTOs are in `domain`. The adapters import downward only (`domain.agent_home`, `domain.containers`). `fake_containers` reaches processes only through `run_process`, under feature decision 18 (a).
    - Group 3, security: no secrets and no silencing markers under `src/`. The `/bin/sh -c` script is a fixed string, and the command words are passed as separate arguments.
    - Group 4, quality: there are no second copies of existing helpers. `fake_snapshots._clear` is not a copy of `git_cli._remove_entry`: that helper turns errors into `RepositoryUnsealed`.
    - Group 5, work item hygiene: the Description matches what was built, and the journal explains the main choices and what was rejected. Criterion 14 still says what the documenter must write.

    Earlier tests:
    - `tests/application/test_interfaces.py`: the human's leave in `feature.md`, decision 18 (a). `INTERFACES` and `INTERFACE_IDS` gain `Snapshots` and `ContainerRuns`, and the operations test gains exactly the two `__abstractmethods__` assertions. Every earlier test keeps its name.
    - `tests/test_wrapper_search.py`: the human's leave in `feature.md`, decision 18 (a). The expected set gains `factory.adapters.fake_containers` and nothing else changes.

    Notes:
    - `tests/adapters/test_fake_containers.py:118,211`: `_run` and `_run_with` call `runs.run` with nearly the same arguments.
    - `tests/adapters/test_fake_containers.py:30,201`: `_launch` repeats the pattern of `_launch_word`. One helper with parameters would cover both pairs.
21. factory: started docs as self.
22. documenter: Round 2 docs. No findings: the code matches the Interface and the criteria, and the round-2 change (`beneath_or_at` made public in `factory.domain.agent_home`) needs no documentation. I changed only documents, so I did not run `make check`; the factory's check after this stage decides. I ran no examples, because I wrote none.

    Files changed:
    - `docs/project-guide/stage-environment.md` (new): the guide file criterion 14 asks for. It has a title and a sentence naming the five modules, then the sections *The snapshots*, *The container runs* and *The fakes*.
      - *The snapshots*: the interface, the base, what `changed_paths` lists and does not list, and `SnapshotError`.
      - *The container runs*: `launch` against `run`, the fixed `/work` mount, the refused targets and `ContainerError`.
      - *The fakes*: the folder and its copy, the path mapping with the longer target winning, and what the fake cannot do (a read-only mount is not enforced, nothing is isolated).
      - It ends with the tests.
    - `docs/project-guide/README.md`: *The files* names `stage-environment.md` with its modules and sections. *Errors* names `SnapshotError` and `ContainerError` as `BoundaryError`s beside `ProjectCommandError`.

    Written to match the code, not only the Interface: `Mount.target` accepts `/a/./b`. The Interface lists only empty and `..` segments as refused, and round 1 fixed the code to match.

    Cross-read and found current: `docs/project-guide/README.md` (the *Errors* section apart from the lines I added) and `docs/project-guide/processes-and-checks.md`, for how `run_process` and the structural wrapper test are described. I did not read `docs/decisions.md`, since the criterion says it takes no entry in this story. I did not read `docs/operator-guide.md` or the top-level `README.md`: nothing in the diff is visible to the operator, because no module uses the new code yet.

    Stale text noticed, not touched:
    - In *Errors*, `AgentRuntimeError` is called the "fourth subtype" of `BoundaryError`. I did not number the two new errors, so the ordinal wording will need a look if the human cares about it.
    - `tests/adapters/test_fake_containers.py` has near-duplicate helpers (`_run` and `_run_with`, `_launch` and `_launch_word`), as the reviewer noted. That is the tester's file, not mine.
    - The module name `agent_home` is now narrow for a general path helper, as the coder noted.

    `check`: check: green (not run again: passed on tree 05aa75c575e2 at 2026-10-24T11:53:57Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
23. factory: started smoke-test as self.
24. smoke-tester: Smoke test, round 2. I ran both commands under `## Smoke test` from the repository root, exactly as written and in order. Both met their `Expect:` lines. I changed nothing.

    Command 1 (the Python script on `FakeSnapshots` and `FakeContainerRuns` in a `mktemp -d` folder that removes itself). Exit status 0. Output, with uv's bytecode line first:
    ```
    Bytecode compiled 4164 files in 86ms
    reset True
    [('checkout/a.txt', 'modified'), ('checkout/gone.txt', 'deleted'), ('checkout/new.txt', 'added')]
    [] ['a.txt', 'gone.txt']
    0 False ['W/checkout', 'W/home', 'W/checkout/a.txt', 'err']
    1 True /work/checkout
    ```
    Met: the script printed exactly the five expected lines, in order. The `Bytecode compiled` line is uv's own output, not the script's.

    Command 2 (`uv run pytest tests/application/test_interfaces.py tests/adapters/test_fake_snapshots.py tests/adapters/test_fake_containers.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`):
    ```
    1
    ```
    Met: `1` as expected. I ran the same pytest call again, outside the smoke test, only to see the line it counts: `67 passed in 1.58s`.

    Against the acceptance criteria, nothing the smoke test showed contradicts one:
    - Criterion 7: `reset()` with no base raised `SnapshotError`, its `command` was `reset` and its `detail` was `no base at <base>`.
    - Criterion 5: `changed_paths()` listed only files, sorted by path, with no folder in the list (`home/` was made after `advance()` and is not listed).
    - Criterion 7: after `reset()` the diff was empty, `gone.txt` was back and `new.txt` was gone.
    - Criterion 11: `run` mapped the working directory, `$HOME` and the command word, and merged stderr into the output.
    - Criterion 12: `calls` recorded the call as it was given (`/work/checkout`, the mount still `read_only`).

    Criteria 13 (`make check`) and 14 (docs) are not things the smoke test checks. Journal entry 22 records `check: green`, `secrets: green` and `documents ok` for them.

    Findings: none.
25. factory: done (pull request merged); cost: 11 runs, 19.6 min, 110 turns, 480561 tokens in (3070249 more from cache), 62479 out, $5.12
