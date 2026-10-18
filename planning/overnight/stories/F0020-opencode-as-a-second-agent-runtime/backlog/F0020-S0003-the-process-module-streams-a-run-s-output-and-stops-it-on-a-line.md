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

1. A child that prints `one` and `two` on standard output and `err` on standard error and exits 3 gives the calls `("stdout", "one")`, `("stdout", "two")` and `("stderr", "err")`, the stdout calls in that order, and a result with exit status 3, `stdout` `"one\ntwo\n"`, `stderr` `"err\n"`, `stopped` and `timed_out` false.
2. A last line without a line feed is passed, and a line with bytes that are not UTF-8 is passed with the replacement character (rows).
3. A child that prints `go`, then sleeps 60 seconds, with a callback that returns `True` for `go`: the call returns within 20 seconds, with `stopped` true, `exit_status` `None` and `timed_out` false; a grandchild the child started is gone (`is_gone`), and no line the child would print after the sleep is passed.
4. A callback that returns `True` for a line on standard error stops the run as in criterion 3.
5. A child that prints `started` and sleeps 60 seconds under a time limit of 3 seconds, with a callback that never stops: the call returns within 20 seconds with `timed_out` true, `stopped` false, `exit_status` `None` and `started` in `stdout`.
6. A callback that raises `RuntimeError` on the first line: the call raises it, and the child, which would sleep 60 seconds after that line, is gone.
7. With `merge_stderr=True`, a line on standard error comes as `("stdout", ...)` in the order written, and the result's `stderr` is `""`.
8. A missing executable raises `FileNotFoundError` and calls the callback never.
9. Lines arrive while the child runs: a child that prints `first`, then waits until a file appears, then prints `second`, with a callback that writes that file when it gets `first`, ends with both lines passed (no sleep in the test).
10. `run_process` and every test of `tests/adapters/test_process.py` behave as before, and the module holds one `subprocess.Popen(` line.
11. `make check` stays green.
12. docs: `docs/project-guide.md`, the process module: `run_streaming` hands each line to a callback while the process runs and kills the process group when the callback says stop, for a runtime that must act on its output as it comes (the opencode runtime's budget and provider limit); `ProcessResult.stopped`. `docs/decisions.md`: an entry *A run's output can be streamed by the one process module*, dated with the story, with the reasons of the feature's decision 5.

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
