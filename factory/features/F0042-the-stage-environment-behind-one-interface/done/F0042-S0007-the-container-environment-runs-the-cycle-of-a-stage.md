---
stage: done
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 415
comments_read: [6387344840]
handed_over: approval
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-24T17:32:46.344793Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-24T17:33:04.281020Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-24T17:33:27.916072Z'
  stage: intake
  run: 2533ea2b6a634cc3af93bef9a10c7590
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T17:33:48.316182Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T17:40:53.044119Z'
  stage: tests
  run: ed791de863834dc98520aaa123c6058a
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T17:41:14.579408Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T17:51:08.719413Z'
  stage: doing
  run: e5e0aa19908f49e2b0bc5d99ba406130
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T17:51:30.808318Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T17:52:58.830648Z'
  stage: review
  run: f1c5ed444ab14fe8ae5b6012e590b28b
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T17:53:19.446283Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T17:53:50.985374Z'
  stage: doing
  run: 21a81ace73834f579e3cf21d98cf8ff9
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T17:54:11.865297Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-24T17:57:15.729183Z'
  stage: tests
  run: 1b3535e5354b4499a9ec45ae85dba96d
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-24T17:57:36.646135Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-24T18:00:38.302438Z'
  stage: doing
  run: e1600c0606d14d59bc8217ca9eb215c8
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T18:00:59.273832Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-24T18:03:06.635018Z'
  stage: review
  run: b9e2cd083eff47deb8c5e8ec54d06997
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-24T18:03:27.079476Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-24T18:03:49.511987Z'
  stage: doing
  run: df738252e9614f4cbdf59b181c96a616
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-24T18:04:09.742474Z'
  stage: tests
- number: 24
  speaker: tester
  kind: result
  at: '2026-10-24T18:07:37.517110Z'
  stage: tests
  run: e13775572dac41ae88f0b762b7479703
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-24T18:07:59.666133Z'
  stage: doing
- number: 26
  speaker: coder
  kind: result
  at: '2026-10-24T18:11:10.885200Z'
  stage: doing
  run: 5c864d1604504480b7500e443252e2dd
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-24T18:11:31.560726Z'
  stage: review
- number: 28
  speaker: reviewer
  kind: result
  at: '2026-10-24T18:12:47.129251Z'
  stage: review
  run: 941f5ebbf440434f928748fdaf313d84
- number: 29
  speaker: factory
  kind: started
  at: '2026-10-24T18:13:07.710507Z'
  stage: docs
- number: 30
  speaker: documenter
  kind: result
  at: '2026-10-24T18:14:14.761567Z'
  stage: docs
  run: 364e534559724c4c8c80c309e9c9bfce
- number: 31
  speaker: factory
  kind: started
  at: '2026-10-24T18:14:35.494355Z'
  stage: smoke-test
- number: 32
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T18:15:24.734443Z'
  stage: smoke-test
  run: 2539578023e945ee9598763a336c3820
- number: 33
  speaker: factory
  kind: done
  at: '2026-10-24T18:16:46.332182Z'
  stage: approval
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
6. `run_agent(request)` with a queued fake run returns `SealedRun(result=<the queued result>, nested_repositories=[])`, makes no git call on the host (its `.git` mode is unchanged: no seal), and with `run=<a recorder>` calls the recorder once and the runtime not at all (rows of one parametrized test); a repository the fake run writes as `notes/.git/HEAD` under the request's working directory is not removed and not listed, and an ignored file the fake run writes (`build/out.txt`, the host's `.gitignore` holding `build/`) is still there afterwards (no removal of ignored paths); a file the fake run writes into the host's `agent_home` is left as it is (no home reset).
7. `take(start, PATH)` after the dataset's checkout got `src/new.py` (inside the write paths), `docs/guide.md` changed (outside) and `.venv/bin/x` (ignored by the host's `.gitignore`), and the dataset's `home/.claude.json` was written: the host's `src/new.py` holds the dataset's bytes, `docs/guide.md` is unchanged on the host, nothing of `.venv` or `home` reached the host, and the report is `TakeReport(left=["docs/guide.md"], restored_work_item=False)`.
8. The timing line: after `prepare(...)` and `take(...)` on one object, with the manual clock advanced by 0.4, 12.3, 0.1 and 0.25 seconds inside `reset`, the sync container's run, `advance` and `changed_paths` (fakes wrapped by the test to advance the clock), the factory log's last line ends with `stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s` (one decimal, Python's rounding); `take` on a fresh object without `prepare` writes `... reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s`; exactly one such line per stage, none after `prepare` alone (rows of one parametrized test).
9. A whole stage through `StageRunner` on boundaries with the two fakes and a runtime of the test (an `AgentRuntime` like `CommittingRuntime` of `tests/application/test_stage_run.py`) that writes `tests/test_a.py` and `notes.md` into `<workspace>/checkout` and returns a completed run with the decision `doing`, in the stage `tests`, ends with the pushed result commit holding `tests/test_a.py` and not `notes.md`, the entry's paragraph naming `notes.md`, the factory log holding exactly one `stage environment:` line, and the host's work tree clean afterwards. (The agent's own container, which makes the real runtime write there, is S0008's.)
10. `factory.domain.checks.last_line(lines)` (rows of one parametrized test): a line starting with `make:` is skipped, a line starting with `make[2]:` is skipped, a trailing blank line is skipped, the recipe's last line is returned, and `""` is returned for make messages alone and for no lines.
11. `factory.adapters.make_commands` imports `last_line` from `factory.domain.checks` and defines neither `_last_line` nor `_MAKE_MESSAGE_PREFIXES`; `tests/adapters/test_make_commands*.py` stay unchanged and green.
12. The timeout's seconds are rounded up, not rounded (rows of one parametrized test, with a `ContainerRuns` of the test whose `run` returns `ContainerResult(exit_status=None, output="", timed_out=True, duration=<the limit>)`): under `sync_time_limit` 1.2 seconds `prepare` raises `ContainerError("sync", "no end within 2 s")`, and under 3 seconds `ContainerError("sync", "no end within 3 s")`. (Criterion 5's 1.5 seconds cannot tell rounding up from Python's `round`, which also gives 2.)
13. The timing line carries the durations of the last `prepare` of the object, neither the first's nor their sum (a row of criterion 8's parametrized test): after two `prepare`s on one object, the first for `main` with the clock advanced by 0.4, 12.3 and 0.1 seconds inside `reset`, the sync container's run and `advance`, the second for the work item's branch at its stage-start commit with the clock advanced by 1.0, 2.0 and 3.0 seconds there, and then one `take` with 0.25 seconds inside `changed_paths`, the factory log holds exactly one `stage environment:` line, and it ends with `stage environment: reset 1.0 s, sync 2.0 s, advance 3.0 s, take 0.2 s`.
14. `make check` stays green.
15. docs: `docs/project-guide/stage-environment.md` gains the section *The container environment*: the cycle step by step with the container paths and the mounts, the sync script's steps and why every branch is fetched (decision 5), the agent files (decision 6), the faults and what each leaves behind, `run_agent` without a seal, the take on the snapshots' changed paths, the timing line and how to read it against the plan's measures, `Boundaries.snapshots` and `containers`, `stage_environment_of`, the tests and their fakes; `docs/project-guide/watching.md`, *Boundaries*: the two new fields and what `None` means; `docs/operator-guide.md`, *The factory log*: the line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`, one per stage of a `container` instance, and that an `inline` instance writes none. `docs/decisions.md`: none (S0005 wrote the entry).

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
4. 2026-10-24 human: Answers to the intake (F0042-S0007, the container environment runs the cycle of a stage):

   1. **(a)**: one criterion with a parametrized test of `factory.domain.checks.last_line`, with the rows you name: a `make:` line skipped, a `make[2]:` line skipped, a trailing blank line skipped, the recipe's last line returned, and `""` for make messages alone and for no lines. A second criterion checks that `factory.adapters.make_commands` imports `last_line` from `factory.domain.checks` and no longer defines `_last_line` or `_MAKE_MESSAGE_PREFIXES`. `tests/adapters/test_make_commands*.py` stay unchanged and green.
   2. **Yes**: criterion 6 gains the row that a file the fake run writes into the host's `agent_home` is left as it is (no home reset).

   Please write both into the criteria as you accept.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. The `Boundaries` fields, the `ContainerEnvironment` constructor, `stage_environment_of`, the module constants, the sync call's argument order and mounts, and the `last_line` move into `factory.domain.checks` are all named.
   - Criteria: after the human's answers (journal entry 4) every criterion is testable by one test function, and every Interface rule has criteria for both sides. Criteria 1 to 9 are unchanged. Carried in from entry 4, not improvements of mine: (1) criterion 6 gains the row that a file the fake run writes into the host's `agent_home` is left as it is (no home reset). (2) A new criterion 10 tests `factory.domain.checks.last_line` in a parametrized test with the rows entry 4 names. (3) A new criterion 11 checks that `make_commands` imports `last_line` and no longer defines `_last_line` or `_MAKE_MESSAGE_PREFIXES`, with `tests/adapters/test_make_commands*.py` unchanged. Both new criteria stand before the closing two, so `make check` is now 12 and `docs:` is 13.
   - Smoke test: runnable. The pytest command passes no `-q` because `addopts` already sets one. Each `Expect:` line is checkable. I left the smoke test as it was. The tests for criteria 10 and 11 are the tester's to place, and the pytest command does not name them.
   - Architecture: fits. The application layer holds `ContainerEnvironment` and `SHELL`, the domain holds `last_line`, and the adapters layer is not imported upward.
   - Scope: inside feature.md's S0007 entry. No earlier test changes, and decision 18 (g) holds.
7. factory: started tests as self.
8. tester: Wrote the tests for criteria 1 to 11 against the Interface. Criteria 12 and 13 are the check and the docs, so they get no test.

   - criterion 1: tests/application/test_stage_environment_of.py::test_the_container_environment_needs_both_snapshots_and_containers (rows: both, snapshots-only, containers-only, neither)
   - criterion 2: tests/application/test_container_environment.py::test_prepare_syncs_the_dataset_to_the_commit_and_moves_the_base
   - criterion 3: tests/application/test_container_environment.py::test_the_sync_container_gets_container_paths_mounts_environment_and_limit
   - criterion 4: tests/application/test_container_environment.py::test_a_second_prepare_reuses_the_repository_and_resets_everything_else
   - criterion 5: tests/application/test_container_environment.py::test_a_failed_prepare_raises_and_leaves_the_base (rows: sync-fails, sync-times-out, no-base, no-such-commit, blank-output, make-messages-only)
   - criterion 6: tests/application/test_container_environment.py::test_run_agent_runs_unsealed_through_the_runtime_or_the_given_run (rows: runtime, given-run) and ::test_run_agent_leaves_nested_repositories_ignored_files_and_the_home
   - criterion 7: tests/application/test_container_environment_take.py::test_take_copies_the_snapshots_changes_the_role_may_write
   - criterion 8: tests/application/test_container_environment_take.py::test_one_timing_line_per_take_carries_the_last_prepares_durations (rows: prepare-and-take, take-without-prepare, prepare-alone)
   - criterion 9: tests/application/test_container_environment_take.py::test_a_whole_stage_takes_the_agents_work_from_the_dataset
   - criterion 10: tests/domain/test_checks_last_line.py::test_the_last_line_is_the_recipes_own
   - criterion 11: tests/adapters/test_make_last_line_shared.py::test_the_make_adapter_uses_the_domains_last_line_rule

   Files created:
   - tests/container_support.py: the shared helpers `container_dataset`, `push_main`, `sync_makefile`, `dataset_git`, `local_branches` and `timing_lines`.
   - tests/application/test_container_environment.py
   - tests/application/test_container_environment_take.py
   - tests/application/test_stage_environment_of.py
   - tests/domain/test_checks_last_line.py
   - tests/adapters/test_make_last_line_shared.py

   I changed no earlier test file. tests/conftest.py and tests/adapters/test_make_commands*.py are untouched.

   Notes for the coder:
   - Criterion 5, timeout row: I bound the elapsed time to at least 1 and less than 25 seconds, as the criterion says.
   - Criterion 5, `base_kept`: the "changed paths not empty, then `reset()` empties the dataset" check runs only on the sync-fails row, where the criterion states it.
   - Criterion 5, no-such-commit row: the test checks that `command` is `sync` and that `detail` is not empty. It does not pin git's exact message.
   - Criterion 6: the agent-home row writes its file through the `run=` callable, which then calls the fake runtime.
   - Criterion 9: the Makefile's `sync` writes `.synced` and the host's `.gitignore` ignores it. That way, if the stage also runs a sync on the host, the "host work tree clean" check is not affected.
   - Criterion 11: the test reads `vars(make_commands)["last_line"]`, so `mypy --strict` passes without an explicit re-export.

   `make test` ran once and the new tests are red for the right reason. Four modules could not be imported because `ContainerEnvironment` (factory.application.stage_environment) and `factory.domain.checks.last_line` do not exist yet:
   - tests/application/test_container_environment.py
   - tests/application/test_container_environment_take.py
   - tests/application/test_stage_environment_of.py
   - tests/domain/test_checks_last_line.py

   tests/adapters/test_make_last_line_shared.py does import, and fails on the missing `last_line` in make_commands. `make lint` is green. I skipped the type check, as the stage says to.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/domain/test_checks_last_line.py - ImportError while importing test module '/work/checkout/tests/domain/test_checks_last_line.py'.
9. factory: started doing as self.
10. coder: I built `ContainerEnvironment` and the choice between the two environments. `make check` is green: 99.19 % coverage, ending in `check: green`. The tester's 28 new tests pass, and no test was changed.

    What I built:
    - `src/factory/application/stage_environment.py`:
      - It holds `UPSTREAM`, `AGENT_FILES`, `SHELL`, `SYNC_ENVIRONMENT` and `TIMING_LINE`, and the sync script as one literal.
      - `ContainerEnvironment.prepare` runs reset, then the sync container, then advance. Each step is timed with `boundaries.clock`, and the durations are kept only when all three succeed.
      - `_check_sync` turns a failed result into `ContainerError("sync", …)`. A timeout gives "no end within n s", with the seconds rounded up. A non-zero exit gives the domain's `last_line` of the output, or `exit status <n>` when that is empty.
      - `run_agent` is the runtime's run or the given one, with no seal.
      - `take` is `TakeService` on `changed_paths()`, followed by one `TIMING_LINE` through `boundaries.log.line`, each duration to one decimal with `.1f`.
      - `stage_environment_of` returns the container environment when both fields are set, else the inline one.
    - `src/factory/application/boundaries.py`: the new fields `snapshots` and `containers`, both defaulting to `None`, after `agent_home`.
    - `src/factory/domain/checks.py`: `MAKE_MESSAGE_PREFIXES` and the public `last_line`, moved here from `src/factory/adapters/make_commands.py`. That module now imports `last_line` and no longer has `_last_line` or `_MAKE_MESSAGE_PREFIXES`.

    The sync script:
    - It does `set -eu`, then `mkdir -p "$1" "$2"`.
    - It replaces the agent files with `rm -rf "$2/.claude"` followed by `cp -R "$4" "$2/.claude"`.
    - It then `cd`s into `$1` and runs `git init -q` when there is no `.git`.
    - Then the fetch with `--prune --update-head-ok` of every branch, `checkout -f "$5"`, `reset --hard "$6"` and `make sync`.
    - Its text holds no container path.

    Main choice: the durations are fields on the object, set at the end of a successful `prepare` and zero from the start. A `take` without a `prepare` therefore writes `0.0` with no special case. I rejected a separate timing DTO returned by `prepare`. The interface fixes `prepare` to return `None`, and the line belongs to `take` alone.

    Refactor pass: I read the diff and found nothing to change beyond one docstring I shortened to fit the line length.

    Noticed but not touched:
    - The comment on the sync script gives its reason directly and cites no date in `docs/decisions.md`. The "paths as arguments" decision is decision 5 of `feature.md`, and the log has no entry of its own for it.
    - A failed `prepare` does not reset the kept durations. If a later `take` ran on the same object after a failed `prepare`, it would report the last successful `prepare`'s timings. The stage protocol stops at the error, so that case does not come up.

    `check`: check: green
    `duplicates`: duplicates: 9 new, 37 known, 1 gone
11. factory: started review as self.
12. reviewer: Review round 0. I read the work item and the whole diff of `src/` and `tests/` against it. I left out `make check`, as the stage says: the factory's run after the coder was green (entry 10). I ran `make duplicates` to read its new findings. All 9 are in modules of earlier stories (`fake_containers`, `fake_snapshots`, `podman_runs`, `zfs_snapshots`), none in this diff.

    Findings:
    1. criterion 12 added: it needs its test. Where: `tests/application/test_container_environment.py::test_a_failed_prepare_raises_and_leaves_the_base`, row `sync-times-out`, together with `src/factory/application/stage_environment.py` `_check_sync`. What's wrong: the Interface says `n` is the seconds "rounded up". The only row uses 1.5 s, and that gives 2 under `math.ceil`, under Python's `round` (half to even) and under `int(x) + 1` alike. So nothing pins rounding up, and nothing pins that a whole number stays as it is. The new criterion 12 adds two rows with a `ContainerRuns` of the test that returns `timed_out=True`, so they need no real sleep: 1.2 s gives `no end within 2 s`, and 3 s gives `no end within 3 s`. The closing criteria are renumbered to 13 (`make check`) and 14 (docs). The tester adds the rows. The code needs no change.

    Everything else checked and in order:
    - Criteria 1 to 11: each has its test, and each test checks what its criterion says. Criteria 1, 5, 6, 8 and 10 have their sides as rows of one parametrized test.
    - Architecture: `ContainerEnvironment` and `SHELL` are in `application`, and `last_line` is in `domain`. `make_commands` imports it and keeps no copy.
    - Security: no marker and no string-built command. The sync script takes every path as an argument.
    - Code quality: no copied helper. The new stand-ins (`ResultContainerRuns`, `ClockedSnapshots`, `ClockedContainerRuns`, `WorkspaceRuntime`, `RecordingRun`) copy no shared helper of `tests/`.
    - The Description matches what was built.

    Not a finding, kept open from the coder's note: a failed `prepare` keeps the previous successful `prepare`'s durations. The Interface's "the three of the last `prepare`" does not settle that case, and the stage stops at the error anyway.

    Earlier tests: none. Every test file in the diff is new (`A`).
13. factory: started doing as self.
14. coder: Round 1. The reviewer's only finding was criterion 12, which needs nothing but its test, so I changed no code and no test. Criterion 12 says the timeout's seconds are rounded up, not rounded: under `sync_time_limit` 1.2 s, `prepare` raises `ContainerError("sync", "no end within 2 s")`, and under 3 s it raises `ContainerError("sync", "no end within 3 s")`.

    For the tester: add criterion 12 as two rows of one parametrized test in `tests/application/test_container_environment.py`, rows 1.2 s → 2 s and 3 s → 3 s. Use a `ContainerRuns` of the test whose `run` returns `ContainerResult(exit_status=None, output="", timed_out=True, duration=<the limit>)`, so no real sleep is needed.

    The code should already pass both rows. `_check_sync` in `src/factory/application/stage_environment.py:198` rounds with `math.ceil(time_limit.total_seconds())`.

    The journal changed the task only by adding criterion 12 and renumbering the closing criteria to 13 and 14. The reviewer already wrote that into the Description. I did not run `make check` this round because nothing changed in the working tree; the factory's run after round 0 was green.

    Still open, untouched: a failed `prepare` keeps the durations of the last successful one.
15. factory: started tests as self.
16. tester: This was the approved test change from the coder's entry 14: the test for criterion 12, which the reviewer added. It checks that the timeout's seconds are rounded up. I edited no existing test.

    - criterion 12: tests/application/test_container_environment.py::test_the_timeouts_seconds_are_rounded_up. It has two rows:
      - `fraction-rounds-up`: a limit of 1.2 s gives `ContainerError("sync", "no end within 2 s")`.
      - `whole-stays`: a limit of 3 s gives `ContainerError("sync", "no end within 3 s")`.

    How the test works: it builds `ContainerEnvironment` on the `dataset` fixture's snapshots. For the container runs it reuses the module's own `ResultContainerRuns`, which here returns `ContainerResult(exit_status=None, output="", timed_out=True, duration=<the limit>)`. No container really runs and nothing sleeps. The test asserts `command` is `sync` and `detail` is the exact text above.

    Files: I created no new file. I added the test to tests/application/test_container_environment.py, which this story's tester wrote earlier. No other earlier test file changed.

    Imports: every module imported. The new rows pass at once, because the code from round 0 already rounds up with `math.ceil`. They are not red, and the coder expected that in entry 14. One `make test` run was green with 99.19 % coverage (`test: green (71.2 s)`), and `make lint` was green. I skipped the type check, as the stage says.

    Still open from entries 10 and 12: after a failed `prepare`, the object keeps the durations of the last successful one. No criterion covers that case, so I wrote no test for it.

    `lint`: lint: green (0.7 s)
    `test`: test: green (67.6 s)
17. factory: started doing as self.
18. coder: Round 1, after the tester's change. The only finding was the reviewer's criterion 12. The tester has now written its test, `tests/application/test_container_environment.py::test_the_timeouts_seconds_are_rounded_up`, with the rows 1.2 s → 2 s and 3 s → 3 s. The round-0 code already passes it: `_check_sync` in `src/factory/application/stage_environment.py` rounds up with `math.ceil`. So I changed no code and no test this round. `make check` is green: 99.19 % coverage, `test: green (70.7 s)`, ending in `check: green`.

    What I built (unchanged since round 0, entry 10):
    - `src/factory/application/stage_environment.py`: `ContainerEnvironment`, `stage_environment_of`, the constants and the sync script.
    - `src/factory/application/boundaries.py`: the fields `snapshots` and `containers`.
    - `src/factory/domain/checks.py`: `last_line` and `MAKE_MESSAGE_PREFIXES`, which `src/factory/adapters/make_commands.py` now imports instead of keeping its own copy.

    Main choice, still the one from round 0: the durations are fields on the object, zero from the start and set when a `prepare` succeeds. I rejected a timing DTO returned by `prepare`, because the interface fixes `prepare` to return `None`.

    Refactor pass: there is no new diff this round, so there was nothing to refactor.

    Journal effect on the Description: it only added criterion 12 and renumbered the two closing criteria to 13 and 14. The reviewer already wrote both into the Description.

    Noticed, not touched: after a failed `prepare`, the object keeps the durations of the last successful one. No criterion covers that case, and the stage stops at the error anyway.

    `check`: check: green
    `duplicates`: duplicates: 9 new, 37 known, 1 gone
19. factory: started review as self.
20. reviewer: Review round 1. I read the work item and the whole diff of `src/` and `tests/` against it, and went through every criterion and every rule of the Interface. Criteria 1 to 12 each have their test, and each test checks what its criterion says. I left out `make check`: the factory's run after the coder was green (entry 18).

    Findings:
    1. criterion 13 added: it needs its test. Where: `tests/application/test_container_environment_take.py::test_one_timing_line_per_take_carries_the_last_prepares_durations`, together with `src/factory/application/stage_environment.py` `ContainerEnvironment.prepare`/`take`. What's wrong: the Interface says the timing line carries "the three of the last `prepare` of this object". Every row runs at most one `prepare`, so code that added the durations of several prepares, or kept the first one's, would still pass. Fix: criterion 13 adds a row to criterion 8's parametrized test. It runs two prepares on one object, with the clock advanced by 0.4/12.3/0.1 s in the first and 1.0/2.0/3.0 s in the second, then one `take` with 0.25 s. The test expects exactly one line, ending `stage environment: reset 1.0 s, sync 2.0 s, advance 3.0 s, take 0.2 s`. The closing criteria are renumbered to 14 (`make check`) and 15 (docs). The tester adds the row. The code needs no change.

    Still open, as before, and not a finding: after a failed `prepare` the object keeps the durations of the last successful one. The Interface does not settle that case.

    Earlier tests: none. Every test file in the diff is new (`A`).
21. factory: started doing as self.
22. coder: Round 2. The reviewer had one finding (entry 20): criterion 13 needs a test and nothing else. I changed no code and no test.

    For the tester: add criterion 13 as a row of criterion 8's parametrized test, `tests/application/test_container_environment_take.py::test_one_timing_line_per_take_carries_the_last_prepares_durations`. The row runs two `prepare`s on one object:
    - the first for `main`, with the clock advanced by 0.4, 12.3 and 0.1 s inside `reset`, the sync run and `advance`;
    - the second for the work item's branch at its stage-start commit, with the clock advanced by 1.0, 2.0 and 3.0 s there.

    It then runs one `take` with 0.25 s inside `changed_paths`. It expects exactly one `stage environment:` line, ending in `stage environment: reset 1.0 s, sync 2.0 s, advance 3.0 s, take 0.2 s`.

    I expect the round-0 code to pass the row without a change. `ContainerEnvironment.prepare` in `src/factory/application/stage_environment.py:136-138` assigns the three durations (it does not add to them), so each successful `prepare` replaces the previous one's. The line is written only in `take`, at line 157.

    What the journal changed: only the new criterion 13, and the closing criteria moved to 14 and 15. The reviewer already wrote both into the Description. I did not run `make check`, because the working tree has no change; the factory's run after entry 18 was green.

    What I built, unchanged since round 0 (entry 10):
    - `src/factory/application/stage_environment.py`
    - `src/factory/application/boundaries.py`
    - `src/factory/domain/checks.py`
    - `src/factory/adapters/make_commands.py`

    The main choice is also unchanged: the durations are fields on the object, zero at the start and replaced when a `prepare` succeeds. I rejected a timing DTO returned by `prepare`.

    Refactor pass: there is no new diff this round, so nothing to refactor.

    Noticed, not touched: after a failed `prepare`, the object keeps the durations of the last successful one. No criterion covers that case.
23. factory: started tests as self.
24. tester: Mode: the approved test change from the coder's entry 22. The reviewer added criterion 13, and it needed only its test, so I wrote it as a new row of criterion 8's parametrized test. The three existing rows still check what they checked before.

    - criterion 13: tests/application/test_container_environment_take.py::test_one_timing_line_per_take_carries_the_last_prepares_durations, row `last-prepare-counts`.
      - What it does: two `prepare`s on one object, the first for `main` at the host's `main` commit with steps 0.4/12.3/0.1 s, the second for the work item's branch at its stage-start commit with steps 1.0/2.0/3.0 s. Then one `take`, with 0.25 s inside `changed_paths`.
      - What it expects: exactly one `stage environment:` line, ending in `stage environment: reset 1.0 s, sync 2.0 s, advance 3.0 s, take 0.2 s`.
    - criterion 8: the same test, rows `prepare-and-take`, `take-without-prepare` and `prepare-alone`, unchanged in what they check.

    How the test changed: until now the clocked fakes always advanced the clock by the same fixed amounts. Now `ClockedSnapshots` and `ClockedContainerRuns` read their seconds from a shared, mutable `Pace` that holds a frozen `Steps` (reset, sync, advance), and the test sets the pace before each `prepare`. The amount inside `changed_paths` stays fixed at 0.25 s (`TAKE_SECONDS`). The `prepares` parameter is now a tuple of (branch, steps) pairs instead of a bool; an empty tuple keeps the unclocked object for the take-without-prepare row.

    Files: I created no new file. I edited only tests/application/test_container_environment_take.py, which this story's tester wrote. No other earlier test file changed.

    Imports: every module imported. The new row passes at once, as the coder expected: `prepare` replaces the durations rather than adding to them. One `make test` run was green (99.19 % coverage, `test: green (71.1 s)`), and `make lint` was green.

    Still open, as before: after a failed `prepare`, the object keeps the durations of the last successful one. No criterion covers that case, so there is no test for it.

    `lint`: lint: green (0.7 s)
    `test`: test: green (70.9 s)
25. factory: started doing as self.
26. coder: Round 2, after the tester's change. The reviewer had one finding (entry 20): criterion 13. The tester has now written its test as the `last-prepare-counts` row of `tests/application/test_container_environment_take.py::test_one_timing_line_per_take_carries_the_last_prepares_durations`. The round-0 code passes that row without a change: `ContainerEnvironment.prepare` in `src/factory/application/stage_environment.py` replaces the three durations each time and does not add them up. So I changed no code and no test this round. `make check` is green: 99.19 % coverage, `test: green (69.9 s)`, ending in `check: green`.

    What I built (unchanged since round 0, entry 10):
    - `src/factory/application/stage_environment.py`: `ContainerEnvironment`, `stage_environment_of`, the constants and the sync script.
    - `src/factory/application/boundaries.py`: the fields `snapshots` and `containers`.
    - `src/factory/domain/checks.py`: `last_line` and `MAKE_MESSAGE_PREFIXES`. `src/factory/adapters/make_commands.py` now imports them and no longer keeps its own copy.

    Main choice: the durations are fields on the object. They start at zero and are replaced when a `prepare` succeeds. I rejected a timing DTO returned by `prepare`, because the interface fixes `prepare` to return `None`.

    Refactor pass: nothing to refactor, because this round added no code.

    What the journal changed: only criterion 13, with the closing criteria renumbered to 14 and 15. The reviewer already wrote both into the Description.

    Noticed, not touched: after a failed `prepare`, the object keeps the durations of the last successful one. No criterion covers that case.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 9 new, 37 known, 1 gone
27. factory: started review as self.
28. reviewer: Review round 2. I read the work item and the whole diff of `src/` and `tests/` against it, and went through every criterion and every rule of the Interface again. The code under `src/` has not changed since round 0: one coder commit, 2d1d05b3. The only test change since round 1 is the `last-prepare-counts` row. I did not run `make check`, because the factory's run after the coder was green (entry 26).

    no findings

    What I checked:
    - Criterion 1: `tests/application/test_stage_environment_of.py` has four rows covering both, one and neither of snapshots and containers.
    - Criteria 2 to 4: the tests check
      - HEAD, the branch and the local branches, including the `--prune` of `gone`;
      - the sync marker and the agent file;
      - that `changed_paths` is empty after the base moves;
      - the exact command list after the script, the mounts, the environment, the time limit and the working directory, and that the script contains no container path;
      - on the second prepare: the repository is reused, the stray files are gone, the changed agent file arrives and `extra.md` is removed.
    - Criteria 5 and 12, the faults of `prepare`:
      - `boom` with make's own line skipped, and the base kept until the next `reset()`;
      - a timeout under 1.5 s whose elapsed time is bounded, plus the rounding-up rows 1.2 s → 2 s and 3 s → 3 s;
      - `SnapshotError` with no container call;
      - a commit that does not exist;
      - `exit status 3` and `exit status 2` when the output has no usable line.
    - Criterion 6:
      - two parametrized rows, one through the runtime and one through a given `run`, and the `.git` modes are unchanged;
      - the nested repository, the ignored `build/out.txt` and the file written into `agent_home` all stay in place.
    - Criterion 7: `test_take_copies_the_snapshots_changes_the_role_may_write` checks that `src/new.py` is copied, `docs/guide.md` is left, nothing of `.venv` or `home` reaches the host, and the exact `TakeReport`.
    - Criteria 8 and 13: one parametrized test with four rows (prepare-and-take, take-without-prepare, prepare-alone, last-prepare-counts). Each row checks the exact end of the line, or that no line was written.
    - Criterion 9: a whole stage through `StageRunner` gives a result commit with `tests/test_a.py` and without `notes.md`, the journal names `notes.md`, the log holds one timing line, and the host's work tree is clean.
    - Criteria 10 and 11: `last_line` has six parametrized rows. `make_commands` holds the domain's function and no private copy.
    - Interface rules: the base does not move after a failed sync, and `SnapshotError` propagates as it is. Both are pinned. Exit status 0 passes in every success test.
    - Architecture: `ContainerEnvironment`, `SHELL` and the constants are in `application`, and they import only `application` and `domain`. `last_line` and `MAKE_MESSAGE_PREFIXES` are in `domain`, and `make_commands` imports them without keeping a copy. `Boundaries` gains the two fields with `None` defaults, after `agent_home`.
    - Security: no suppression markers and no command built from strings. The sync script gets every path, the branch and the commit as positional arguments, and the error detail is the last line of the recipe.
    - Quality: the names fit, there is no dead code, and the comments say why. `make duplicates`: the 9 new findings are in modules of earlier stories (read in round 0, and `src/` has not changed since).
    - Hygiene: the Description matches what was built. The journal gives the main choice (the durations kept as fields, replaced on each successful `prepare`) and the rejected option (a timing DTO). Docs criterion 15 still says what the documenter has to write.

    Still open, as before, and not a finding: after a failed `prepare`, the object keeps the durations of the last successful one. The Interface does not settle that case.

    Earlier tests: none. Every test file in the diff is new (`A`).

    Notes:
    1. `tests/application/test_container_environment.py:35` and `tests/application/test_container_environment_take.py:34`: `FIVE_MINUTES` is defined in both modules. It could live in `tests/container_support.py`.
    2. `tests/application/test_container_environment_take.py`, `ClockedSnapshots` and `ClockedContainerRuns`: their overriding methods have no `@override`, while `ResultContainerRuns` and `ContainerEnvironment` have it.
29. factory: started docs as self.
30. documenter: Docs round 2. I found no code or docstring finding, so I end with `smoke-test`. I read the story and its journal, the code under `src/` (`stage_environment.py` in full) and the existing docs. The code matches the Interface. `build_boundaries` sets neither new field, so no instance chooses the container environment yet. I wrote that into the docs. I changed only documents, so I did not run `make check`. I ran `make documents`, which printed `documents ok`.

    Files changed:
    - `docs/project-guide/stage-environment.md`:
      - New section *The container environment*. It covers:
        - `prepare` step by step, with the container paths and the two read-only mounts;
        - the sync script, the reason every branch is fetched (decision 5) and the agent-file copy that replaces the folder (decision 6);
        - the faults and what each leaves behind, `run_agent` without a seal, and the take on the snapshots' changed paths;
        - the timing line and how to read it, the wiring, and the tests with their fakes.
      - I corrected three stale passages:
        - the intro said only the inline environment exists;
        - `stage_environment_of` was described as "always inline";
        - *The take* said "Nothing calls the service yet".
    - `docs/project-guide/watching.md`, *Boundaries*: the fields `snapshots` and `containers`. `None` means the inline environment. `build_boundaries` leaves both `None`, and the `boundaries` fixture is unchanged.
    - `docs/operator-guide.md`, *The factory log*: the line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`. It is written once per stage by a `container` instance and not by an `inline` one. I also said that no instance chooses the container environment yet.

    Cross-read and found current: `README.md`, `docs/project-guide/README.md`, `docs/decisions.md` (none needed, S0005 wrote the entry), and the `make_commands` mentions in `docs/project-guide/processes-and-checks.md`. I found no mention of the private `_last_line` or `_MAKE_MESSAGE_PREFIXES` in the docs.

    I did not test the doc example's timing line against a real run: the container environment is only played on the fakes. The example line is the shape that `TIMING_LINE` produces, and tests pin its exact ending.

    Stale or open text I saw and did not touch, not mine to fix:
    - After a failed `prepare` the object keeps the durations of the last successful one. This was open in the reviewer's notes. I only documented the behaviour as it stands.
    - The reviewer's two test notes: `FIVE_MINUTES` is defined in two test modules, and `ClockedSnapshots` and `ClockedContainerRuns` lack `@override`. Both are for the tester or coder, not findings.
    - A comment above `_SYNC_SCRIPT` in `src/factory/application/stage_environment.py` wraps oddly mid-sentence. That is a code comment, so it is not mine to edit.

    `check`: check: green (not run again: passed on tree 27d3de5f1300 at 2026-10-24T18:09:51Z)
    `secrets`: secrets: green (1.8 s)
    `documents`: documents ok
31. factory: started smoke-test as self.
32. smoke-tester: Smoke test, round 2. I ran both commands under `## Smoke test` exactly as written, from the repository root, and fixed nothing.

    Command 1 (the pytest run of the three new test modules, the last line counted by `grep -cE '^[0-9]+ passed in '`):
    ```
    1
    ```
    Met `Expect: 1`. I ran the same pytest command again without the `grep`, only to see the last line: `24 passed in 3.63s`.

    Command 2 (the `uv run python` heredoc):
    ```
    Bytecode compiled 4164 files in 70ms
    stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s
    {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/work/home'} StageEnvironment
    None None
    ```
    Met the expectation. The three lines the script prints are exactly the expected ones. The first line, `Bytecode compiled ...`, is uv's own message about the environment, not the script's output, so I do not count it as a finding.

    Against the acceptance criteria: nothing in the output contradicts any criterion.
    - `TIMING_LINE` gives the exact line of criteria 8 and 13.
    - `SYNC_ENVIRONMENT` is the environment of criterion 3.
    - `ContainerEnvironment` derives from `StageEnvironment`.
    - `Boundaries.snapshots` and `Boundaries.containers` default to `None`, as the Interface says.
    - The 24 tests of criteria 1 to 9, 12 and 13 pass.

    Criteria 10 and 11 (`last_line`, `make_commands`) and 14 (`make check`) are not exercised by the smoke test. The docs stage reports `make check` green on the current tree.

    No findings.

    Still open, carried over from the review and not a finding: after a failed `prepare`, the object keeps the durations of the last successful one. The Interface does not settle that case.
33. factory: done (pull request merged); cost: 15 runs, 30.2 min, 135 turns, 495900 tokens in (4111969 more from cache), 76355 out, $6.48
