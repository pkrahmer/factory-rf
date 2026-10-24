---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 418
comments_read: [6388655761]
handed_over: approval
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T19:35:49.622469Z'
  stage: intake
- number: 5
  speaker: intake
  kind: question
  at: '2026-10-24T19:36:08.915704Z'
  stage: intake
  run: 24d7204107f244b69644850876ed6e9d
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-24T19:38:29.772036Z'
  stage: intake
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T19:38:48.719276Z'
  stage: intake
- number: 8
  speaker: intake
  kind: result
  at: '2026-10-24T19:39:04.533920Z'
  stage: intake
  run: fed9f2e9b5b94e998180e5c1dec17e0c
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T19:39:24.817213Z'
  stage: tests
- number: 10
  speaker: tester
  kind: result
  at: '2026-10-24T19:44:16.998358Z'
  stage: tests
  run: 55c412574715431da102ebec770f6285
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T19:44:38.737624Z'
  stage: doing
- number: 12
  speaker: coder
  kind: result
  at: '2026-10-24T19:48:35.963725Z'
  stage: doing
  run: 9a4b17aba44746a7b43571307738335a
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T19:48:57.600260Z'
  stage: review
- number: 14
  speaker: reviewer
  kind: result
  at: '2026-10-24T19:50:22.256803Z'
  stage: review
  run: f1d8f1aa858c4049adcde09a38c768b5
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T19:50:42.718164Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-10-24T19:52:34.851254Z'
  stage: doing
  run: 5dc51a8659a241cab6cb268a4db4c081
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-24T19:52:55.269748Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-10-24T19:55:43.247958Z'
  stage: tests
  run: 916165c913ec4a8ba3bfd216323badd3
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T19:56:04.866469Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-10-24T19:58:57.232253Z'
  stage: doing
  run: 70a1943facb24333b472cefafd5d3dab
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-24T19:59:18.160401Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-10-24T20:00:11.969373Z'
  stage: review
  run: d9205f381b2e49ef89172234d26cce3d
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-24T20:00:33.245289Z'
  stage: docs
- number: 24
  speaker: documenter
  kind: result
  at: '2026-10-24T20:01:14.667225Z'
  stage: docs
  run: 60c15c9ef7d6489eab0abb64f412c847
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-24T20:01:35.453466Z'
  stage: smoke-test
- number: 26
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T20:02:04.211509Z'
  stage: smoke-test
  run: 04b311ebf4134b6ca01c1cebabc896e9
---

# The project commands run in a check container on the taken result

## Description

Step 7 of the cycle (`planning/v1.2-plan.md`, "The cycle of a stage"): the checks see the taken result on a clean base. The dataset is rolled back to the base, the files the take brought into the host's work tree are copied in, and a container runs `make sync && make <command>` with `--timeout` as the command's time limit; a file a check makes stays in its container. This story adds `ContainerMakeCommands`, the second make-based implementation of `ProjectCommands`, beside `MakeProjectCommands` in `factory.adapters.make_commands`, which reads a command's output exactly as the first does. What to copy in is what differs from `HEAD` on the host (`git.changed_paths("HEAD")`: after the take, the taken files, the restored work item and the factory's cost record; at the preflight's `lint` on `main`, nothing), mirrored with `copy_changed` of S0004 (decision 7 of `feature.md`); so nothing is remembered between the take and the checks. `KnownResults` and `RecordingProjectCommands` are unchanged: the wiring (S0010) puts the class behind them for a `container` instance. The suite runs it on `FakeSnapshots` and `FakeContainerRuns` with a real `make` as the child process. What stays: `MakeProjectCommands` and `SealedProjectCommands`, the inline instance's commands, unchanged in behaviour; `MakeProjectCommands` shares the refusal of a bad call and the reading of the output with the new class.

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
8. The dataset's own `.git` is never touched (rows of one parametrized test): after a run with a host work tree that differs from `HEAD`, a marker file the test placed in the dataset's `checkout/.git` is intact and no host `.git` path was copied in; nothing is written outside `<mount_point>/checkout` (the files of the dataset's folder beside `checkout` are the same before and after the copy, apart from what the container itself writes).
9. `make check` stays green.
10. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*: `ContainerMakeCommands` beside `MakeProjectCommands`, its steps (the reset, the copy of what differs from `HEAD`, the check container, the reading shared with the first implementation), its environment, its faults as `ProjectCommandError`, and that a check's files stay in the container; `docs/project-guide/stage-environment.md` gains the section *The checks* (step 7 of the cycle, pointing to `processes-and-checks.md`, and decision 7: why what differs from `HEAD` is copied and no list is kept). `docs/decisions.md`: none.

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
4. factory: started intake as self.
5. intake: Format check passed. One finding from my own checks:

   1. The Interface states a rule, "The dataset's own `.git` is never touched: `changed_paths` never lists a `.git` path, and `copy_changed` writes under `<mount_point>/checkout` only", and no acceptance criterion tests it. Two coders could read it two ways and both would pass the tests. Options:
      (a) Add a criterion before the two closing ones. It would say: after a run with a host work tree that differs from `HEAD`, the dataset's checkout `.git` folder is byte-for-byte what it was before the run (a marker file the test placed in it is intact, and no host `.git` path was copied in). A second row would say that nothing is written outside `<mount_point>/checkout`.
      (b) Drop the sentence from the Interface, since `changed_paths` and `copy_changed` are S0004's and are tested there.
      I would choose (a), with the marker file in the dataset's `.git` checked after the run.

   Everything else checked out:
   - Interface: it names the module, the constant and the class signature, the call order, the exact container command and the error mappings.
   - Criteria: criteria 1 to 6 cover the passing side, the `sync` failure, the time limit, the pre-run refusals, the faults and the 30-line tail. They are otherwise testable by one function each, with the failing sides present.
   - Smoke test: the commands are runnable. `pyproject.toml` sets `-q` in `addopts` and the command passes none, so the `N passed in` line exists. The `Expect:` lines can be checked.
   - Architecture: it sits in `factory.adapters` behind the `ProjectCommands` interface, and `make` is allowed there.
   - Scope: it is within S0009 of `feature.md` and decisions 7 and 8, and touches no out-of-scope item.
6. 2026-10-24 human: Answer to the intake (F0042-S0009, the project commands run in a check container on the taken result): **(a)**. Add a criterion before the two closing ones, with two rows: (1) after a run with a host work tree that differs from `HEAD`, a marker file the test placed in the dataset's `checkout/.git` is intact and no host `.git` path was copied in; (2) nothing is written outside `<mount_point>/checkout`. The Interface's sentence stays. Please write it into the criteria as you accept.
7. factory: started intake as self.
8. intake: accepted

   Carried in from journal entry 6 (the human's answer (a) to my question 1): I added a criterion before the two closing ones. It is now criterion 8, with two rows. Row 1: after a run with a host work tree that differs from `HEAD`, a marker file the test placed in the dataset's `checkout/.git` is intact and no host `.git` path was copied in. Row 2: nothing is written outside `<mount_point>/checkout`. `make check` is now criterion 9 and `docs:` is criterion 10. The Interface sentence stays as it was. I wrote the parenthesis in row 2 ("the files of the dataset's folder beside `checkout` are the same before and after the copy, apart from what the container itself writes") to make the row testable. It is my wording of the human's row.

   - Interface: it names the module, `CHECK_ENVIRONMENT` and the `ContainerMakeCommands` signature. It gives the order of the checks and calls, the exact container command, and the `SnapshotError`/`ContainerError` mapping to `ProjectCommandError`. It also says that `GitError` and `ValueError` propagate.
   - Criteria: criteria 1 to 8 are each testable by one test function. Every rule has its failing side: the `time_limit` and command-name refusals (5), the faults (6), the `sync` failure (3), the time limit (4) and the `.git` rule (8). The 30-line tail is in 1. The reset, copy, deletion and ignored-path cases are rows in 2.
   - Smoke test: both commands are runnable. `pyproject.toml` sets `-q`, and the command passes none, so the `N passed in` line exists. Both `Expect:` lines can be checked against the output.
   - Architecture: the class sits in `factory.adapters` behind the `ProjectCommands` interface. It reuses `copy_changed`, `last_line` and `status_of`, and the word `make` stays in the allowed modules.
   - Scope: it is within S0009 of `feature.md` and decisions 7 and 8. It touches nothing under "Out of scope".
9. factory: started tests as self.
10. tester: Wrote the tests for `ContainerMakeCommands`. They use `FakeSnapshots` and `FakeContainerRuns` on `tmp_path`, the `checkout` fixture as the host clone, and the real `make`. The fixture `setup` commits `.gitignore` (`.venv/`), `src/kept.py` and `src/old.py` on the host. For each test it then builds the base: the host's files plus that test's own `Makefile`, a marker in `checkout/.git`, and `home/kept.txt` beside `checkout`.

    Criterion → test:
    - criterion 1: tests/adapters/test_make_commands_container.py::test_check_runs_after_sync_in_the_container_and_its_files_stay_there. The 40-line tail part is in ::test_output_tail_is_the_last_thirty_lines.
    - criterion 2: tests/adapters/test_make_commands_container.py::test_check_sees_the_base_with_what_differs_from_head_on_the_host. Rows: stray file reset, added and changed copied with the host's bytes, deleted removed, ignored `.venv/x` not copied, nothing changed. The `check` recipe lists the checkout's files outside `.git`, and the test compares that listing exactly.
    - criterion 3: tests/adapters/test_make_commands_container.py::test_failing_sync_fails_and_check_does_not_run
    - criterion 4: tests/adapters/test_make_commands_container.py::test_check_reaching_its_time_limit_is_a_time_limit_result. The limit is 1 s and the bound is 1 ≤ elapsed < 25. The child need not start to be killed, so the short limit stays.
    - criterion 5: tests/adapters/test_make_commands_container.py::test_refused_call_runs_nothing. Rows: limit 0, limit −1 s, and the name `Check`. The positive side of the limit is the 1-minute and 1-second runs in criteria 1 and 4.
    - criterion 6: tests/adapters/test_make_commands_container.py::test_faults_are_project_command_errors_but_git_and_paths_propagate. Rows: no base, a container that cannot start (a small `ContainerRuns` subclass), a `GitCli` subclass whose `changed_paths` raises (the test checks it gets that same `GitError` object back), and one that returns `../x`. The last two rows also check that no container call was recorded.
    - criterion 7: tests/adapters/test_make_commands_container.py::test_container_commands_are_project_commands. The search for the word `make` is the existing, unchanged tests/test_make_search.py::test_only_the_make_class_names_make.
    - criterion 8: tests/adapters/test_make_commands_container.py::test_copy_writes_under_the_dataset_checkout_and_never_its_git. Rows: the files under the dataset's `checkout/.git` equal the base's, and the files beside `checkout` equal the base's, both after a run with host changes.
    - criteria 9 and 10: no test; they are `make check` and the docs.

    Files created: tests/adapters/test_make_commands_container.py. No earlier test file changed.

    Module the test run could not import: `make test` ends in a collection error, an `ImportError` on tests/adapters/test_make_commands_container.py, because `ContainerMakeCommands` does not exist yet in `factory.adapters.make_commands`. `make lint` is green. The fake classes mark their unused arguments with `del`, to satisfy ruff's ARG002 rule.

    `lint`: lint: green (0.6 s)
    `test`: ERROR tests/adapters/test_make_commands_container.py - ImportError while importing test module '/work/checkout/tests/adapters/test_make_commands_container.py'.
11. factory: started doing as self.
12. coder: Built `ContainerMakeCommands` and `CHECK_ENVIRONMENT` in src/factory/adapters/make_commands.py, beside `MakeProjectCommands`. It is the only file I changed. Every test in tests/adapters/test_make_commands_container.py passes, and so do the unchanged tests/adapters/test_make_commands.py and tests/test_make_search.py. `make check` is green: `test: green (66.0 s)`, `check: green`, total coverage 99.20 %. The second smoke command prints `{'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} True`.

    `run` works in the order the Interface gives:
    - It refuses a bad call before anything runs, through `_check_call`. This is the time-limit and command-name refusal that used to sit inline in `MakeProjectCommands.run`; both classes now call it.
    - It runs `snapshots.reset()`. A `SnapshotError` becomes `ProjectCommandError(command, str(exc))`.
    - It calls `copy_changed(checkout, mount_point / "checkout", git.changed_paths("HEAD"))`, reused from `factory.application.take`. `GitError` and `ValueError` pass through as they are.
    - It calls `containers.run` with `/bin/sh -c '"$1" sync && "$1" --no-print-directory "$2"' factory-check make <command>`, no mounts, `CHECK_ENVIRONMENT`, the time limit and `/work/checkout`. A `ContainerError` becomes `ProjectCommandError(command, str(exc))`.
    - It reads the result into a `CheckResult`.

    Main choice: both classes read their output through one function. I split the old `_check_result` into a thin adapter over a new `_read_result(command, exit_status, output, duration)`. `MakeProjectCommands` passes in a `ProcessResult` and the new class a `ContainerResult`. Both get the same `status_of`, `last_line`, `_tail` and `target_times`. Alternative rejected: turning the `ContainerResult` into a `ProcessResult` and calling `_check_result` with it. That would build a fake process record just to reach the reader.

    Refactor pass: I read the diff and found nothing to change.

    Noticed but did not touch:
    - `CHECK_ENVIRONMENT` has the same value as `SYNC_ENVIRONMENT` in `factory.application.stage_environment`. The Interface names it as a separate constant in this module, so I kept it separate rather than importing that one.
    - `SHELL_EXECUTABLE` is imported from `factory.adapters.agent_launch`, its only definition.
    - The `make` literal appears twice in this module: the existing `executable` default and the container command. `tests/test_make_search.py` allows both.

    I did not rewrite `## Description`: the journal changed nothing in the task's meaning that the intake had not already written in as criterion 8.

    `check`: check: green
    `duplicates`: duplicates: 16 new, 36 known, 2 gone
13. factory: started review as self.
14. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: src/factory/adapters/make_commands.py and tests/adapters/test_make_commands_container.py. Group 1 passes. Every criterion from 1 to 8 has a test that checks what the criterion says. The Interface's refusals (a limit of 0 and of -1 s, the name `Check`) and its faults (snapshot, container, `GitError`, `../x`) are rows of parametrized tests. The positive side of the limit is covered by the 1-minute and 1-second runs. The coder's journal (entry 12) reports `check: green`. Groups 2 and 3 pass: the layers hold, `copy_changed` is reused from the application layer, the command name goes in as a shell argument and never into the script, and the diff adds no silencing markers. `make duplicates` finds one new item from this diff, the unused class `ContainerMakeCommands`. That is expected, because S0010 wires it. Group 4 fails on copies of existing constants:

    1. src/factory/adapters/make_commands.py:46: `_DATASET_CHECKOUT = "checkout"` is a second copy of `_MOUNTED_CHECKOUT` in src/factory/application/take.py:17. That is the folder name of the dataset's checkout, and if only one copy changes, the take and the checks would use different folders. Fix: make that one constant public (in `factory.application.take`, or beside `WORK_CHECKOUT` in `factory.domain.containers`) and import it in both modules.
    2. src/factory/adapters/make_commands.py:41: `CHECK_ENVIRONMENT` repeats the value of `SYNC_ENVIRONMENT` in src/factory/application/stage_environment.py:25 literally, including the PATH string. Fix: keep the name the Interface gives, but derive the value from the existing constant (`CHECK_ENVIRONMENT = dict(SYNC_ENVIRONMENT)`) or from one shared system-PATH constant, so the value is written once.
    3. tests/adapters/test_make_commands_container.py:84 (`setup` fixture): `tmp_path / "checkout"` hard-codes the name the `checkout` fixture clones into. Fix: use `CHECKOUT` from `git_support`, as tests/adapters/test_claude_runtime_environment.py does.

    description corrected: "`MakeProjectCommands` and `SealedProjectCommands` ... untouched" -> "unchanged in behaviour; `MakeProjectCommands` shares the refusal of a bad call and the reading of the output with the new class". The Interface requires the shared reader ("read by the same code", "shared, not copied"), and the diff splits `_check_call` and `_read_result` out of `MakeProjectCommands`.

    Earlier tests: none. The diff only adds tests/adapters/test_make_commands_container.py (status `A`).
15. factory: started doing as self.
16. coder: Round 1. I worked through the reviewer's findings in entry 14. I fixed two of them in the code. The third is a change to a test, so I'm passing it to the tester.

    1. Fixed. The dataset checkout's folder name now exists once. I renamed `_MOUNTED_CHECKOUT` in src/factory/application/take.py to the public `MOUNTED_CHECKOUT`, and src/factory/adapters/make_commands.py imports it. Its own copy, `_DATASET_CHECKOUT`, is removed. I picked `take.py` over a new constant beside `WORK_CHECKOUT` in `factory.domain.containers` because the take already owns the name, and moving it would have touched more files for the same result.
    2. Fixed. `CHECK_ENVIRONMENT` keeps the name the Interface gives, but its value now comes from the existing constant: `CHECK_ENVIRONMENT = dict(SYNC_ENVIRONMENT)`, imported from `factory.application.stage_environment`. The `WORK_HOME` import in make_commands.py was no longer used, so I dropped it. The value is unchanged: `{'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'}`.
    3. For the tester: in tests/adapters/test_make_commands_container.py, the `setup` fixture (line 84) should use `CHECKOUT` from `git_support` in place of the literal `tmp_path / "checkout"`, as tests/adapters/test_claude_runtime_environment.py does. I did not touch the test.

    Refactor pass: I read the diff again and found nothing more to change. `make check` is green (`test: green (68.9 s)`, `check: green`, coverage 99.20 %).

    Description: unchanged by me. The reviewer had already corrected it in entry 14.
17. factory: started tests as self.
18. tester: Round 1. I made the one test change the coder's entry 16 names, from the reviewer's finding 3 in entry 14. It is a change to my own test file from this story.

    In tests/adapters/test_make_commands_container.py, the `setup` fixture now builds the host's directory as `tmp_path / CHECKOUT`, using the constant imported from `git_support`, instead of the literal `tmp_path / "checkout"`. This matches what tests/adapters/test_claude_runtime_environment.py does. If the `checkout` fixture ever clones into a different folder, the test now follows it instead of pointing at a stale path. I changed nothing else: no test was renamed and every test checks the same thing.

    The criterion → test mapping is the same as in entry 10:
    - criterion 1: tests/adapters/test_make_commands_container.py::test_check_runs_after_sync_in_the_container_and_its_files_stay_there and ::test_output_tail_is_the_last_thirty_lines
    - criterion 2: ::test_check_sees_the_base_with_what_differs_from_head_on_the_host
    - criterion 3: ::test_failing_sync_fails_and_check_does_not_run
    - criterion 4: ::test_check_reaching_its_time_limit_is_a_time_limit_result
    - criterion 5: ::test_refused_call_runs_nothing
    - criterion 6: ::test_faults_are_project_command_errors_but_git_and_paths_propagate
    - criterion 7: ::test_container_commands_are_project_commands, plus the existing, unchanged tests/test_make_search.py::test_only_the_make_class_names_make
    - criterion 8: ::test_copy_writes_under_the_dataset_checkout_and_never_its_git
    - criteria 9 and 10: no test; they are `make check` and the docs.

    Files: I created none in this round and changed only tests/adapters/test_make_commands_container.py. I changed no earlier test file. Every module imports; nothing failed to import.

    `make test`: test: green (69.4 s), total coverage 99.20 %. `make lint`: lint: green (0.2 s).

    `lint`: lint: green (0.6 s)
    `test`: test: green (67.4 s)
19. factory: started doing as self.
20. coder: Round 1, after the tester's change. I changed no code in this run. The reviewer's entry 14 had three findings, and all three are now done:
    - Finding 1: `MOUNTED_CHECKOUT` is made public in src/factory/application/take.py, and src/factory/adapters/make_commands.py imports it (entry 16).
    - Finding 2: `CHECK_ENVIRONMENT = dict(SYNC_ENVIRONMENT)` in src/factory/adapters/make_commands.py (entry 16).
    - Finding 3: the tester's `setup` fixture now uses `tmp_path / CHECKOUT` from `git_support` (entry 18).

    What I built across the story: `ContainerMakeCommands` and `CHECK_ENVIRONMENT` in src/factory/adapters/make_commands.py, plus the public `MOUNTED_CHECKOUT` in src/factory/application/take.py.

    Main choice: `MakeProjectCommands` and the new class share two functions, `_check_call` (refuses a bad call) and `_read_result` (reads the output). I rejected building a fake `ProcessResult` out of a `ContainerResult` just to reuse the old reader.

    Refactor pass: there was nothing new to read, because the working tree holds no code change from this run. The only modified file is the factory's own costs sidecar.

    `make check` is green on the committed state: `test: green (69.3 s)`, coverage 99.20 %, `check: green`.

    Noticed but did not touch: `make duplicates` still reports `ContainerMakeCommands` as unused. That is expected until the wiring story puts it in use.

    Description: unchanged. The reviewer already corrected it in entry 14.

    `check`: check: green
    `duplicates`: duplicates: 16 new, 36 known, 2 gone
21. factory: started review as self.
22. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`. The diff covers src/factory/adapters/make_commands.py, src/factory/application/take.py and tests/adapters/test_make_commands_container.py.

    no findings

    - Round 0's findings (entry 14) are all fixed. Finding 1: `MOUNTED_CHECKOUT` is now public in src/factory/application/take.py:17 and imported in make_commands.py:27, and no copy of `_MOUNTED_CHECKOUT` is left anywhere in src or tests. Finding 2: `CHECK_ENVIRONMENT = dict(SYNC_ENVIRONMENT)` (make_commands.py:43), with the value unchanged. Finding 3: the `setup` fixture now uses `tmp_path / CHECKOUT`.
    - Group 1 (acceptance criteria): passes.
      - Criteria 1 to 8 each have a test that checks what the criterion says, and I checked them against the criteria myself.
      - Criterion 1: the container call is checked field by field, plus the marker file in the dataset and not on the host, the host's `git.status()`, and the 30-line tail.
      - Criterion 2: five rows, each comparing the dataset's file listing exactly and the host's bytes.
      - Criterion 3: exit status 2, `last_line` `boom`, and no marker.
      - Criterion 4: `time_limit` with exit status None, bounded 1 ≤ elapsed < 25.
      - Criterion 5: rows for a limit of 0, a limit of -1 s and the name `Check`, each with no call and the stray file still there. The positive side of the limit is covered by the 1 min and 1 s runs.
      - Criterion 6: rows for the snapshot fault, the container fault, the same `GitError` object propagating, and `ValueError` for `../x`, with no call in the last two.
      - Criterion 7: `isinstance`, plus the unchanged test_make_search.py.
      - Criterion 8: the files under the dataset's `checkout/.git`, and the files beside `checkout`, are each compared with the base.
      - Every Interface rule has its refused side tested. The factory's `make check` after the coder was green (entry 20: `check: green`).
    - Group 2 (architecture): passes. adapters → application imports are allowed. The containers are reached only through `ContainerRuns`, and `make` stays in the make wrapper.
    - Group 3 (security): passes. The command name goes in as a shell argument (`"$1"`/`"$2"`), never into the script text, and it is checked against `COMMAND_NAME_PATTERN` first. The diff adds no markers that silence a check.
    - Group 4 (quality): passes. The refusal and the reading of the output are shared through `_check_call` and `_read_result`, not copied. I ran `make duplicates` (`16 new, 36 known, 2 gone`). The only new item from this diff is the unused class `ContainerMakeCommands` (make_commands.py:185), which is expected until S0010 wires it. The other new items are in modules this diff does not touch.
    - Group 5 (work item hygiene): passes. The journal explains the shared reader and the alternative it rejected. The Description (corrected in round 0) matches the code. The docs criterion still says what the reader needs.

    Earlier tests: none. The diff only adds tests/adapters/test_make_commands_container.py (status `A`).
23. factory: started docs as self.
24. documenter: Docs round 1. Only documents changed, so I did not run `make check`; the factory's checks follow.

    Files changed:
    - docs/project-guide/processes-and-checks.md: new subsection *Container project commands*, before *Rules of `run`*. It covers `ContainerMakeCommands` and `CHECK_ENVIRONMENT`, the steps (the shared refusal of a bad call, the reset, the copy of what differs from `HEAD`, the check container, the shared reading of the output), the faults, and that a check's files stay in the container. The opening paragraph of *Project commands* now names it as the second implementation.
    - docs/project-guide/stage-environment.md: new section *The checks* (step 7 of the cycle, a pointer to the subsection above, and why what differs from `HEAD` is copied and no list is kept). The sentence in *copy_changed* that said the check container's copy "will" use it now says it does.

    The wording on decision 7 is mine. I did not read `feature.md`, which my instructions exclude. I stated only the reasoning the story itself gives: `HEAD` and the host's work tree already say what the take brought, so nothing is remembered between the take and the checks. If the feature's own reasoning differs, the human should correct that sentence.

    Cross-read against the diff and found current:
    - the rest of processes-and-checks.md (*Rules of `run`*, *Known results*, *Sealed project commands*);
    - the *take* and *container environment* sections of stage-environment.md;
    - agents.md, watching.md and decisions.md, where I checked only the `MakeProjectCommands` mentions.

    `docs/decisions.md` is unchanged, as the docs criterion says. I did not run the examples, because I wrote none. I took the command line and the environment from the source and the Interface.

    Stale text I saw and left alone:
    - The README sentence that "This repository's own `Makefile` and `factory/pipeline.yml` do not have [sync] yet" is the human's change.
    - The `make duplicates` report still lists `ContainerMakeCommands` as unused; that is expected until S0010 wires it.

    Code findings: none. The code matches the Interface and the criteria.

    `check`: check: green (not run again: passed on tree 75a4af8630b7 at 2026-10-24T19:57:40Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
25. factory: started smoke-test as self.
26. smoke-tester: Smoke test, round 1. I ran both commands under `## Smoke test` exactly as written, from the repository root and in order. I changed nothing.

    **Command 1:** `uv run pytest tests/adapters/test_make_commands_container.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`
    ```
    1
    ```
    Met `Expect: 1`. For context, I ran pytest a second time without the grep. Its last lines were:
    ```
    ...................                                                      [100%]
    19 passed in 1.57s
    ```

    **Command 2:** the `uv run python -` heredoc that imports `CHECK_ENVIRONMENT` and `ContainerMakeCommands` and checks the class against `ProjectCommands`
    ```
    Bytecode compiled 4164 files in 92ms
    {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} True
    ```
    Met `Expect: {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} True`. The line before it is uv's own bytecode-compile notice, not output of the script. The process exited with 0.

    **Against the acceptance criteria:**
    - Command 2 matches the environment given in criterion 1 and the `ProjectCommands` instance check in criterion 7.
    - Command 1 shows that the container suite passes. That suite is the one criteria 1 to 8 are written against.
    - Nothing either command showed contradicts any criterion.
    - Criterion 9 (`make check`) and criterion 10 (docs) are not covered by the smoke test, and I did not run or judge them here. The factory gates `make check`, and the docs stage covers criterion 10.

    **Findings:** none.

    **Open:** nothing.
