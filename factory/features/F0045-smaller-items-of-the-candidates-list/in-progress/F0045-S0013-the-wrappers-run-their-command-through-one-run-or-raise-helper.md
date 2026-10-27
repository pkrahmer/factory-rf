---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 478
comments_read: [6432903366, 6433141030]
handed_over: null
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
---

# The wrappers run their command through one run-or-raise helper

<!-- proposed by feature acceptance of 2026-10-27; refine before starting -->

## Description

S0008 (the factory powers its machine off after an idle stretch) wrote `SystemctlPowerOff.power_off` as a third copy of one block: build a `ProcessRequest` at `/` with no environment, the wrapper's time limit and merged standard error, run it, and turn a program that cannot start, the time limit reached, or an exit status the wrapper does not accept into the wrapper's own error, with the detail `failure_detail` or `no_end_detail` of `factory.adapters.printed_output` gives. `ZfsSnapshots._execute` holds the same block and `PodmanRuns._query` the same without the exit check, and each of the three modules defines its own `_ROOT = Path("/")`. `make duplicates` has reported the two similarities as `2 new` since S0008, and the human recorded them in S0008's journal (entry 33) "for a later tidy-up". This story writes the block once, in `factory.adapters.process`, and the three wrappers call it with their own error. What stays: every wrapper's commands, errors, error texts and time limits; `run_process`, `run_streaming` and the drain; `PodmanRuns.run`, which passes the launch's environment and keeps its own request; every existing test, unchanged.

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
