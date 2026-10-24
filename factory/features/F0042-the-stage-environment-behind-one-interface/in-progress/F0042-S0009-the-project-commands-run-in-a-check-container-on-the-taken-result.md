---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 1
pull_request: null
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T19:27:01.642983Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T19:27:01.649011Z'
  stage: intake
- number: 3
  speaker: factory
  kind: crash
  at: '2026-10-24T19:35:48.210269Z'
  stage: intake
---

# The project commands run in a check container on the taken result

## Description

Step 7 of the cycle (`planning/v1.2-plan.md`, "The cycle of a stage"): the checks see the taken result on a clean base. The dataset is rolled back to the base, the files the take brought into the host's work tree are copied in, and a container runs `make sync && make <command>` with `--timeout` as the command's time limit; a file a check makes stays in its container. This story adds `ContainerMakeCommands`, the second make-based implementation of `ProjectCommands`, beside `MakeProjectCommands` in `factory.adapters.make_commands`, which reads a command's output exactly as the first does. What to copy in is what differs from `HEAD` on the host (`git.changed_paths("HEAD")`: after the take, the taken files, the restored work item and the factory's cost record; at the preflight's `lint` on `main`, nothing), mirrored with `copy_changed` of S0004 (decision 7 of `feature.md`); so nothing is remembered between the take and the checks. `KnownResults` and `RecordingProjectCommands` are unchanged: the wiring (S0010) puts the class behind them for a `container` instance. The suite runs it on `FakeSnapshots` and `FakeContainerRuns` with a real `make` as the child process. What stays: `MakeProjectCommands` and `SealedProjectCommands`, the inline instance's commands, untouched.

## Interface

`factory.adapters.make_commands` (`adapters`):

```python
CHECK_ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": WORK_HOME}


class ContainerMakeCommands(ProjectCommands):
    """Runs `make sync && make <command>` in a check container on the rolled-back base with the taken files."""

    def __init__(
        self, snapshots: Snapshots, containers: ContainerRuns, git: Git, *, checkout: Path
    ) -> None: ...
```

- `run(command, *, time_limit)`, in this order: a `time_limit` of 0 or less raises `ValueError`, a command name that does not match `COMMAND_NAME_PATTERN` raises `ProjectCommandError(command, f"invalid command name {command!r}")`, both before anything runs (as in `MakeProjectCommands`); `snapshots.reset()`; `copy_changed(checkout, snapshots.mount_point / "checkout", git.changed_paths("HEAD"))`; `containers.run([SHELL_EXECUTABLE, "-c", '"$1" sync && "$1" --no-print-directory "$2"', "factory-check", "make", command], mounts=[], environment=CHECK_ENVIRONMENT, time_limit=time_limit, working_directory=WORK_CHECKOUT)`; the result read into a `CheckResult` with `command`, `status` by `status_of` of the exit status (`None` when `timed_out`, so `time_limit`), `exit_status`, `duration`, `last_line` (`factory.domain.checks.last_line`, which S0007 moves there from `MakeProjectCommands`: the last non-blank line that is no make message; shared, not copied), `output_tail` (the last `OUTPUT_TAIL_LINES` lines, read by the same code as `MakeProjectCommands`) and `targets` (`target_times` of the output, so `sync`'s own green line counts among them).
- `SnapshotError` from the reset and `ContainerError` from the container are turned into `ProjectCommandError(command, <the error's message>)`; `GitError` from `changed_paths` and `ValueError` from `copy_changed` propagate as they are.
- The dataset's own `.git` is never touched: `changed_paths` never lists a `.git` path, and `copy_changed` writes under `<mount_point>/checkout` only.
- `tests/test_make_search.py` allows the word `make` in this module already; the class names it here and nowhere else.

Tests (the tester writes them): `tests/adapters/test_make_commands_container.py`, with `FakeSnapshots` and `FakeContainerRuns` on `tmp_path`, a host checkout made with the `checkout` fixture (a real clone, whose `HEAD` the test moves and whose work tree the test changes), a `Makefile` in the dataset's checkout (prepared by the test as the base: it has `sync`, `check`, `lint`, `slow` targets that print lines and write marker files), and the real `make`. `tests/adapters/test_make_commands.py` and `test_make_commands_user.py` are unchanged.

## Acceptance criteria

1. `run("check", time_limit=timedelta(minutes=1))` on a dataset whose base holds a `Makefile` with `sync` (echoes `sync: green (0.1 s)`) and `check` (echoes `checked` and `check: green (0.2 s)`): the result is `passed` with `exit_status` 0, `last_line` `check: green (0.2 s)`, `targets` `[TargetTime(target="sync", seconds=0.1), TargetTime(target="check", seconds=0.2)]`, and the fake's one call has the command `["/bin/sh", "-c", '"$1" sync && "$1" --no-print-directory "$2"', "factory-check", "make", "check"]`, no mounts, the environment `{"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/work/home"}`, the time limit 1 minute and the working directory `/work/checkout`; the marker file `check` writes is in the dataset's checkout and not in the host's checkout, whose `git.status()` is the same before and after the run. A `check` that prints the 40 lines `line 1` to `line 40` gives an `output_tail` of exactly the 30 lines `line 11` to `line 40`.
2. The reset and the copy (rows of one parametrized test): a file the test wrote into the dataset's checkout after the base (`stray.txt`) is gone when `check` runs (the `check` recipe lists the folder into its output, and `stray.txt` is not in it); a file the host's work tree holds beyond `HEAD` (`src/new.py` untracked, and `src/kept.py` changed; the base holds `src/kept.py` with `HEAD`'s bytes) is in the dataset's checkout when `check` runs, with the host's bytes; a file deleted on the host (`src/old.py` removed, still in `HEAD` and in the base) is not in the dataset when `check` runs; a host file the host's `.gitignore` ignores (`.venv/x`) is not copied; with the host's work tree equal to `HEAD`, nothing is copied and the dataset holds the base's files only.
3. `sync` failing: a `Makefile` whose `sync` exits 1 printing `boom` gives `failed` with `exit_status` 2 (make's own status for a failed recipe, as `tests/adapters/test_make_commands.py` pins it) and `last_line` `boom` (make's `make: *** ... Error 1` line after it is skipped), and `check`'s recipe did not run (its marker file is absent).
4. The time limit: a `Makefile` whose `check` sleeps 30 seconds under `time_limit` 1 second gives `status` `time_limit`, `exit_status` `None`, after at least 1 and less than 25 seconds.
5. Before anything runs (rows of one parametrized test): `time_limit` 0 and `time_limit` minus 1 second each raise `ValueError`; the command `Check` raises `ProjectCommandError` with `detail` `invalid command name 'Check'`; in both rows the fake recorded no call and the dataset was not reset (a `stray.txt` written after the base is still there).
6. Faults (rows of one parametrized test): a `FakeSnapshots` without a base makes `run("check", ...)` raise `ProjectCommandError` whose `command` is `check` and whose `detail` starts with `snapshot command reset failed:`; a `ContainerRuns` of the test (a small class inheriting the interface) whose `run` raises `ContainerError("make", "[Errno 2] No such file or directory")` makes it raise `ProjectCommandError` with `detail` `container command make failed: [Errno 2] No such file or directory`; a `GitCli` of the test (a subclass of the `checkout` fixture's class) whose `changed_paths` raises `GitError("git diff", 128, "bad revision")` makes it raise that `GitError` itself, not a `ProjectCommandError`; one whose `changed_paths` returns `[ChangedPath(path="../x", change="added")]` makes it raise `ValueError`; in these two rows the fake recorded no call.
7. `ContainerMakeCommands` is an instance of `ProjectCommands`, and `make` appears as a string literal in `factory.adapters.make_commands` and `factory.application.preflight` only (`tests/test_make_search.py`, unchanged).
8. `make check` stays green.
9. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*: `ContainerMakeCommands` beside `MakeProjectCommands`, its steps (the reset, the copy of what differs from `HEAD`, the check container, the reading shared with the first implementation), its environment, its faults as `ProjectCommandError`, and that a check's files stay in the container; `docs/project-guide/stage-environment.md` gains the section *The checks* (step 7 of the cycle, pointing to `processes-and-checks.md`, and decision 7: why what differs from `HEAD` is copied and no list is kept). `docs/decisions.md`: none.

## Smoke test

```bash
uv run pytest tests/adapters/test_make_commands_container.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
uv run python - <<'EOF'
from factory.adapters.make_commands import CHECK_ENVIRONMENT, ContainerMakeCommands
from factory.application.project_commands import ProjectCommands

print(CHECK_ENVIRONMENT, issubclass(ContainerMakeCommands, ProjectCommands))
EOF
```
Expect: `{'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} True`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. factory: crash 1: the run of stage intake ended without a result. Its work is discarded back to commit 7ce230d8035ee0a60356a2aa5c50161e4b91e3d7.
