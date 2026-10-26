---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 472
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-26T23:17:38.225983Z'
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
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-26T23:09:31.810606Z'
  stage: doing
  run: 92f4d80dab344316912deb17ce06d932
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-26T23:09:52.193951Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-26T23:10:36.311482Z'
  stage: review
  run: 79f426aa01494da8b617162166852fe9
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T23:10:56.764003Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-26T23:11:12.712775Z'
  stage: doing
  run: 7683845f5996404781c7c31907ce54bd
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T23:11:33.272616Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-26T23:17:17.409941Z'
  stage: tests
  run: 6efea6d6515c4bddba71915356ae7773
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-26T23:17:38.225983Z'
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
7. coder: Removed `output_abandoned` from `ProcessResult` in src/factory/adapters/process.py. The drain behaviour is unchanged.

   - `ProcessResult` loses the field. `run_process` and `run_streaming` no longer set it.
   - In `run_process`, the bounded read after the kill at the time limit is now a plain statement, `_read_bounded(reader, process, None, ended_at=...)`. Its outcome is no longer kept, but the read itself stays, so the output that arrives after the kill is still read for at most `PIPE_DRAIN`.
   - Docstrings: `run_process` now says a pipe still open after `PIPE_DRAIN` is closed and the call returns what it read. `run_streaming` says the same, followed by the existing rule about a last line without a line feed. Neither names a field.

   Main choice: I kept the private `_ReadOutcome` value `"abandoned"`. `_read_bounded` still has to tell the drain's end apart from the pipes closing, because `_read_to_exit` waits for the child's exit only on `"closed"`. I rejected merging it into `"closed"`: then the code would call `process.wait` on a child whose pipes are still held, which changes the control flow for no gain. The source test looks only for the string `output_abandoned`, so the private value does not trip it.

   Refactor: I read the diff once. Nothing needed changing.

   `make check`: green (test: green (158.9 s), check: green).

   Noticed but not touched:
   - docs/project-guide/processes-and-checks.md still names `output_abandoned` at lines 58, 65, 83 and 85. Updating it is the documenter's job under criterion 5.
   - The dead-code line for the field in security/duplicates-baseline.txt is the human's change 4, due after the merge.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 42 known, 1 gone
8. factory: started review as vm.
9. reviewer: 1. tests/adapters/test_process_result_fields.py:37-44 (`holder_file`): the fixture is a second copy of `holder_file` in tests/adapters/test_process_drain.py:71-78. Only the docstring wording differs; the body is the same (pid file under `tmp_path`, SIGKILL of a holder still running, `ProcessLookupError` suppressed). Fix: under the standing leave to move a shared test helper, the tester moves the fixture to tests/conftest.py and has both modules use it from there. Every test in test_process_drain.py keeps its name and what it checks.

   The rest of the review found no other gaps:
   - Criterion 1 is pinned by `test_the_result_has_no_output_abandoned_field`. It checks the field order and the `ValidationError` through a variable typed `type[BaseModel]`.
   - Criterion 2 is pinned by `test_the_call_reads_for_the_drain_after_the_child_ended`. Its three rows are run_process held, run_streaming held, and closed with exit status 3. `PIPE_DRAIN` is set to 1 s with monkeypatch, and each row is bounded by at least the drain and by `ROOMY_BOUND_SECONDS`.
   - Criterion 3 is pinned by `test_no_module_holds_the_name_of_the_removed_field`.
   - The coder's `make check` was green (journal entry 7).
   - src/factory/adapters/process.py drops the field and keeps the bounded read after the kill, now as a plain statement. The private `_ReadOutcome` value `"abandoned"` stays, and `_read_to_exit` still uses it to tell the drain's end apart from closed pipes.
   - The docstrings match the Interface. The architecture and security checks found nothing.
   - No other module under src or tests names the field.

   Earlier tests:
   - tests/adapters/test_process_drain.py: changed under the human's leave, decision 27 of feature.md. The seven named tests lost their `output_abandoned` assertion and kept their names. Two lost the `abandoned` parametrize column, which fed only that assertion; their row ids and other values are unchanged. `test_drain_is_five_seconds_and_output_is_not_abandoned_by_default` also lost the `ProcessResult` construction, which existed only for the removed assertion. All of this is within the leave.
10. factory: started doing as vm.
11. coder: The reviewer's one finding is a change to the tests, so I changed no code and am handing it to the tester under the standing leave in `CLAUDE.md` to move a shared test helper.

    The move: the `holder_file` fixture appears twice with the same body, once in tests/adapters/test_process_result_fields.py (lines 37-44) and once in tests/adapters/test_process_drain.py (lines 71-78). It writes a pid file under `tmp_path` and, after the test, SIGKILLs a holder that is still running, ignoring `ProcessLookupError`. The tester should:
    - move it to tests/conftest.py as one fixture;
    - delete both copies, so both modules use the shared one;
    - drop any import (`contextlib`, `os`, `signal`, `Iterator`) that no longer has a user in either module.

    Every test in test_process_drain.py keeps its name and checks the same thing.

    Why `tests` and not a fix of my own: the coder never edits tests, and the leave assigns this move to the tester.

    What I built: nothing new this round. The code from entry 7 stays as it was: `ProcessResult` without `output_abandoned`, in src/factory/adapters/process.py.

    Rejected: changing the code to get around the finding. The duplication is in the tests only, so a code change would not resolve it.

    The journal did not change what the task means, so the Description stays as it is.

    Noticed, not touched: docs/project-guide/processes-and-checks.md still names `output_abandoned`; updating it is the documenter's work under criterion 5.
12. factory: started tests as vm.
13. tester: Moved the `holder_file` fixture into tests/conftest.py, as the coder asked in entry 11 after the reviewer's finding in entry 9. I did this under the standing leave in `CLAUDE.md` to move a shared test helper.

    - tests/conftest.py now holds one `holder_file` fixture. Its body is the same as both copies had: it yields `tmp_path / "holder.pid"`, then kills any holder still running with SIGKILL and ignores `ProcessLookupError`. conftest.py also gained the `contextlib` and `signal` imports it needs.
    - tests/adapters/test_process_result_fields.py: removed its copy, plus the `contextlib`, `os`, `signal` and `Iterator` imports that nothing else in the file used.
    - tests/adapters/test_process_drain.py (an earlier story's test file, changed under the standing leave): removed its copy, plus the `contextlib`, `os`, `signal` and `Iterator` imports that nothing else in the file used. `Callable` is still imported. Every test keeps its name and checks the same thing.

    Nothing else in `tests/` defines `holder_file`, so the shared fixture is the only one.

    The criterion → test mapping has not changed since entry 5:
    - criterion 1: tests/adapters/test_process_result_fields.py::test_the_result_has_no_output_abandoned_field
    - criterion 2: tests/adapters/test_process_result_fields.py::test_the_call_reads_for_the_drain_after_the_child_ended
    - criterion 3: tests/adapters/test_process_result_fields.py::test_no_module_holds_the_name_of_the_removed_field

    No files were created this round. Every module imported.

    `make lint` is green. `make test` is green: test: green (157.6 s).

    `lint`: lint: green (0.2 s)
    `test`: test: green (153.7 s)
14. factory: started doing as vm.
