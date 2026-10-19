---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 250
comments_read: [6259541572]
handed_over: null
claim: null
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
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-19T04:26:27.764390Z'
  stage: doing
  run: 3f5c5d10c2e94a6788311ce0dc131014
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-19T04:26:47.845595Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-19T04:28:18.534197Z'
  stage: review
  run: 415d1faa2d38438ca1d19f23dc4d0eb6
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-19T04:28:39.161355Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-19T04:29:00.773661Z'
  stage: doing
  run: 9ad038bf0ea649fe80f6f572dcbb3820
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-19T04:29:20.512660Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-19T04:31:02.769747Z'
  stage: tests
  run: 3a87dab5e1da4296bf4f32d1d2c74d50
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-19T04:31:23.359998Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-19T04:33:11.687891Z'
  stage: doing
  run: 2fca8ecc14b54f2d9f8b11552c757140
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-19T04:33:31.911922Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-19T04:34:34.951395Z'
  stage: review
  run: 5e5370a3222d4d6eabd93b2fe41044a6
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-19T04:34:55.037187Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-19T04:36:06.802755Z'
  stage: docs
  run: 7c183c5f87e24198a44df7c4c22043f5
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-19T04:36:26.962373Z'
  stage: smoke-test
- number: 24
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T04:36:53.600527Z'
  stage: smoke-test
  run: 214e01b6ad80448bbb017e3175a6b3c2
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
13. A child that closes its standard output and standard error and then sleeps 60 seconds, under a time limit of 3 seconds: the call returns within 20 seconds with `timed_out` true, `stopped` false and `exit_status` `None`, and the child is gone (`is_gone`).
14. `make check` stays green.
15. docs: `docs/project-guide.md`, the process module: `run_streaming` hands each line to a callback while the process runs and kills the process group when the callback says stop, for a runtime that must act on its output as it comes (the opencode runtime's budget and provider limit); `ProcessResult.stopped`. `docs/decisions.md`: an entry *A run's output can be streamed by the one process module*, dated with the story, with the reasons of the feature's decision 5.

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
10. coder: Added `run_streaming` and `ProcessResult.stopped` in `src/factory/adapters/process.py`. `make check` is green.

    **What I built** (all in `src/factory/adapters/process.py`):
    - `Stream = Literal["stdout", "stderr"]`.
    - `ProcessResult.stopped: bool = False`, added as the last field.
    - `_start(request)` holds the module's one `subprocess.Popen(` line, with its two suppression markers, and both `run_process` and `run_streaming` call it. Apart from that, `run_process` is unchanged.
    - `_LineReader` reads both pipes through `selectors.DefaultSelector`, using `os.read` chunks of 64 KiB. It keeps each stream's bytes and splits off complete lines on `\n` before decoding them, so a UTF-8 character split across two chunks stays whole. It passes a last line with no line feed when its stream reaches end of file. It stops at the first line for which the callback returns `True` (the `any(...)` short-circuits), so a later line in the same chunk is never passed.
    - `_read_until_end` loops until every stream has ended, the deadline passes, or the callback says stop. `_wait_for_exit` then waits for the exit status within the remaining time.
    - `run_streaming` kills the process group on a stop or a timeout, and on any exception from the callback, which it then re-raises.

    **Main choice:** a selector loop on the calling thread. That satisfies "the calls come one at a time from the calling thread" directly, and a stop takes effect between two lines. I rejected two reader threads feeding a queue: it needs thread handoff and cleanup and gains nothing here. Once a stop or a timeout kills the group, the reader stops reading. So `stdout` and `stderr` hold only what was read before that, as the Interface says. `run_process`, by contrast, collects output after the kill.

    **Refactor pass:** renamed the reader's `open`/`read` to `has_open_stream`/`read_bytes`. Nothing else needed changing.

    **Noticed, not touched:**
    - `make duplicates` shows 1 new finding: vulture marks `run_streaming` as unused (60% confidence). That is expected, because nothing calls it until S0004.
    - It also lists a "gone" dead-code entry for `src/factory/application/hosting.py` `close`, which this story did not touch.
    - `ProcessResult` is not in the records contract, so there was no schema to regenerate.
    - No change to the description was needed: the human's answer was already worked into it at intake.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 35 known, 4 gone
11. factory: started review as self.
12. reviewer: 1. Criterion 13 added: it needs its test. Location: `src/factory/adapters/process.py`, `_wait_for_exit` and its `subprocess.TimeoutExpired` branch, which `run_streaming` reaches when a child has closed both of its streams but keeps running. This is one path of the Interface's time-limit rule, and no criterion or test reaches it. Criterion 5 only covers a child whose streams stay open. If that branch waited without a timeout, or did not kill the group, every test would still pass, and `run_streaming` would run past `time_limit`. The fix needs no change under `src/`. The tester adds a test in `tests/adapters/test_process_streaming.py`. The child closes fd 1 and fd 2 (`os.close`) and sleeps 60 s under a 3 s limit. The test asserts that the call returns within 20 s with `timed_out` true, `stopped` false and `exit_status` `None`, and that `is_gone` holds for the child's pid, which the child writes to a file before it closes its streams. The closing criteria are renumbered: `make check` is now 14 and `docs:` is 15.

    Read and found sound: every other criterion (1–12) has a test that checks what it names. This includes the same-chunk row of 3, which writes `go\nlater\n` in one write, and the standard-input row of 10, which would hang until its limit if stdin were not `/dev/null`. The coder's entry 10 reports `make check` green. On architecture and security (groups 2 and 3), the single `subprocess.Popen(` line and its markers moved unchanged into `_start`, and no new suppression marker was added. Groups 4 and 5 were not judged this round: group 1 failed first, and the checklist stops at the first failing group.

    Earlier tests:
    - tests/adapters/test_process.py: changed under the standing leave to move a shared test helper (CLAUDE.md, *Tests*). The only change moves `_python` to `process_support.python_argv` and drops the now-unused `import sys`. Every test keeps its name and checks the same thing.
    - tests/process_support.py: none needed. The file only gains `python_argv`, and its existing `is_gone` and `GONE_WITHIN_SECONDS` are unchanged.
13. factory: started doing as self.
14. coder: This round changes no code. The reviewer's only finding in entry 12 adds criterion 13, which needs only its test.

    Criterion 13: a child closes its standard output and standard error and then sleeps 60 s, under a 3 s time limit. The call returns within 20 s with `timed_out` true, `stopped` false and `exit_status` `None`, and the child is gone (`is_gone`).

    - **Test to add:** in `tests/adapters/test_process_streaming.py`, the test the reviewer describes. The child writes its pid to a file in `tmp_path`, closes fd 1 and fd 2 with `os.close`, then sleeps 60 s.
    - **Existing tests:** none of them reaches this path. I checked: no test in that file closes the child's streams.
    - **Why the code should already pass:** the path runs through `_wait_for_exit` in `src/factory/adapters/process.py`. That function calls `process.wait` with the remaining time and returns `timed_out=True` on `subprocess.TimeoutExpired`. `run_streaming` then kills the process group (`_kill_group`) and returns `exit_status=None`. If the new test fails, the next doing round fixes the code.

    The description is already up to date: criterion 13 and the renumbered closing criteria 14 and 15 are in it. Since no file changed, I did not run `make check` this round. It was green after entry 10.

    Noticed but not touched: as entry 10 says, `make duplicates` reports `run_streaming` as unused. That is expected, because nothing calls it until S0004.
15. factory: started tests as self.
16. tester: Wrote the test for criterion 13, which the reviewer added (entry 12). The coder's entry 14 names it. No existing test was edited.

    - criterion 13: tests/adapters/test_process_streaming.py::test_child_that_closed_its_streams_is_killed_at_the_time_limit. The child writes its own pid to a file in `tmp_path`, then closes fd 1 and fd 2 with `os.close` and sleeps 60 s, under a 3 s `time_limit`. The test checks four things:
      - the call returns within 20 s;
      - `timed_out` is true, `stopped` is false and `exit_status` is `None`;
      - `is_gone` holds for the child's pid.

    The mapping of criteria 1–12 is unchanged from entry 8. Criteria 14 (`make check`) and 15 (docs) have no test.

    Files changed: tests/adapters/test_process_streaming.py, which gains the one test above. I created no new files. Every module imported: the code under test already exists, so the new test passes with the current `run_streaming`, as entry 14 expected.

    `make test`: test: green (41.5 s). `make lint`: green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (37.5 s)
17. factory: started doing as self.
18. coder: Round 1 changes no code. In entry 16 the tester added tests/adapters/test_process_streaming.py::test_child_that_closed_its_streams_is_killed_at_the_time_limit for the criterion 13 the reviewer added. It passes against the existing `run_streaming` in `src/factory/adapters/process.py`, as entry 14 expected. That path goes through `_wait_for_exit`: `subprocess.TimeoutExpired` gives `timed_out=True`, then `_kill_group` runs and `exit_status` is `None`. `make check`: check: green.

    What I built is unchanged from entry 10, all in `src/factory/adapters/process.py`:
    - `Stream` and `ProcessResult.stopped`.
    - `_start`, which holds the module's one `Popen` line and serves both functions.
    - `_LineReader`, a selector loop.
    - `_read_until_end`, `_wait_for_exit` and `run_streaming`.

    The main choice also stands from entry 10: a selector loop on the calling thread. I rejected reader threads feeding a queue.

    Refactor pass: nothing to change, because this round has no diff of its own.

    Journal: the description already holds criterion 13 and the renumbered 14 and 15, so I did not rewrite it.

    Noticed, not touched: `make duplicates` still reports `run_streaming` as unused (vulture). That is expected until S0004 calls it.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 35 known, 4 gone
19. factory: started review as self.
20. reviewer: no findings

    What I read: the work item, `git diff main...HEAD -- . ':!factory'` (`src/factory/adapters/process.py`, `tests/adapters/test_process_streaming.py`, `tests/adapters/test_process.py`, `tests/process_support.py`) and all of `src/factory/adapters/process.py`.

    - Acceptance criteria (group 1): each of criteria 1–13 has a test that checks what the criterion names. This includes criterion 13, which round 0 added: `test_child_that_closed_its_streams_is_killed_at_the_time_limit` reaches the `subprocess.TimeoutExpired` branch of `_wait_for_exit`. The failing sides of the Interface's rules are covered: the missing executable (8), the callback that raises (6), and the time limit hit (5, 13) against a run that ends inside its limit (9, 10). Coder entry 18 reports `make check` green.
    - Architecture and security (groups 2 and 3): the change stays inside the one process module in `factory.adapters`. The only new import is `selectors` from the standard library. The single `subprocess.Popen(` line moved into `_start` with its two existing markers and no new marker.
    - Quality (group 4): `_decode`, `_seconds` and `_kill_group` are reused, not copied. Kill on stop, timeout and exception is correct, and so is the end-of-stream handling. The read loop drops the rest of a chunk once the callback says stop. I noticed docstrings on three private names (`_LineReader`, `_read_until_end`, `_wait_for_exit`). I did not count them as a finding: the module already has such docstrings elsewhere, and the one on `_read_until_end` gives the order of its returned tuple, which the signature does not. `make duplicates` reports one new item, vulture flagging `run_streaming` as unused, which is expected until S0004 calls it.
    - Work item hygiene (group 5): entry 10 explains the main choice, a selector loop on the calling thread, and the alternative it rejected, reader threads feeding a queue. The Description matches what was built, and the docs criterion (15) still says what the reader must know.

    Notes:
    1. `tests/adapters/test_process_streaming.py:106` and `:128`: stopping on standard output and stopping on standard error are two sides of one rule but are written as two test functions; they could be rows of one parametrized test.

    Earlier tests:
    - tests/adapters/test_process.py: changed under the standing leave to move a shared test helper (CLAUDE.md, *Tests*). `_python` moved to `process_support.python_argv` and the unused `import sys` was dropped. Every test keeps its name and checks the same thing.
    - tests/process_support.py: changed under the same standing leave, as the destination of the move. It only gains `python_argv`; `is_gone` and `GONE_WITHIN_SECONDS` are unchanged.
21. factory: started docs as self.
22. documenter: Documented `run_streaming` and `ProcessResult.stopped` as the docs criterion asks. I changed documents only, so I did not run `make check`; the factory's check after this stage is the gate.

    Files changed:
    - `docs/project-guide.md`, section "Starting a process": adds `ProcessResult.stopped` and a `run_streaming` paragraph. The paragraph covers what the function is for (the opencode runtime's budget and provider limit, from S0004), the shared private `_start` that holds the one `Popen` line, the lines passed, the three endings (stop, time limit, raising callback), what `stdout`/`stderr` hold, and the tests and helpers.
    - `docs/decisions.md`: new entry *A run's output can be streamed by the one process module*, dated 2026-10-19 with the story. It has the decisions, the reasons and the rejected alternatives. I took the reasons from the story's Description, because my instructions keep me out of `feature.md`. The text therefore cites "F0020 decision 5" without having read it.

    Cross-read and found current against the diff:
    - The "Starting a process" paragraphs on `ProcessRequest`, `run_process` and `replace_process`.
    - The `tests/test_process_search.py` paragraph: the single `Popen` line and the six markers are unchanged.
    - The `claude -p` runtime and the git, make and confine sections that call `run_process`.

    Code findings: none. The code matches the Interface.

    Stale text noticed, left alone:
    - The "Known limits" paragraph under "Starting a process" says output is read without a limit after the kill. That is true of `run_process` and still correct. `run_streaming` reads nothing after a kill, and my new paragraph says so.
    - `make duplicates` reports vulture flagging `run_streaming` as unused. That is expected until S0004 calls it.

    `check`: check: green
    `documents`: documents ok
23. factory: started smoke-test as self.
24. smoke-tester: Ran the smoke test from the repository root as written: one shell block. It creates a temporary directory with an EXIT trap and runs the Python script through `uv run -q python - "$d"`. Nothing was fixed or changed.

    Command 1 (the `mktemp`/`uv run` block):

    ```
    stderr:two stdout:one stdout:stop
    True None False True
    exit: 0
    ```

    (`exit: 0` is the shell's exit status, which I printed after the block.)

    Met its `Expect:` line: yes. The first line is exactly `stderr:two stdout:one stdout:stop` and the second is exactly `True None False True`. The callback returned `True` for `stop`, so the run ended with `stopped=True`, `exit_status=None` and `timed_out=False`. The call returned in under 20 seconds, even though the child would have slept another 60 seconds. `never` was never passed to the callback. Lines from both streams arrived, standard error as `stderr` and standard output as `stdout`, with no `merge_stderr`.

    Judged against the acceptance criteria: the output agrees with criterion 1 (stream labels for both streams), criterion 3 (a stop on a line kills the run at once, returns within the bound, and passes no later line) and criterion 9 (`one` and `two` arrived before `stop`, while the child was still running). It contradicts no criterion. The smoke test does not exercise the time limit, a callback that raises, `merge_stderr`, a missing executable or `duration`; the tests cover those.

    Findings: none.
