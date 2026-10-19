# run_streaming keeps a long output and a line split across reads

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`run_streaming` (`factory.adapters.process`) reads a run's output in chunks of up to 64 KiB and hands each complete line to the callback. The opencode runtime parses its whole result from `ProcessResult.stdout` and stops a run on a line, so a line that arrives in two reads must reach the callback whole, and an output longer than one read must reach `stdout` whole. A real story's event stream is far longer than 64 KiB. The code does this today, but no test notices if it stops: F0020's mutation run left both `self.read_bytes[stream] += chunk` → `= chunk` and `self._pending[stream] += chunk` → `= chunk` in `_LineReader.read_ready` alive. This story pins both with tests and changes no code. The callback's stop, the time limit and `run_process` stay as they are, and so do their tests.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `run_streaming(request, on_line) -> ProcessResult` in `factory.adapters.process` (adapters), as it is:

- A line is handed to `on_line` once and whole, however many reads it takes to arrive, on standard output and on standard error alike.
- `ProcessResult.stdout` and `ProcessResult.stderr` hold everything the process printed, however many reads it took.

Tests (the tester writes them): `tests/adapters/test_process_streaming_reads.py` (new), with real Python child processes and the helper `python_argv` from `tests/process_support.py`, imported, not copied. No earlier test changes.

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
