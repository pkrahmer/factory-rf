---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 250
comments_read: [6259541572]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T04:23:02.110011Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T04:16:36.001707Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T04:16:36.007769Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T04:16:55.230625Z'
  stage: intake
  run: 6b9747a9275848fb81f16b9634a9d198
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T04:18:11.974084Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T04:18:29.536723Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T04:18:58.053646Z'
  stage: intake
  run: 92678775aefc4fc585dc35341555f978
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T04:19:18.008910Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T04:22:41.833023Z'
  stage: tests
  run: 4f3ad73be4904dbe9135b7d731828d31
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T04:23:02.110011Z'
  stage: doing
---

# The process module streams a run's output and stops it on a line

## Description

`run_process` hands a caller the output of a process only when the process has ended. The opencode runtime cannot wait for that: opencode has no budget flag, so the factory must sum the cost of each step as the events arrive and stop the run when it passes the budget (S0006), and a provider's spend limit may leave a run waiting for input it never gets, until the stage's `time_limit` (S0006). This story adds `run_streaming` to the one process module: it starts a process as `run_process` does, hands every line of standard output and of standard error to a callback while the process runs, and kills the whole process group at once when the callback says stop. The time limit, the process group and the result stay as they are, and the result says whether the callback stopped the run. `run_process` is unchanged, and the module keeps its one `Popen` line, so the suppression markers and the searches over the package stay as they are. Nothing uses `run_streaming` yet; the opencode runtime does from S0004.

## Interface

`factory.adapters.process` (`adapters`):

```python
Stream = Literal["stdout", "stderr"]

class ProcessResult(BaseModel):
    ...
    stopped: bool = False   # new, last

def run_streaming(request: ProcessRequest, on_line: Callable[[Stream, str], bool]) -> ProcessResult: ...
```

- `run_streaming` starts `request.argv` as `run_process` does: without a shell, standard input from `/dev/null`, in its own session, in `request.cwd` with `request.env`; a program that cannot be started raises its `OSError`, as there.
- It calls `on_line(stream, line)` once for every line the process writes to either stream, as the line arrives, in each stream's own order: the line without its line feed, decoded as UTF-8 with replacement; a last line without a line feed is passed when its stream ends. With `request.merge_stderr`, every line comes as `"stdout"`. The calls come one at a time from the calling thread.
- When `on_line` returns `True`, the process group is killed at once and no further line is passed; the result has `stopped=True`, `exit_status=None` and `timed_out=False`.
- At the time limit the process group is killed as by `run_process`: `timed_out=True`, `exit_status=None`, `stopped=False`, and no line read after the kill is passed.
- When `on_line` raises, the process group is killed and the exception propagates.
- `stdout` and `stderr` of the result hold the text read from each stream, line feeds included, up to the end, the stop or the kill (with `merge_stderr`, `stderr` is `""`); `duration` is the time from the start to the result.
- A process that ends by itself gives `stopped=False`, `timed_out=False` and its exit status, after `on_line` has had every line.
- `run_process` behaves as today. The module keeps exactly one line with `subprocess.Popen(`, shared by both functions, so `tests/test_process_search.py` passes unchanged; `stopped` defaults to `False`, so every `ProcessResult` built today stays valid.

Tests (the tester writes them): `tests/adapters/test_process_streaming.py`, with real Python child processes like `tests/adapters/test_process.py`; the waits for a killed child use `is_gone` from `tests/process_support.py`. The helper `_python` of `tests/adapters/test_process.py`, which the new module needs too, moves to `tests/process_support.py` as `python_argv` under the standing leave of `CLAUDE.md` (*Tests*), and `tests/adapters/test_process.py` uses it from there; each of its tests keeps its name and checks the same thing.

## Acceptance criteria

1. A child that prints `one` and `two` on standard output and `err` on standard error and exits 3 gives the calls `("stdout", "one")`, `("stdout", "two")` and `("stderr", "err")`, the stdout calls in that order and every call on the test's own thread (`threading.get_ident()`), and a result with exit status 3, `stdout` `"one\ntwo\n"`, `stderr` `"err\n"`, `stopped` and `timed_out` false.
2. A last line without a line feed is passed, and a line with bytes that are not UTF-8 is passed with the replacement character (rows).
3. A child that prints `go`, then sleeps 60 seconds, with a callback that returns `True` for `go`: the call returns within 20 seconds, with `stopped` true, `exit_status` `None`, `timed_out` false and `stdout` `"go\n"`; a grandchild the child started is gone (`is_gone`), and no line the child would print after the sleep is passed. A further row: a child that prints `go` and then `later` at once, with a callback that returns `True` for `go`, never gets `later` passed, also when both lines were read in the same chunk.
4. A callback that returns `True` for a line on standard error stops the run as in criterion 3.
5. A child that prints `started` and sleeps 60 seconds under a time limit of 3 seconds, with a callback that never stops: the call returns within 20 seconds with `timed_out` true, `stopped` false, `exit_status` `None` and `started` in `stdout`; and a child that prints `late` after a sleep longer than the limit never has `late` passed to the callback.
6. A callback that raises `RuntimeError` on the first line: the call raises it, and the child, which would sleep 60 seconds after that line, is gone.
7. With `merge_stderr=True`, a line on standard error comes as `("stdout", ...)` in the order written, and the result's `stderr` is `""`.
8. A missing executable raises `FileNotFoundError` and calls the callback never.
9. Lines arrive while the child runs: a child that prints `first`, then waits until a file appears, then prints `second`, with a callback that writes that file when it gets `first`, ends with both lines passed (no sleep in the test).
10. `run_streaming` starts the child as `run_process` does (rows): a child that prints its working directory gives `request.cwd`; a child that prints one variable of `request.env` gives its value; a child that reads standard input gets end of file at once.
11. `duration` of the result is at least the child's known run time (a child that prints a line and exits after a short wait) and below an upper bound with room above it.
12. `run_process` and every test of `tests/adapters/test_process.py` behave as before, and the module holds one `subprocess.Popen(` line.
13. `make check` stays green.
14. docs: `docs/project-guide.md`, the process module: `run_streaming` hands each line to a callback while the process runs and kills the process group when the callback says stop, for a runtime that must act on its output as it comes (the opencode runtime's budget and provider limit); `ProcessResult.stopped`. `docs/decisions.md`: an entry *A run's output can be streamed by the one process module*, dated with the story, with the reasons of the feature's decision 5.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import sys
import time
from pathlib import Path
from factory.adapters.process import ProcessRequest, run_streaming

seen = []
def on_line(stream, line):
    seen.append(f"{stream}:{line}")
    return line == "stop"

started = time.monotonic()
result = run_streaming(ProcessRequest(argv=["/bin/sh", "-c", "echo one; echo two >&2; sleep 1; echo stop; sleep 60; echo never"], cwd=Path(sys.argv[1])), on_line)
print(" ".join(sorted(seen)))
print(result.stopped, result.exit_status, result.timed_out, time.monotonic() - started < 20)
EOF
```
Expect: two lines, `stderr:two stdout:one stdout:stop` and `True None False True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says `run_streaming` starts the process "as `run_process` does": without a shell, standard input from `/dev/null`, in `request.cwd` with `request.env`, in its own session. No criterion tests any of these for `run_streaming`. Criterion 10 only covers `run_process`'s existing tests, and the smoke test uses `cwd` but never reads it back. Two coders could wire these differently and still pass every test. Options: (a) add a criterion with rows: a child that prints its working directory, one variable from `request.env` and whether standard input is at end of file (read returns empty at once). I would choose this. (b) Drop the clause and say that `run_streaming` shares `run_process`'s start code, which is a structural claim and still needs a test.
   2. The Interface states "`duration` is the time from the start to the result", and no criterion tests it. Suggested: a criterion that `duration` is at least the child's known run time, for example a child that prints a line and exits after a short wait, and below an upper bound with room above it. Or drop the clause.
   3. The Interface says that after a stop "no further line is passed". Criterion 3 covers this only for a line that the child prints after a 60-second sleep, which the kill prevents anyway. It does not cover a child that prints several lines in a burst after the stop line. Suggested: add a row where the child prints `go` and then `later` at once, and the callback stops on `go`; `later` is never passed. Please confirm that this is the intended meaning, since lines already read in the same chunk are the ambiguous case.
   4. The time-limit clause says "no line read after the kill is passed", and criterion 5 has no check for it. Suggested: add to criterion 5 that no call has a line printed after the limit, for example a child that prints `late` after a sleep longer than the limit.
   5. The Interface says an exception from the callback propagates. The criterion for the other side is missing: the callback raising on a line on standard error. Optional; I would accept it as is if you say that stdout alone is enough.

   Everything else checked out. The module and signatures are concrete. The smoke test is runnable and its `Expect:` line is checkable. The story is in the adapters layer, within the feature's scope, and it is not in "Out of scope".
4. 2026-10-19 human: 1. (a): add the criterion with the rows (working directory, one variable from `request.env`, standard input at end of file).
   2. Yes: add the `duration` criterion (at least the child's known run time, below an upper bound with room above it).
   3. Yes, that is the intended meaning: after the callback stops on a line, no further line is passed, also not one already read in the same chunk. Add the row (`go` then `later` at once; `later` is never passed).
   4. Yes: add to criterion 5 that no line printed after the limit is passed (`late` after a sleep longer than the limit).
   5. Standard output is enough; leave it as is.
5. factory: started intake as self.
6. intake: accepted
   - Interface: `factory.adapters.process` names `Stream`, `ProcessResult.stopped` and `run_streaming(request, on_line)` concretely. Every clause has a criterion, including the start conditions, `duration` and the burst after a stop (see the edits below).
   - Criteria: each is testable by one test function. Each rule has both sides: stop vs. natural end (1, 3), time limit (5), raise (6), merge (7), missing executable (8), lines arriving while the child runs (9). The human's answer in journal entry 4 was carried in as follows. (1) New criterion 10: cwd, env and stdin at end of file, as rows. (2) New criterion 11: `duration`. (3) A burst row (`go` then `later`) added to criterion 3. (4) `late` after a sleep longer than the limit added to criterion 5. (5) Left as is, stdout only. The closing criteria were renumbered: `run_process` unchanged is now 12, `make check` 13 and `docs:` 14.
   - Smoke test: runnable, and the `Expect:` lines can be checked against the output.
   - Architecture: it sits in the adapters layer, in the one process module, and keeps the single `Popen` line. No new wrapper or dependency.
   - Scope: within F0020's scope (S0003 in the feature's Scope and decision 5), and not in "Out of scope".
7. factory: started tests as self.
8. tester: Wrote the tests for `run_streaming` and `ProcessResult.stopped`, using real Python child processes. Each child that has to be killed starts a grandchild, and `is_gone` waits for it to end.

   - criterion 1: tests/adapters/test_process_streaming.py::test_every_line_of_both_streams_reaches_the_callback_on_the_calling_thread
   - criterion 2: tests/adapters/test_process_streaming.py::test_last_line_and_undecodable_bytes_reach_the_callback (rows: no-line-feed, not-utf-8)
   - criterion 3: tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_output_kills_the_group_at_once (rows: before-a-sleep, which checks `stdout == "go\n"`; same-chunk, which writes `go\nlater\n` in one write and does not check `stdout`, because the criterion leaves it open for that row)
   - criterion 4: tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_error_kills_the_group_at_once
   - criterion 5: tests/adapters/test_process_streaming.py::test_child_is_killed_at_the_time_limit_and_no_later_line_is_passed (a 3 s limit, with `late` printed after a 60 s sleep)
   - criterion 6: tests/adapters/test_process_streaming.py::test_callback_that_raises_kills_the_child_and_the_error_propagates (the child's first line is its pid)
   - criterion 7: tests/adapters/test_process_streaming.py::test_merged_standard_error_comes_as_standard_output_in_the_order_written
   - criterion 8: tests/adapters/test_process_streaming.py::test_missing_executable_raises_file_not_found_without_a_call
   - criterion 9: tests/adapters/test_process_streaming.py::test_lines_reach_the_callback_while_the_child_runs (the child polls for the file; the test does not sleep; a 20 s time limit keeps it from hanging when the output is not streamed)
   - criterion 10: tests/adapters/test_process_streaming.py::test_child_starts_as_run_process_starts_it (rows: working-directory, environment, standard-input)
   - criterion 11: tests/adapters/test_process_streaming.py::test_duration_covers_the_child_run_time (at least 0.5 s, below 20 s)
   - criterion 12: tests/adapters/test_process_streaming.py::test_run_process_shares_the_one_popen_line_and_reports_no_stop, plus the unchanged tests of tests/adapters/test_process.py and tests/test_process_search.py
   - criteria 13 and 14: no test (`make check`, docs).

   Files created: tests/adapters/test_process_streaming.py.
   Earlier test files changed under the standing leave to move a shared test helper (CLAUDE.md, *Tests*), as the Interface asks:
   - tests/process_support.py: gains `python_argv`, moved from `_python`.
   - tests/adapters/test_process.py: uses `python_argv` from there; every test keeps its name and checks the same thing.

   `make test`: the run could not import tests/adapters/test_process_streaming.py (an ImportError, because `Stream` and `run_streaming` do not exist yet in `factory.adapters.process`). This is the expected red. `make lint`: green.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/adapters/test_process_streaming.py - ImportError while importing ...
9. factory: started doing as self.
