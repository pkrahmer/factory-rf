---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 472
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-26T23:03:22.092138Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T22:55:43.641634Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T22:55:43.647154Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T22:56:06.563941Z'
  stage: intake
  run: 6d069c2ca73140bd8926ab77c11a4c74
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T22:56:26.624023Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T23:03:01.328631Z'
  stage: tests
  run: 7019af26f9dd48f997a1c0b7c764978b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T23:03:22.092138Z'
  stage: doing
---

# The process result no longer says that its output was abandoned

## Description

Since F0040-S0005 the process module reads a child's output for at most `PIPE_DRAIN` (five seconds) after the child has ended or was killed, so that a process left holding a pipe cannot hold the call; it then closes the pipes and marks the result `output_abandoned=True`. No caller under `src/factory` reads that field (F0040-A0002, note 4c), and `security/duplicates-baseline.txt` carries it as accepted dead code. After F0044 the host starts only git, `zfs`, `podman` and, in the suite, `make`, and nothing reads the field there either. This story removes the field and keeps the behaviour: `run_process` and `run_streaming` still stop reading `PIPE_DRAIN` after the child's end or kill, close the pipes and return what they read, with the same exit status, `timed_out` and `stopped` as today (decision 5 of `feature.md`). The baseline's line goes by the human's change 4 after the merge. What stays: `PIPE_DRAIN` and its value, the polling of the child's end, the kill at the time limit, every other field of `ProcessResult`.

## Interface

`factory.adapters.process` (`adapters`): `ProcessResult` loses the field `output_abandoned`:

```python
class ProcessResult(BaseModel):
    exit_status: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration: timedelta
    stopped: bool = False
```

- `run_process` and `run_streaming` build no such field; their docstrings say that a pipe still open after `PIPE_DRAIN` is closed and the call returns, without naming a field.
- Nothing else in the module changes in behaviour.

Tests (the tester changes them; the leave is decision 27 of `feature.md`): `tests/adapters/test_process_drain.py`: `test_a_child_that_ended_beside_a_holder_returns_after_the_drain`, `test_pipes_that_close_within_the_drain_give_the_whole_output`, `test_the_read_after_the_kill_is_bounded_by_the_drain`, `test_streaming_ended_by_a_kill_does_not_abandon_output`, `test_drain_is_five_seconds_and_output_is_not_abandoned_by_default`, `test_a_limit_during_the_drain_times_the_call_out` and `test_the_last_line_without_a_line_feed_is_not_passed_after_the_drain` lose their assertion on `output_abandoned`; each keeps its name, its rows and every other assertion (the duration bounds, the output read, the exit status, `timed_out`). New tests at the tester's choice, for example `tests/adapters/test_process_result_fields.py`.

## Acceptance criteria

1. The field is gone (one test): `ProcessResult.model_fields` is exactly `exit_status`, `stdout`, `stderr`, `timed_out`, `duration`, `stopped`, in that order; constructing it through a variable typed `type[BaseModel]` with `output_abandoned=True` raises `ValidationError`.
2. The drain stays (rows of one parametrized test, `PIPE_DRAIN` set to one second with `monkeypatch.setattr`, the waits bounded by `ROOMY_BOUND_SECONDS` of `tests/time_limits.py`): a child that prints `a` and ends while a grandchild it started holds the pipe and sleeps 60 seconds returns from `run_process` with exit status 0, `timed_out` false, `stdout` starting `a`, after at least the drain and within the bound; the same through `run_streaming` passes the line `a` to the callback and returns the same way; a child that prints two lines and ends with exit status 3, its pipes closing at its end, returns both lines and exit status 3.
3. The source (one test reading `src/factory`): no module holds the string `output_abandoned`.
4. `make check` stays green.
5. docs: `docs/project-guide/processes-and-checks.md`, `## Starting a process`: `ProcessResult` without `output_abandoned`, and *Reading after the child's end* says that the call closes the pipes and returns, without the field. `docs/decisions.md`: the entry "A call stops reading five seconds after its own process ended" gains one closing line: "The field `output_abandoned`, which no caller read, went with v1.2 F0045-S0007; the drain stays." `docs/operator-guide.md`, `README.md`: none (no operator-visible change).

## Smoke test

```bash
uv run python -c 'from factory.adapters.process import ProcessResult; print(list(ProcessResult.model_fields))'; grep -rl 'output_abandoned' src/factory --include='*.py' | wc -l
```
Expect: two lines: `['exit_status', 'stdout', 'stderr', 'timed_out', 'duration', 'stopped']`; `0`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: `factory.adapters.process.ProcessResult` is given with its full field list. The module, `PIPE_DRAIN`, `run_process` and `run_streaming` exist as named. `output_abandoned` occurs in 4 places in `src/factory/adapters/process.py` and 7 in `tests/adapters/test_process_drain.py`. That matches the seven tests decision 27 names, and the human's leave covers them. The docstring statement has no test of its own, because wording is not testable. The drain behaviour it describes is covered by criterion 2.
   Criteria: all four testable by one test function each. 1 checks the field order and the `ValidationError` on the removed field. 2 has rows for the passing side (output within the drain, exit status 3) and for the drain side (a holder that outlives the child, through `run_process` and through `run_streaming`). The bounds are given: at least the drain, within `ROOMY_BOUND_SECONDS`. 3 is a source search. The kill and `timed_out` paths are kept by the seven existing tests, which keep their other assertions.
   Smoke test: one command with two printed lines. It runs no pytest, so the `-q` rule does not apply. `Expect:` gives exact output that can be compared.
   Architecture: the change stays inside the adapters layer in `factory.adapters.process`, the one module that starts processes, and adds no layer crossing. Docs go to the paths the docs criterion names.
   Scope: this is S0007 of F0045, matching the feature's scope line and decision 5. The baseline line is the human's change 4 and the story leaves it alone. Nothing in the feature's "Out of scope" is touched.
4. factory: started tests as vm.
5. tester: Wrote the tests for the field removal and changed the seven drain tests under decision 27's leave.

   - criterion 1: tests/adapters/test_process_result_fields.py::test_the_result_has_no_output_abandoned_field
   - criterion 2: tests/adapters/test_process_result_fields.py::test_the_call_reads_for_the_drain_after_the_child_ended. It has three rows: run_process-held, run_streaming-held and run_process-closed. `PIPE_DRAIN` is set to one second with monkeypatch. The held rows wait at least the drain; every row must return within `ROOMY_BOUND_SECONDS`.
   - criterion 3: tests/adapters/test_process_result_fields.py::test_no_module_holds_the_name_of_the_removed_field. It is a text search of `src/factory` through `search_support.modules_matching` with `root=source_search.SRC`.
   - criterion 4 (`make check`) and criterion 5 (docs): no test, as these belong to the later stages.

   Files created: tests/adapters/test_process_result_fields.py.

   Earlier test file changed, under the leave in decision 27 that the Interface names: tests/adapters/test_process_drain.py.
   - These seven tests lost their `output_abandoned` assertion: test_a_child_that_ended_beside_a_holder_returns_after_the_drain, test_pipes_that_close_within_the_drain_give_the_whole_output, test_the_read_after_the_kill_is_bounded_by_the_drain, test_streaming_ended_by_a_kill_does_not_abandon_output, test_drain_is_five_seconds_and_output_is_not_abandoned_by_default, test_a_limit_during_the_drain_times_the_call_out and test_the_last_line_without_a_line_feed_is_not_passed_after_the_drain.
   - In two of them, test_the_read_after_the_kill_is_bounded_by_the_drain and test_a_limit_during_the_drain_times_the_call_out, the parametrize column `abandoned` fed only that assertion, so it went. Each row keeps its id and its other values.
   - test_drain_is_five_seconds_and_output_is_not_abandoned_by_default built a `ProcessResult` only to check the field's default. The construction went with that assertion, and the `PIPE_DRAIN == 5 s` assertion stays. The now unused `ProcessResult` import went too.
   - Every test keeps its name and all its other assertions.

   Run (`make test`): two tests fail, as intended.
   - The field-list test fails because `model_fields` still holds `output_abandoned`.
   - The source test fails because it finds `adapters/process.py`.
   - The criterion-2 test already passes, because the drain behaviour exists today and the criterion only pins that it stays.
   - Every module imported; nothing was missing.

   `make lint` is green. The new test takes its parameters keyword-only (`*,`), as other tests here do, to satisfy PLR0917.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/adapters/test_process_result_fields.py::test_no_module_holds_the_name_of_the_removed_field - AssertionError: assert ['adapters/process.py'] == []
6. factory: started doing as vm.
