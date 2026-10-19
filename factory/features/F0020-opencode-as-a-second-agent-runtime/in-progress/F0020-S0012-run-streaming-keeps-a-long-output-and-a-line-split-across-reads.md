---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 278
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T18:43:18.475891Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T18:43:18.483571Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T18:43:40.616337Z'
  stage: intake
  run: 30dcdd2f68aa4627abba3dade15a12d6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T18:44:01.983017Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T18:46:14.324213Z'
  stage: tests
  run: 8eb2b246c32a4a8b8db6912d1d022b6b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T18:46:34.953495Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T18:48:44.717775Z'
  stage: doing
  run: cbcead40275c4aebb5a5b3e8d6c7efc2
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T18:49:06.060475Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T18:49:30.077850Z'
  stage: review
  run: bf0a515435d44a0b8bb444d152e9644d
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T18:49:51.205034Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T18:50:12.135031Z'
  stage: docs
  run: 60e523348b744e36bdcdefd22125c7c0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T18:50:32.763454Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T18:50:54.725043Z'
  stage: smoke-test
  run: 840f23cce74c400b9be5276b88dcb7c2
---

# run_streaming keeps a long output and a line split across reads

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`run_streaming` (`factory.adapters.process`) reads a run's output in chunks of up to 64 KiB and hands each complete line to the callback. The opencode runtime parses its whole result from `ProcessResult.stdout` and stops a run on a line, so a line that arrives in two reads must reach the callback whole, and an output longer than one read must reach `stdout` whole. A real story's event stream is far longer than 64 KiB. The code does this today, but no test notices if it stops: F0020's mutation run left both `self.read_bytes[stream] += chunk` → `= chunk` and `self._pending[stream] += chunk` → `= chunk` in `_LineReader.read_ready` alive. This story pins both with tests and changes no code. The callback's stop, the time limit and `run_process` stay as they are, and so do their tests.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `run_streaming(request, on_line) -> ProcessResult` in `factory.adapters.process` (adapters), as it is:

- A line is handed to `on_line` once and whole, however many reads it takes to arrive, on standard output and on standard error alike.
- `ProcessResult.stdout` and `ProcessResult.stderr` hold everything the process printed, however many reads it took.

Tests (the tester writes them): `tests/adapters/test_process_streaming_reads.py` (new), with real Python child processes, the helper `python_argv` from `tests/process_support.py` and the callback `Recorder`, imported, not copied. Under the standing leave of `CLAUDE.md` (*Tests*) the tester moves `Recorder` from `tests/adapters/test_process_streaming.py` to `tests/process_support.py`, and `tests/adapters/test_process_streaming.py` imports it from there; its tests keep their names and what they check. No other earlier test changes.

## Acceptance criteria

1. A child that prints one line of 200000 `x` characters to standard output and exits 0: `on_line` is called exactly once, with `("stdout", <the 200000 characters>)`, and `ProcessResult.stdout` has length 200001 (the line and its newline). A second row prints the line to standard error: one call with `("stderr", ...)`, and `ProcessResult.stderr` has length 200001.
2. A child that writes `{"a":` to a stream, flushes it, waits 0.5 seconds and then writes `1}` and a newline: `on_line` gets exactly one line, `{"a":1}`, for that stream, and the stream's text in the result is `{"a":1}\n`. Two rows, standard output and standard error.
3. `make check` stays green.
4. docs: `docs/project-guide/processes-and-checks.md`, the paragraph on `run_streaming`, says in one sentence that a line reaches the callback whole however many reads it takes, and that `stdout` and `stderr` hold the whole output.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from pathlib import Path
from factory.adapters.process import ProcessRequest, run_streaming

d = Path(sys.argv[1])
seen = []
long = run_streaming(ProcessRequest(argv=[sys.executable, "-c", "print('x' * 200000)"], cwd=d, time_limit=timedelta(seconds=20)), lambda stream, line: seen.append((stream, len(line))) is None and False)
print(seen, len(long.stdout))
split = "import sys, time; sys.stdout.write('{\"a\":'); sys.stdout.flush(); time.sleep(0.5); sys.stdout.write('1}\\n'); sys.stderr.write('he'); sys.stderr.flush(); time.sleep(0.5); sys.stderr.write('llo\\n')"
lines = []
result = run_streaming(ProcessRequest(argv=[sys.executable, "-c", split], cwd=d, time_limit=timedelta(seconds=20)), lambda stream, line: lines.append((stream, line)) is None and False)
print(sorted(lines), repr(result.stdout), repr(result.stderr))
EOF
```
Expect: two lines, `[('stdout', 200000)] 200001` and `[('stderr', 'hello'), ('stdout', '{"a":1}')] '{"a":1}\n' 'hello\n'`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change. It pins the behaviour of `run_streaming(request, on_line) -> ProcessResult` in `factory.adapters.process`. I checked that `python_argv` is in `tests/process_support.py`, that `Recorder` is in `tests/adapters/test_process_streaming.py` (the move to `tests/process_support.py` is covered by the standing leave and named in the story), and that `_LineReader.read_ready` holds both `+=` lines the story names (`src/factory/adapters/process.py` lines 126-127).
   Criteria: criterion 1 (200000-character line, once and whole, `stdout` and `stderr` of length 200001) and criterion 2 (a line split across a 0.5 s pause, `stdout` and `stderr`) are each one parametrized test with exact values. Every clause of the two Interface bullets has a criterion on both streams. The story states no limit, refusal or default, so there is no failing side to cover. Criteria 3 and 4 are the two closing ones, in the right order.
   Smoke test: it runs as written with `uv run -q python` on real child processes, and the `Expect:` line gives the exact values to compare. The run's two lines and the sorted list make the second check order-independent.
   Architecture: it fits. The change is tests only, in `tests/adapters/`, mirroring the package. It uses no fake git and no mocks, and the child processes are real. The docs criterion names `docs/project-guide/processes-and-checks.md`, which has the `run_streaming` paragraph at line 71.
   Scope: it is within F0020 (S0003's streaming) and not in its Out of scope. Moving `Recorder` is covered by the standing leave and the story names the file changed. I changed nothing in the story.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 and 2, using real Python child processes, `python_argv` and `Recorder` from `tests/process_support.py`.
   criterion 1: tests/adapters/test_process_streaming_reads.py::test_line_longer_than_one_read_reaches_the_callback_and_the_result_whole (two rows, `stdout` and `stderr`. Each checks that `on_line` was called exactly once, as `(stream, "x" * 200000)`, and that the stream's text in the result has length 200001.)
   criterion 2: tests/adapters/test_process_streaming_reads.py::test_line_split_across_two_writes_reaches_the_callback_once_and_whole (two rows, `stdout` and `stderr`. The child writes `{"a":`, flushes, waits 0.5 s in the child, then writes `1}\n`. The test checks that the callback got exactly `['{"a":1}']` for that stream and that the stream's text is `{"a":1}\n`.)
   criterion 3 (`make check`) and criterion 4 (docs) are not test criteria. They belong to the coder and the documenter.

   Files created: tests/adapters/test_process_streaming_reads.py.
   Earlier test files changed under the standing leave in CLAUDE.md (*Tests*), as the Interface names:
   - tests/process_support.py: `Recorder` moved here, along with its `threading` and `Stream` imports. The module docstring now covers the wider purpose.
   - tests/adapters/test_process_streaming.py: `Recorder` removed and imported from `process_support`. Its tests keep their names and what they check.

   Modules the test runner could not import: none. The story pins behaviour the code already has and changes no code, so the new tests pass from the start (`make test`: `test: green`). They do not fail first, as the story intends. They fail under the two surviving mutants: the 200000-character line takes several reads of at most 64 KiB, and the split line takes two. `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: test: green (45.8 s)
6. factory: started doing as self.
7. coder: No code change. The story pins behaviour `run_streaming` already has, and its Interface says no module under `src/factory/` changes. I ran `make check` on the committed state with the tester's tests in `tests/adapters/test_process_streaming_reads.py`, and every target passed (`test: green (47.2 s)`, `check: green`). There is no diff of mine to refactor.
   Main choice: leave `src/factory/adapters/process.py` (`_LineReader.read_ready`) as it is. I rejected restructuring the reader so that the two surviving mutants (`+=` → `=`) could be killed some other way, because the story is tests only (R13).
   Noticed, not touched: nothing. The journal did not change the meaning of the task, so the Description is as it was. Criterion 4 (the `run_streaming` sentence in `docs/project-guide/processes-and-checks.md`) is the documenter's.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   I read the diff (`tests/adapters/test_process_streaming_reads.py` new, `tests/process_support.py` and `tests/adapters/test_process_streaming.py` changed, nothing under `src/`) against the work item and against `_LineReader.read_ready` in `src/factory/adapters/process.py`.
   - Criterion 1: `test_line_longer_than_one_read_reaches_the_callback_and_the_result_whole` has one row per stream. A 200001-byte write needs several reads of at most 64 KiB. The test asserts `recorder.calls == [(stream, "x" * 200000)]`, which means exactly one call and none on the other stream, and that the result's text has length 200001. Under `read_bytes[stream] = chunk` the length check fails. Under `_pending[stream] = chunk` the line reaches the callback cut short.
   - Criterion 2: `test_line_split_across_two_writes_reaches_the_callback_once_and_whole` has one row per stream. The child writes `{"a":`, flushes, waits 0.5 s, then writes `1}\n`. The test asserts that the callback got exactly `['{"a":1}']` for that stream and that the stream's text is `{"a":1}\n`. That kills both surviving mutants the story names (the callback would get `1}`, and the text would be `1}\n`).
   - The coder's entry 7 says `make check` was green. No code change, so there is no mutation line to read. The story states no limit or refusal, so there is no failing side to cover. The architecture and security checks do not apply to a test-only diff. The `_text` helper is not a copy of an existing one: I searched `tests/` and found none with the same use. The Description matches what was built. Criterion 4 still names the `run_streaming` paragraph the documenter has to update.

   Earlier tests:
   - tests/process_support.py: changed under the standing leave to move a shared test helper. `Recorder` moved here unchanged, with its `threading` and `Stream` imports and a wider module docstring. The story's Interface names this file too.
   - tests/adapters/test_process_streaming.py: changed under the standing leave to move a shared test helper. Its own copy of `Recorder` was removed and it now imports `Recorder` from `process_support`. Every test keeps its name and what it checks. The story's Interface names this file too.
10. factory: started docs as self.
11. documenter: No findings. The diff is tests only (`tests/adapters/test_process_streaming_reads.py` new; `Recorder` moved to `tests/process_support.py`); nothing under `src/` changed, so the code and the story's Interface agree.

    Files changed:
    - `docs/project-guide/processes-and-checks.md`: in the `run_streaming` paragraph, one added sentence says a line reaches the callback once and whole however many reads it takes (a line longer than one 64 KiB read, or one split by a pause), and that `stdout` and `stderr` hold the whole output (criterion 4). The "Tests:" line now also names `tests/adapters/test_process_streaming_reads.py` and says `Recorder` is among the helpers in `tests/process_support.py`, since it moved there.

    Cross-read and found current: `docs/project-guide/agents.md` (the `run_streaming` mention in the opencode runtime), `docs/decisions.md` (the `run_streaming` entries), and the rest of `processes-and-checks.md`. I changed documents only, so I did not run `make check`; the factory's checks run after this stage.

    Stale text noticed, not touched: none.

    `check`: check: green (not run again: passed on tree c16507d52c1f at 2026-10-19T18:47:44Z)
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed, no findings.

    I ran the one command under `## Smoke test` exactly as written, from the repository root. It exited with 0.

    ```
    [('stdout', 200000)] 200001
    [('stderr', 'hello'), ('stdout', '{"a":1}')] '{"a":1}\n' 'hello\n'
    ```
    Expect: two lines, `[('stdout', 200000)] 200001` and `[('stderr', 'hello'), ('stdout', '{"a":1}')] '{"a":1}\n' 'hello\n'`. Met: both lines match exactly.

    Checked against the acceptance criteria:
    - Criterion 1: on standard output, the 200000-character line reached the callback once and whole, and `stdout` has length 200001. The smoke test does not cover the standard-error row of this criterion. The tester's parametrized test covers it, and nothing in the output contradicts it.
    - Criterion 2: a line split by a 0.5 s pause reached the callback once and whole on both streams (`{"a":1}` and `hello`), and each stream's text in the result is whole. Nothing contradicts it.
    - Criterion 3: I did not run `make check` in this stage. The coder reported `check: green` (entry 7) and the factory reused that result after the docs stage (entry 11). Nothing in the smoke test contradicts it.
    - Criterion 4: `docs/project-guide/processes-and-checks.md:71` holds the sentence: "A line reaches the callback once and whole however many reads it takes to arrive …, and `stdout` and `stderr` hold the whole output."

    I changed nothing. The working tree holds only the factory's `.costs.jsonl` sidecar.
