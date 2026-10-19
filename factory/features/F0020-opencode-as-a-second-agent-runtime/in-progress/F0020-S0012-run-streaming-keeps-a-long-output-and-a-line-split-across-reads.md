---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 278
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T18:44:01.983017Z'
  lease_duration: 60
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
