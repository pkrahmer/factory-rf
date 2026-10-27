---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 478
comments_read: [6432903366]
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
