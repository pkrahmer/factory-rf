---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 478
comments_read: [6432903366, 6433141030]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-27T03:18:05.529489Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-27T03:18:05.534971Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-27T03:18:27.981856Z'
  stage: intake
  run: ed41856240664b3ab0c96c65a95ff97a
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-27T03:19:43.622712Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-27T03:20:03.697121Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-27T03:20:20.856498Z'
  stage: intake
  run: 1898b49551fa4516a917ef24a8a1883d
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-27T03:20:41.153636Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-27T03:27:29.738088Z'
  stage: tests
  run: de65a84aece243808a8013dda984d162
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-27T03:27:50.340280Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-27T03:37:26.091930Z'
  stage: doing
  run: 71cb7248539b47e2805606418319fd58
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-27T03:39:45.709966Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-27T03:40:03.536600Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-27T03:40:21.380244Z'
  stage: doing
  run: 053b077404ac4898bf206d66d743f133
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-27T03:40:41.852123Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-27T03:46:44.891307Z'
  stage: tests
  run: 4b95d78c3ba34ce5ad726af396e8e871
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-27T03:47:05.123622Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-27T03:53:18.033502Z'
  stage: doing
  run: 19881c3adfb542e7b9ad9d1d98087c97
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-27T03:53:38.307757Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-10-27T03:54:26.659472Z'
  stage: review
  run: 2793c32de39f4ebf9bda4fc81de4d62f
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-27T03:54:46.994682Z'
  stage: docs
- number: 21
  speaker: documenter
  kind: result
  at: '2026-10-27T03:55:11.167987Z'
  stage: docs
  run: 5c3e50f883c445c9abdcf1c507c29311
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-27T03:55:31.591846Z'
  stage: smoke-test
- number: 23
  speaker: smoke-tester
  kind: result
  at: '2026-10-27T03:55:55.751628Z'
  stage: smoke-test
  run: 1a48bafc6a5441a0bffd6157570e3f88
- number: 24
  speaker: factory
  kind: done
  at: '2026-10-27T03:57:16.056816Z'
  stage: approval
---

# The wrappers run their command through one run-or-raise helper

<!-- proposed by feature acceptance of 2026-10-27; refine before starting -->

## Description

S0008 (the factory powers its machine off after an idle stretch) wrote `SystemctlPowerOff.power_off` as a third copy of one block: build a `ProcessRequest` at `/` with no environment, the wrapper's time limit and merged standard error, run it, and turn a program that cannot start, the time limit reached, or an exit status the wrapper does not accept into the wrapper's own error, with the detail `failure_detail` or `no_end_detail` of `factory.adapters.printed_output` gives. `ZfsSnapshots._execute` holds the same block and `PodmanRuns._query` the same without the exit check, and each of the three modules defines its own `_ROOT = Path("/")`. `make duplicates` has reported the two similarities as `2 new` since S0008, and the human recorded them in S0008's journal (entry 33) "for a later tidy-up". This story writes the block once, in `factory.adapters.process`, and the three wrappers call it with their own error. What stays: every wrapper's commands, errors, error texts and time limits; `run_process`, `run_streaming` and the drain; `PodmanRuns.run`, which passes the launch's environment and keeps its own request; every existing test, unchanged, except four that now patch `run_process` on `factory.adapters.process`, where `run_or_raise` calls it, each keeping its name and what it checks (the human's leave, journal entry 11): three in `tests/adapters/test_zfs_snapshots.py` and `test_version_runs_under_two_minutes_by_default` in `tests/adapters/test_podman_runs_results.py`.

## Interface

`factory.adapters.process` (`adapters`):

```python
ROOT = Path("/")

def run_or_raise(
    argv: list[str],
    *,
    time_limit: timedelta,
    fault: Callable[[str], Exception],
    cwd: Path = ROOT,
    accepted: tuple[int, ...] | None = (0,),
) -> ProcessResult: ...
```

- Runs `ProcessRequest(argv=argv, cwd=cwd, env=None, time_limit=time_limit, merge_stderr=True)` through `run_process` and returns its result.
- A program that cannot be started (`OSError`) raises `fault(str(error))`, chained from the error.
- A call that reached `time_limit` raises `fault(no_end_detail(time_limit))`.
- With `accepted` given, an exit status not in it raises `fault(failure_detail(result.stdout, result.exit_status))`; with `accepted=None` every exit status is returned.

`factory.adapters.zfs_snapshots`, `factory.adapters.power_off`, `factory.adapters.podman_runs` (`adapters`): `ZfsSnapshots._execute`, `SystemctlPowerOff.power_off` and `PodmanRuns._query` call `run_or_raise` (`_query` with `cwd=self._workspace` and `accepted=None`); `PodmanRuns.run` passes `cwd=ROOT`; none of the three modules defines `_ROOT`. The texts of `SnapshotError`, `PowerOffError` and `ContainerError` do not change.

Tests (the tester writes them): a new module at the tester's choice, for example `tests/adapters/test_run_or_raise.py`, with `sh` stand-ins under `tmp_path`. No earlier test changes: the tests of the three wrappers stay as they are and stay green.

## Acceptance criteria

1. The helper (rows of one parametrized test, `fault` a function that returns a `RuntimeError` of its detail): `sh -c 'echo ok'` returns a result with exit status 0 and `stdout == "ok\n"`; `sh -c 'echo boom; exit 3'` raises `RuntimeError("boom")`; `sh -c 'echo boom >&2; exit 3'` raises `RuntimeError("boom")`; the same with `accepted=(0, 3)` and with `accepted=None` returns exit status 3; `sh -c 'exit 1'` (nothing printed) raises `RuntimeError("exit status 1")`; a program path under `tmp_path` that does not exist raises a `RuntimeError` whose `__cause__` is an `OSError` and whose text equals `str(` that `__cause__` `)`; `sh -c 'sleep 30'` with a time limit of one second raises `RuntimeError(no_end_detail(timedelta(seconds=1)))`.
2. The directory (rows of one parametrized test): `pwd` run through `run_or_raise` without `cwd` prints `/`; with `cwd=tmp_path` it prints `tmp_path`.
3. The block is held once (rows of one parametrized test reading the three modules with `ast`): `zfs_snapshots`, `power_off` and `podman_runs` assign no name `_ROOT`; `zfs_snapshots` and `power_off` construct no `ProcessRequest`; `podman_runs` constructs exactly one, in `run`.
4. `make check` stays green.
5. docs: `docs/project-guide/processes-and-checks.md`, `## Starting a process`: `run_or_raise` and `ROOT`, its rules, and the three wrappers that use it. `docs/decisions.md`, `docs/operator-guide.md`, `README.md`: none (no decision and no operator-visible change).

## Smoke test

```bash
uv run python -c '
from datetime import timedelta
from factory.adapters.process import run_or_raise
try:
    run_or_raise(["sh", "-c", "echo boom; exit 3"], time_limit=timedelta(seconds=10), fault=RuntimeError)
except RuntimeError as error:
    print(error)
print(run_or_raise(["pwd"], time_limit=timedelta(seconds=10), fault=RuntimeError).stdout.strip())'
```
Expect: two lines: `boom`; `/`

```bash
grep -c '^_ROOT = ' src/factory/adapters/zfs_snapshots.py src/factory/adapters/power_off.py src/factory/adapters/podman_runs.py
make duplicates 2>&1 | grep '^duplicates:'
```
Expect: four lines: `src/factory/adapters/zfs_snapshots.py:0`; `src/factory/adapters/power_off.py:0`; `src/factory/adapters/podman_runs.py:0`; a line that begins `duplicates: 0 new,`

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Interface, architecture (the helper sits in `factory.adapters.process` and imports `printed_output`, both in `adapters`), scope (A0001 story within F0045, nothing in "Out of scope") and smoke test (commands runnable, no pytest, every `Expect:` checkable) are fine. Two Interface clauses have no criterion, so two coders could read them two ways and both would pass:

   1. The Interface says an `OSError` raises `fault(str(error))`. Criterion 1 checks only that the `RuntimeError`'s `__cause__` is an `OSError`. It does not check the detail text. Proposal: add that the `RuntimeError`'s text equals `str(` the `__cause__` `)` in the same row. I would choose this.

   2. The Interface says the request has `merge_stderr=True`. No criterion has a program that prints to standard error. All the stand-ins print on standard output, so `merge_stderr=False` would pass. Proposal: add a row in criterion 1 where `sh -c 'echo boom >&2; exit 3'` raises `RuntimeError("boom")`. I would choose this.

   If you accept both, I carry them into criterion 1 as written and end with `tests`.
4. 2026-10-27 human: Both accepted as you propose: the `OSError` row also checks the text equals `str(` the `__cause__` `)`, and a row with `sh -c 'echo boom >&2; exit 3'` raises `RuntimeError("boom")`.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `run_or_raise` and `ROOT` in `factory.adapters.process` are concrete, with a full signature. The three callers are named, with `_query`'s `cwd` and `accepted=None` and `run`'s `cwd=ROOT`. Error texts stay unchanged.
   - Criteria: I carried the human's answer (journal entry 4) into criterion 1 and changed nothing else. The `OSError` row now also checks that the text equals `str(` the `__cause__` `)`. A new row, `sh -c 'echo boom >&2; exit 3'` raising `RuntimeError("boom")`, covers `merge_stderr=True`. Every Interface clause now has a criterion. Both sides are covered: accepted and refused exit status, `accepted=None`, a start failure, the time limit, and `cwd` default and given. Each criterion is testable by one parametrized test.
   - Smoke test: both blocks are runnable and run no pytest. Each `Expect:` line is checkable: two lines `boom` and `/`; the three `:0` counts and a `duplicates: 0 new,` line.
   - Architecture: the helper sits in `adapters` beside `run_process` and imports `printed_output`, also in `adapters`. The wrappers stay the only callers of the process module, so no layer rule is touched.
   - Scope: the story comes from A0001 and is listed in F0045's stories. It touches nothing in "Out of scope", and it changes no earlier test.
7. factory: started tests as vm.
8. tester: Wrote the tests for the three criteria that need tests, all in one new module. Each criterion is one parametrized test:
   - criterion 1: `tests/adapters/test_run_or_raise.py::test_run_or_raise_returns_the_result_or_raises_the_wrappers_fault`. It has eight rows: success with `stdout == "ok\n"`; a refused status printed on stdout; a refused status printed on stderr; `accepted=(0, 3)`; `accepted=None`; `exit status 1` when nothing is printed; a missing program under `tmp_path`, where `__cause__` is an `OSError` and the text equals `str(__cause__)`; and `sleep 30` at a 1 s limit giving `no_end_detail(timedelta(seconds=1))`. The rows that check the default `accepted` call without that argument. The `fault` passed in returns `RuntimeError(detail)`.
   - criterion 2: `tests/adapters/test_run_or_raise.py::test_run_or_raise_runs_in_root_unless_given_a_directory`. Rows: `pwd` without `cwd` prints `/`; with `cwd=tmp_path` it prints `str(tmp_path)`.
   - criterion 3: `tests/adapters/test_run_or_raise.py::test_the_wrappers_hold_no_copy_of_the_run_or_raise_block`. One row for each of `zfs_snapshots`, `power_off` and `podman_runs`. Each row parses the module with `ast` and checks that no `_ROOT` is assigned. It also checks which functions construct `ProcessRequest(...)`: none in the first two, exactly `["run"]` in `podman_runs`. It finds the modules through `SRC` in `tests/source_search.py`.
   - criteria 4 and 5 (`make check`, docs) get no test.

   Files created: `tests/adapters/test_run_or_raise.py`. No earlier test was changed.

   Red run: `make test` fails at collection with an ImportError in `tests/adapters/test_run_or_raise.py`, because `run_or_raise` does not exist yet in `factory.adapters.process`. The module under test is therefore `factory.adapters.process` (the name `run_or_raise`). `make lint` is green.

   The test of criterion 3 reads the source, as the structural tests listed under `[tool.mutmut]` in `pyproject.toml` do. Leaving it out of mutmut's runs would need a change to `pyproject.toml`, which is outside the tester's write paths. I did not make it; the human may want to add it to that list.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/adapters/test_run_or_raise.py - ImportError while importing test module '/work/checkout/tests/adapters/test_run_or_raise.py'.
9. factory: started doing as vm.
10. coder: Stopped before `make check` is green. Four earlier tests contradict "every existing test, unchanged" together with the Interface. I need your word on which one gives way.

    What I built (left in the working tree):
    - `src/factory/adapters/process.py`: `ROOT` and `run_or_raise`, as the Interface states.
    - `src/factory/adapters/zfs_snapshots.py`: `_execute` calls `run_or_raise` with `fault=functools.partial(SnapshotError, command)`.
    - `src/factory/adapters/podman_runs.py`: `_query` calls `run_or_raise` with `cwd=self._workspace, accepted=None`. `run` passes `cwd=ROOT`, and the comment that sat on `_ROOT` moved to that line.
    - `src/factory/adapters/power_off.py`: `power_off` calls `run_or_raise(fault=PowerOffError)`. To keep the text `cannot start <sudo>: <error>`, it catches a `PowerOffError` whose `__cause__` is an `OSError` and raises it again with that prefix, chained from the `OSError`. I rejected changing the start-failure text, because the Interface keeps the error texts.
    - None of the three modules defines `_ROOT` any more. `make duplicates` now reports `duplicates: 0 new, 41 known, 1 gone`.
    - lint, types, layers, sast, secrets and licenses are green. Every new test in `tests/adapters/test_run_or_raise.py` passes, and so do all the other tests except these four:

    The contradiction: these tests monkeypatch `run_process` by name on the wrapper module, so they only see a request when the wrapper calls `run_process` itself. Under the Interface, the wrapper calls `run_or_raise`, which calls `factory.adapters.process.run_process`.
    - `tests/adapters/test_zfs_snapshots.py::test_the_default_time_limit_is_ten_minutes_and_reaches_run_process` and `::test_the_time_limit_is_named_in_whole_seconds_rounded_up[fraction]` / `[whole]` each do `monkeypatch.setattr(zfs_snapshots, "run_process", recording)`. Each fails with `E   AttributeError: <module 'factory.adapters.zfs_snapshots' ...> has no attribute 'run_process'`.
    - `tests/adapters/test_podman_runs_results.py::test_version_runs_under_two_minutes_by_default`: its `recorder` fixture patches `podman_runs.run_process`, which `_query` no longer calls. `version()` then runs the real stand-in and fails with `E   factory.domain.errors.ContainerError: container command .../podman-bin/podman --version failed: printed nothing`.

    Options:
    A. The tester changes those four tests to patch `run_process` where it is called. In zfs, `monkeypatch.setattr(process, "run_process", recording)` in place of `zfs_snapshots`. In podman, the test that goes through `_query` patches `factory.adapters.process.run_process` too, while the `recorder` fixture keeps patching `podman_runs.run_process` for the `run` tests. Each test keeps its name and checks the same thing. I would choose this.
    B. `run_or_raise` gets a further keyword, `run: Callable[[ProcessRequest], ProcessResult] = run_process`, and each wrapper passes its own module's `run_process`, so the old patch points still work. This changes the Interface and keeps an import in each wrapper only to serve the tests.
    C. The zfs and podman wrappers keep their own block. That undoes the story.

    With A, I end the next round with `tests` and name these four tests and the change.

    Refactor: I read the diff once. Nothing more needed changing beyond the moved comment.
11. 2026-10-27 human: A: the human's leave for exactly those four tests: they patch `run_process` where it is called (`factory.adapters.process`); the podman `recorder` fixture keeps patching `podman_runs.run_process` for the `run` tests. Each keeps its name and checks the same thing. No extra keyword on `run_or_raise`.
12. factory: started doing as vm.
13. coder: No code changed this round. The human chose option A (entry 11), which needs a change to four tests. The tester makes it, as follows:
    - `tests/adapters/test_zfs_snapshots.py::test_the_default_time_limit_is_ten_minutes_and_reaches_run_process`, `::test_the_time_limit_is_named_in_whole_seconds_rounded_up[fraction]` and `[whole]`: patch `run_process` where it is now called. That means `monkeypatch.setattr(process, "run_process", recording)` on `factory.adapters.process`, not on `zfs_snapshots`.
    - `tests/adapters/test_podman_runs_results.py::test_version_runs_under_two_minutes_by_default`: patch `factory.adapters.process.run_process`, because `_query` reaches it through `run_or_raise`. The `recorder` fixture keeps patching `podman_runs.run_process` for the `run` tests.

    Each test keeps its name and checks the same thing. `run_or_raise` gets no extra keyword.

    The implementation from round 0 is already on the branch:
    - `src/factory/adapters/process.py`: `ROOT` and `run_or_raise`.
    - `src/factory/adapters/zfs_snapshots.py`, `src/factory/adapters/power_off.py`, `src/factory/adapters/podman_runs.py`: these call `run_or_raise`, none defines `_ROOT`, and `PodmanRuns.run` passes `cwd=ROOT`.

    When the tester sends the work item back, I expect `make check` to go green with no further code change.

    The journal changes one thing in the description: its "every existing test, unchanged" now has these four tests as the exception, by the human's leave. I left `## Description` as it is and name the change here.
14. factory: started tests as vm.
15. tester: I changed the four tests the human allowed in journal entry 11, as the coder's entry 13 named them. Each test keeps its name and checks the same thing. No other test changed.

    - `tests/adapters/test_zfs_snapshots.py::test_the_default_time_limit_is_ten_minutes_and_reaches_run_process` and `::test_the_time_limit_is_named_in_whole_seconds_rounded_up[fraction]` / `[whole]`: these now do `monkeypatch.setattr(process, "run_process", recording)` on `factory.adapters.process` instead of `zfs_snapshots`. The module import changed from `zfs_snapshots` to `process`, since nothing else in the file used `zfs_snapshots` as a module.
    - `tests/adapters/test_podman_runs_results.py::test_version_runs_under_two_minutes_by_default`: this test now also takes `monkeypatch` and patches `factory.adapters.process.run_process` with the same `recorder`, because `_query` reaches `run_process` through `run_or_raise`. The `recorder` fixture still patches `podman_runs.run_process` for the `run` tests. `process` was added to the import from `factory.adapters`.

    Why: the wrappers now call `run_or_raise`, which calls `run_process` inside `factory.adapters.process`. A patch on the wrapper module no longer reached that call.

    Files changed: `tests/adapters/test_zfs_snapshots.py`, `tests/adapters/test_podman_runs_results.py`. No files created. Every module imported in the test run.

    `make test`: test: green (166.0 s)
    `make lint`: lint: green (0.2 s)

    `lint`: lint: green (0.2 s)
    `test`: test: green (165.8 s)
16. factory: started doing as vm.
17. coder: `make check` is green (`test: green (166.0 s)`, `check: green`). I changed no code this round. The implementation from the first doing run already passes the four tests the tester changed in entry 15, as I expected in entry 13.

    What I built (in the working tree on the branch):
    - `src/factory/adapters/process.py`: `ROOT = Path("/")` and `run_or_raise`, as the Interface states. It runs a `ProcessRequest` with `env=None` and `merge_stderr=True` through `run_process`. Each failure raises `fault` of a detail:
      - `OSError`: `fault(str(error))`, chained from the error.
      - Time limit reached: `fault(no_end_detail(time_limit))`.
      - Exit status outside `accepted`: `fault(failure_detail(stdout, status))`.
      - `accepted=None` returns every status.
    - `src/factory/adapters/zfs_snapshots.py`: `_execute` calls `run_or_raise` with `fault=functools.partial(SnapshotError, command)` and passes its own `accepted`.
    - `src/factory/adapters/podman_runs.py`: `_query` calls `run_or_raise` with `cwd=self._workspace` and `accepted=None`, and its fault is `partial(ContainerError, command)`. `run` keeps its own request with `cwd=ROOT`. The comment that sat on `_ROOT` moved onto that line.
    - `src/factory/adapters/power_off.py`: `power_off` calls `run_or_raise(fault=PowerOffError)`.
    - None of the three modules defines `_ROOT` any more. `make duplicates` reported `0 new, 41 known, 1 gone` in the first run.

    Main choice: the fault is a callable of the detail, and each wrapper turns its own error into one with `functools.partial`. Power-off is the exception. Its start-failure text is `cannot start <sudo>: <error>`, and the Interface keeps the error texts. So it catches a `PowerOffError` whose `__cause__` is an `OSError` and raises it again with that prefix, still chained from the `OSError`. Alternatives I rejected:
    - Dropping the prefix: it would change an error text.
    - Giving the helper a separate start-failure fault: it would change the Interface.
    - The human also turned down an extra `run` keyword for the tests' patch points (entry 11).

    Refactor: I read the whole diff once again and nothing needed changing.

    What the journal changed: "every existing test, unchanged" now has one exception, by the human's leave in entry 11. Four tests (three in `tests/adapters/test_zfs_snapshots.py`, one in `tests/adapters/test_podman_runs_results.py`) now patch `run_process` on `factory.adapters.process`. I left `## Description` as it is.

    Noticed, not touched: the tester flagged that the new `ast`-based test in `tests/adapters/test_run_or_raise.py` may belong in mutmut's list of structural tests in `pyproject.toml`. That list is the human's to change.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 1 gone
18. factory: started review as vm.
19. reviewer: no findings

    What I checked:
    - Criteria 1 to 3: `tests/adapters/test_run_or_raise.py` holds one parametrized test per criterion, and every row the criteria name is there. Criterion 1 covers success with `stdout == "ok\n"`, a refused status on stdout and on stderr (the `merge_stderr=True` side), `accepted=(0, 3)`, `accepted=None`, `exit status 1` when nothing is printed, a start failure (`__cause__` is an `OSError` and the text equals `str(__cause__)`), and the time limit through `no_end_detail`. Criterion 2 covers `cwd` left out and given. Criterion 3 checks, with `ast`, that no `_ROOT` is assigned and that `ProcessRequest(` is built only in `PodmanRuns.run`.
    - Interface: every rule of the Interface has its failing side tested (the refused status under the default `accepted` and under a given `accepted`, `OSError`, the time limit). The factory's `make check` after the coder was green (entry 17), with `duplicates: 0 new`.
    - Implementation: `run_or_raise` in `src/factory/adapters/process.py` follows the Interface. `ZfsSnapshots._execute` and `PodmanRuns._query` keep their error texts by passing `functools.partial(<Error>, command)`; `_query` passes `cwd=self._workspace` and `accepted=None`. `SystemctlPowerOff.power_off` keeps `cannot start <sudo>: <error>` by re-raising the start failure with that prefix, still chained from the `OSError`. That is the one way to keep the text without changing the Interface. `printed_output` imports nothing from `process`, so there is no import cycle.
    - Architecture: the helper sits in `adapters` beside `run_process`. No new tool call, layer import or silencing marker.
    - Docs criterion 5 still names what the documenter must write.

    description corrected: "every existing test, unchanged" -> "every existing test, unchanged, except four that now patch `run_process` on `factory.adapters.process`, where `run_or_raise` calls it, each keeping its name and what it checks (the human's leave, journal entry 11): three in `tests/adapters/test_zfs_snapshots.py` and `test_version_runs_under_two_minutes_by_default` in `tests/adapters/test_podman_runs_results.py`"

    Still open, outside this review: the Interface's closing line "No earlier test changes" is stale in the same way. A reviewer may correct only the Description, so I left that line, and entry 11 settles it. Whether the new `ast` test joins mutmut's structural tests in `pyproject.toml` is for the human to decide (entries 8 and 17).

    Earlier tests:
    - `tests/adapters/test_zfs_snapshots.py`: the human's leave, journal entry 11. The patch target moved from `zfs_snapshots` to `process`, and the import changed with it; nothing else in the file used `zfs_snapshots` as a module.
    - `tests/adapters/test_podman_runs_results.py`: the human's leave, journal entry 11. `test_version_runs_under_two_minutes_by_default` now also takes `monkeypatch` and patches `process.run_process` with the same `recorder`; the `recorder` fixture is unchanged.
20. factory: started docs as vm.
21. documenter: Changed `docs/project-guide/processes-and-checks.md`, `## Starting a process`: added a paragraph and list for `run_or_raise` and `ROOT`. It covers the signature, the request it builds, the three rules (OSError, time limit, exit status outside `accepted`), the three wrappers that use it (`ZfsSnapshots._execute`, `SystemctlPowerOff.power_off`, `PodmanRuns._query`), why `PodmanRuns.run` keeps its own request, and the test module. I did not run the new text as code. The paragraph has no runnable example; I checked it against the diff and the Interface. I ran no `make check`, because I changed only a document.

    Cross-read and found current: `docs/project-guide/stage-environment.md` (it mentions `_execute` as the runner for the zfs commands and the drop; still true), `README.md`, `docs/operator-guide.md` and `docs/decisions.md` (the criterion says none). A grep for `_ROOT` in the docs finds nothing stale.

    The code matches the Interface. I found nothing for the coder.

    Stale text I noticed but did not touch: the paragraph in the same section about the `run_process` boundary says that git, make and the `claude -p` runtime "each reach their tool through `run_process`". That is unrelated to this story and still broadly true.

    `check`: check: green (not run again: passed on tree ca4a7b67abec at 2026-10-27T03:50:21Z)
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok
22. factory: started smoke-test as vm.
23. smoke-tester: Smoke test: I ran both commands from the repository root exactly as written. Both met their `Expect:` lines. There are no findings.

    Command 1 (`uv run python -c '...run_or_raise...'`):
    ```
    Bytecode compiled 4164 files in 57ms
    boom
    /
    ```
    It met `Expect:` (two lines: `boom`; `/`). The first line is uv's own build message, not output from the script. The script's two lines are `boom` (the fault raised from a refused exit status, with the detail taken from the printed output) and `/` (the default `cwd=ROOT`). Exit status was 0.

    Command 2 (`grep -c '^_ROOT = ' ...` and `make duplicates 2>&1 | grep '^duplicates:'`):
    ```
    src/factory/adapters/zfs_snapshots.py:0
    src/factory/adapters/power_off.py:0
    src/factory/adapters/podman_runs.py:0
    duplicates: 0 new, 41 known, 1 gone
    ```
    It met `Expect:` (the three `:0` counts and a line that begins `duplicates: 0 new,`).

    Acceptance criteria, read again against the run:
    - Criteria 1 and 2: command 1 showed the refused-status row and the default directory. Nothing contradicts the other rows.
    - Criterion 3: command 2 shows no `_ROOT` in any of the three modules. A grep also shows that `PodmanRuns.run` passes `cwd=ROOT` (`src/factory/adapters/podman_runs.py:123`) and that the three wrappers call `run_or_raise`.
    - Criterion 4: I did not run `make check` in this stage. The factory's last run was green (entries 17 and 21).
    - Criterion 5: `docs/project-guide/processes-and-checks.md:60-66` describes `run_or_raise`, `ROOT`, its rules and the three wrappers that use it.

    Findings: none.
24. factory: done (pull request merged); cost: 10 runs, 22.2 min, 66 turns, 221519 tokens in (1356266 more from cache), 26287 out, $2.23
