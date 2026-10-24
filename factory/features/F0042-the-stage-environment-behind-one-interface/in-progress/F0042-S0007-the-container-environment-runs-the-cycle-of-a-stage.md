---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 415
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T17:30:00.066936Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T17:30:00.072545Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-24T17:30:25.555659Z'
  stage: intake
  run: cceae78738854d1989a0d139d5b73505
  blocked: question
---

# The container environment runs the cycle of a stage

## Description

This story builds the second implementation of `StageEnvironment` (S0005), the one v1.2 is for: `ContainerEnvironment` runs steps 2 to 4 and 6 of the cycle (`planning/v1.2-plan.md`, "The cycle of a stage") on the `Snapshots` and `ContainerRuns` interfaces of S0001. `prepare` rolls the dataset back to its base, runs the sync container (the host repository's `.git` mounted read-only at `/upstream`, the agent files mounted read-only at `/etc/factory/claude`: `git init` when `/work/checkout` has no `.git`, a fetch of every branch, the checkout of the branch reset to the stage-start commit, the agent files copied into `/work/home/.claude`, then `make sync`) and moves the base forward. `run_agent` runs the request through the boundaries' runtime, which S0008 starts in a container; there is no seal and no nested-repository search, because the dataset is rolled back. `take` is the `TakeService` of S0004 on `snapshots.changed_paths()`. One line per stage goes into the factory log, `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`, so the human can read the plan's measures from `/state/factory.log`. `Boundaries` gains `snapshots` and `containers`, and `stage_environment_of(boundaries)` returns the container environment when both are set. The suite runs it on `FakeSnapshots` and `FakeContainerRuns`, with real `git` and `make` as child processes on the host; the real tools come with S0010's wiring and F0043's VM. Step 5 (the agent's own container) is S0008's, step 7 (the checks) S0009's. What stays: `InlineEnvironment` and every stage of `self`, which has no snapshots and no containers in its boundaries until S0010 reads the setting.

## Interface

`factory.application.boundaries` (`application`): `Boundaries` gains two keyword fields with defaults, after `agent_home`:

```python
    snapshots: Snapshots | None = None
    containers: ContainerRuns | None = None
```

- `None` means the inline environment; the fixture `boundaries` of `tests/conftest.py` is unchanged.

`factory.application.stage_environment` (`application`):

```python
UPSTREAM = "/upstream"
AGENT_FILES = "/etc/factory/claude"
SYNC_ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": WORK_HOME}
TIMING_LINE = "stage environment: reset {reset} s, sync {sync} s, advance {advance} s, take {take} s"


class ContainerEnvironment(StageEnvironment):
    """v1.2's way: the agent on the dataset in throwaway containers; the take after."""

    def __init__(self, boundaries: Boundaries, snapshots: Snapshots, containers: ContainerRuns) -> None: ...


def stage_environment_of(boundaries: Boundaries) -> StageEnvironment:
    """The container environment when snapshots and containers are set, else the inline one."""
```

- `stage_environment_of`: both `boundaries.snapshots` and `boundaries.containers` set gives `ContainerEnvironment(boundaries, snapshots, containers)`; one or both `None` gives `InlineEnvironment(boundaries)`.
- `prepare(commit, branch, *, sync_time_limit)`, in this order, each step timed with `boundaries.clock`:
  1. `snapshots.reset()`.
  2. The sync container: `containers.run([SHELL, "-c", <the sync script>, "factory-sync", WORK_CHECKOUT, WORK_HOME, UPSTREAM, AGENT_FILES, branch, commit], mounts=[Mount(source=boundaries.checkout / ".git", target=UPSTREAM, read_only=True), Mount(source=boundaries.settings.agent_home, target=AGENT_FILES, read_only=True)], environment=SYNC_ENVIRONMENT, time_limit=sync_time_limit, working_directory=WORK)`, `SHELL` a constant `/bin/sh` of this module (the application layer cannot read `factory.adapters.agent_launch`'s `SHELL_EXECUTABLE`). The script takes every container path as an argument (`$1` to `$4`), the branch as `$5` and the commit as `$6`, and holds no path in its text (decision 5 of `feature.md`), so that `FakeContainerRuns` can map them. It does, stopping at the first failure (`set -eu`): make `$1` and `$2` when missing; replace `$2/.claude` with a copy of `$4`; in `$1`, `git init -q` when there is no `.git`; `git fetch -q --prune --update-head-ok "$3" '+refs/heads/*:refs/heads/*'` (`--update-head-ok` because git refuses to fetch into the checked-out branch, an unborn one included: a fresh `git init` under `init.defaultBranch=main` would otherwise refuse the host's `main`; the checkout and the reset that follow put the work tree right, so `HEAD` is never detached); `git checkout -q -f "$5"`; `git reset -q --hard "$6"`; `make sync`. The exact text is the coder's.
  3. A result with `timed_out` true is `ContainerError("sync", f"no end within {n} s")`, `n` the whole seconds of `sync_time_limit` rounded up; an exit status other than 0 is `ContainerError("sync", <the last non-blank line of the output that is no make message, or `exit status <n>` when there is none>)`. A make message is a line that starts with `make:` or `make[`: a failed `make sync` ends its output with `make: *** [Makefile:3: sync] Error 1`, and the detail must be the recipe's own last line. The rule is the one `MakeProjectCommands` applies to its `last_line`; this story moves it from `factory.adapters.make_commands` (`_last_line`, `_MAKE_MESSAGE_PREFIXES`) into `factory.domain.checks` as the public function `last_line(lines: list[str]) -> str` with `MAKE_MESSAGE_PREFIXES`, used by both and copied by neither; `tests/adapters/test_make_commands*.py` are unchanged. The base does not move after a failed sync.
  4. `snapshots.advance()`.
  The three durations are kept for the timing line. `SnapshotError` from the snapshots propagates as it is.
- `run_agent(request, *, run=None)`: `(run or boundaries.agent_runtime.run)(request)`, returned as `SealedRun(result=<it>, nested_repositories=[])`. No seal, no home reset, no removal of ignored paths: the dataset is rolled back.
- `take(stage_start, work_item_path)`: `TakeService(boundaries, snapshots.mount_point).take(stage_start, work_item_path, snapshots.changed_paths())`, timed; then one line through `boundaries.log.line`: `TIMING_LINE` with each duration in seconds with one decimal (`0.0`, `12.3`), the three of the last `prepare` of this object and the take's. A `take` without a `prepare` before it on the same object writes the line with `reset`, `sync` and `advance` as `0.0`. The report is returned as the service gives it.

Tests (the tester writes them): `tests/application/test_container_environment.py` and `tests/application/test_container_environment_take.py`, on the `boundaries` fixture replaced (`dataclasses.replace`) with `FakeSnapshots(workspace, base)` and `FakeContainerRuns(workspace)` under `tmp_path`, the host checkout of the fixture serving as the host repository (its `.git` is the upstream), a `Makefile` with a `sync` target pushed to `main` by the test (its recipe writes a marker file, so the test sees it ran), and `agent_home` holding one agent file; `tests/application/test_stage_environment_of.py` for the choice. A whole stage through `StageRunner` with the two fakes and `FakeAgentRuntime` pins the timing line (criterion 9). `tests/application/test_stage_run.py` and the inline tests are unchanged, and so is `tests/test_make_search.py`: the module holds no string literal that is exactly `make` (the sync script is one literal with `make sync` inside it), so the leave of decision 18 g of `feature.md` is not used and S0009's criterion 7 (the literal in `make_commands` and `preflight` only) stays true.

## Acceptance criteria

1. `stage_environment_of` (rows of one parametrized test): snapshots and containers both set gives a `ContainerEnvironment`; snapshots only, containers only, and neither give an `InlineEnvironment`.
2. `prepare(<main's commit>, "main", sync_time_limit=timedelta(minutes=5))` on a dataset whose base folder exists and is empty (a `FakeSnapshots` without a base folder is criterion 5's): afterwards `<workspace>/checkout` is a git repository on the branch `main` whose `HEAD` is the commit, with every local branch of the host repository present as a local branch (`git branch` in the dataset lists `main` and the work item's branch the test checked out on the host before), the `Makefile`'s `sync` marker exists under the dataset's checkout, `<workspace>/home/.claude/agents/<role>.md` holds the agent file of `agent_home`, and `snapshots.changed_paths()` is `[]` (the base moved after the sync).
3. The sync container's call, read from `containers.calls`: the command starts with `/bin/sh`, `-c`, holds the words `factory-sync`, `/work/checkout`, `/work/home`, `/upstream`, `/etc/factory/claude`, `main` and the commit in that order after the script, and the script text holds none of `/work`, `/upstream`, `/etc/factory`; the mounts are exactly `[Mount(source=<checkout>/.git, target="/upstream", read_only=True), Mount(source=<agent_home>, target="/etc/factory/claude", read_only=True)]`; the environment is `{"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/work/home"}`; the time limit is 5 minutes; the working directory `/work`.
4. A second `prepare` on the same dataset for another commit and branch (the work item's branch at its stage-start commit, after the first prepared `main`): the dataset's repository is reused (the first prepare's commit is still an object of it, `git cat-file -e <first commit>` succeeds, and `containers.calls` holds exactly two sync calls), `HEAD` is the new commit on the new branch, a branch `gone` the test made on the host before the first prepare and deleted before the second is no longer listed by `git branch` in the dataset (the `--prune`), a file the test wrote into `<workspace>/checkout/` and into `<workspace>/home/` between the two prepares is gone (the reset), a changed agent file in `agent_home` reaches `<workspace>/home/.claude/agents/`, and an agent file `agents/extra.md` that `agent_home` held at the first prepare and lost before the second is gone from `<workspace>/home/.claude/agents/` (the copy replaces the folder, it does not merge).
5. Faults of `prepare` (rows of one parametrized test): a `Makefile` whose `sync` exits 1 printing `boom` raises `ContainerError` with `command` `sync` and `detail` `boom` (make's own `make: *** ... Error 1` line after it is skipped), and `snapshots.changed_paths()` afterwards is not `[]` (the base did not move) while a following `reset()` empties the dataset again; a `sync` that sleeps 30 seconds under `sync_time_limit` 1.5 seconds raises `ContainerError("sync", "no end within 2 s")` (the seconds rounded up) after at least 1 and less than 25 seconds; a `FakeSnapshots` without a base raises `SnapshotError` from `reset` and no container runs (`containers.calls` is empty); a commit that is no commit (`"a" * 40`) raises `ContainerError` whose `command` is `sync` (git's message in `detail`); with a `ContainerRuns` of the test (a small class inheriting the interface) whose `run` returns `ContainerResult(exit_status=3, output="\n", timed_out=False, duration=timedelta(seconds=1))`, `prepare` raises `ContainerError("sync", "exit status 3")`, and with one whose `run` returns `ContainerResult(exit_status=2, output="make: *** [Makefile:3: sync] Error 2\n", timed_out=False, duration=timedelta(seconds=1))` it raises `ContainerError("sync", "exit status 2")` (make messages alone are no detail).
6. `run_agent(request)` with a queued fake run returns `SealedRun(result=<the queued result>, nested_repositories=[])`, makes no git call on the host (its `.git` mode is unchanged: no seal), and with `run=<a recorder>` calls the recorder once and the runtime not at all (rows of one parametrized test); a repository the fake run writes as `notes/.git/HEAD` under the request's working directory is not removed and not listed, and an ignored file the fake run writes (`build/out.txt`, the host's `.gitignore` holding `build/`) is still there afterwards (no removal of ignored paths).
7. `take(start, PATH)` after the dataset's checkout got `src/new.py` (inside the write paths), `docs/guide.md` changed (outside) and `.venv/bin/x` (ignored by the host's `.gitignore`), and the dataset's `home/.claude.json` was written: the host's `src/new.py` holds the dataset's bytes, `docs/guide.md` is unchanged on the host, nothing of `.venv` or `home` reached the host, and the report is `TakeReport(left=["docs/guide.md"], restored_work_item=False)`.
8. The timing line: after `prepare(...)` and `take(...)` on one object, with the manual clock advanced by 0.4, 12.3, 0.1 and 0.25 seconds inside `reset`, the sync container's run, `advance` and `changed_paths` (fakes wrapped by the test to advance the clock), the factory log's last line ends with `stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s` (one decimal, Python's rounding); `take` on a fresh object without `prepare` writes `... reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s`; exactly one such line per stage, none after `prepare` alone (rows of one parametrized test).
9. A whole stage through `StageRunner` on boundaries with the two fakes and a runtime of the test (an `AgentRuntime` like `CommittingRuntime` of `tests/application/test_stage_run.py`) that writes `tests/test_a.py` and `notes.md` into `<workspace>/checkout` and returns a completed run with the decision `doing`, in the stage `tests`, ends with the pushed result commit holding `tests/test_a.py` and not `notes.md`, the entry's paragraph naming `notes.md`, the factory log holding exactly one `stage environment:` line, and the host's work tree clean afterwards. (The agent's own container, which makes the real runtime write there, is S0008's.)
10. `make check` stays green.
11. docs: `docs/project-guide/stage-environment.md` gains the section *The container environment*: the cycle step by step with the container paths and the mounts, the sync script's steps and why every branch is fetched (decision 5), the agent files (decision 6), the faults and what each leaves behind, `run_agent` without a seal, the take on the snapshots' changed paths, the timing line and how to read it against the plan's measures, `Boundaries.snapshots` and `containers`, `stage_environment_of`, the tests and their fakes; `docs/project-guide/watching.md`, *Boundaries*: the two new fields and what `None` means; `docs/operator-guide.md`, *The factory log*: the line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`, one per stage of a `container` instance, and that an `inline` instance writes none. `docs/decisions.md`: none (S0005 wrote the entry).

## Smoke test

```bash
uv run pytest tests/application/test_container_environment.py tests/application/test_container_environment_take.py tests/application/test_stage_environment_of.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
uv run python - <<'EOF'
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import SYNC_ENVIRONMENT, TIMING_LINE, ContainerEnvironment

print(TIMING_LINE.format(reset="0.4", sync="12.3", advance="0.1", take="0.2"))
print(SYNC_ENVIRONMENT, ContainerEnvironment.__mro__[1].__name__)
print(Boundaries.__dataclass_fields__["snapshots"].default, Boundaries.__dataclass_fields__["containers"].default)
EOF
```
Expect: three lines, `stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s`, `{'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} StageEnvironment`, `None None`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface moves make's last-line rule into `factory.domain.checks` as the public `last_line(lines: list[str]) -> str` with `MAKE_MESSAGE_PREFIXES`, "used by both and copied by neither". No criterion tests the function in its new place. Criterion 5 reaches it only through `prepare`, and only for a `make: ***` line. The other sides of the rule have no test: a line starting with `make[` is skipped, blank lines are skipped, and the result is `""` when no line is left. The same goes for "used by both", i.e. that `MakeProjectCommands` imports it and the old `_last_line` and `_MAKE_MESSAGE_PREFIXES` are gone. `tests/adapters/test_make_commands*.py` stay unchanged and so cannot pin the new location. Two coders could read this differently and both pass. Options: (a) add a criterion with a parametrized test of `factory.domain.checks.last_line`. Its rows would be: a `make:` line skipped, a `make[2]:` line skipped, a trailing blank line skipped, the recipe's last line returned, and `""` for make messages alone or no lines. A second criterion would check that `factory.adapters.make_commands` no longer defines `_last_line` or `_MAKE_MESSAGE_PREFIXES`. (b) State that the move is not tested directly. I would choose (a).

   2. `run_agent` says "no home reset", but no criterion pins that side. Criterion 6 covers no seal, no ignored-path removal and no nested-repository search, and says nothing about the agent home. Should criterion 6 gain a row showing that a file the fake run writes into the host's `agent_home` is left alone? I would add it.

   Everything else I checked is fine. The Interface is concrete. Criteria 1 to 9 are each testable. The smoke test commands are runnable, and the pytest command correctly passes no `-q` because `addopts` already sets it. The architecture fits: the application layer holds `ContainerEnvironment` and the domain holds `last_line`. The scope is inside the feature's S0007 entry.
