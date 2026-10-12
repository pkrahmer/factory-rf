---
stage: tests
pr: 4
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The process wrapper: the one place that starts a subprocess

## Assignment (as of log entry 1)

Build `run_process`, the one place in the factory that starts a subprocess (R5): the git wrapper (S0005), the make class (S0007) and the `claude -p` runtime (S0009) each reach their command-line tool through it. It never uses a shell, starts the child in its own session, gives it exactly the environment it is told to, merges stderr into stdout on request, decodes the output, and at the `time_limit` kills the child together with everything it started. Two searches in the tests prove the boundary: `subprocess` is imported by one module only, and no other route to a process (`shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `asyncio.create_subprocess_*`) is used under `src/factory`; a third proves that the only suppression markers under `src/factory` are the four in this module. Covers R5 (each command-line tool only behind a wrapper class); builds the base that R9 (git), R11 (make) and R12 (the agent runtime) stand on. This story was split from the git wrapper to keep each story within 26 criteria. The suppression markers are already allowed: `CLAUDE.md` carries the exception for `src/factory/adapters/process.py` (the four markers `noqa: S404`, `nosec B404`, `noqa: S603`, `nosec B603`) and `docs/decisions.md` records it, so nothing is asked of the human before the story starts. Tests use real child processes written into `tmp_path` and Python as the child; nothing is faked.

## Interface

`src/factory/adapters/process.py`

```python
class ProcessRequest(BaseModel):
    argv: Annotated[list[str], Field(min_length=1)]
    cwd: Path
    env: dict[str, str] | None = None
    time_limit: timedelta | None = None
    merge_stderr: bool = False

class ProcessResult(BaseModel):
    exit_status: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration: timedelta

def run_process(request: ProcessRequest) -> ProcessResult: ...
```

The rules, each with a criterion below:

- `run_process` never uses a shell: `argv` is the program and its arguments, passed as given. It starts the child in its own session; when `time_limit` is reached it kills the whole process group, so that children of the command end too, and returns with `exit_status` `None`, `timed_out` true and the output written so far. `time_limit` of `None` means no limit; otherwise it must be greater than zero.
- `env` of `None` makes the child inherit the current environment; a mapping is the child's whole environment. With `merge_stderr` the child's stderr goes into the same pipe as its stdout, in the order written, and `stderr` is empty. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start (`OSError`, for example `FileNotFoundError`) is not caught.
- `subprocess` is imported by `factory.adapters.process` only. Under `src/factory`, `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `asyncio.create_subprocess_exec` and `asyncio.create_subprocess_shell` are used nowhere. The search reads attribute calls and imports by name; it does not see a call made through `getattr` or `importlib`, which ruff's `S` rules in `make check` cover.
- The only suppression markers under `src/factory` are the four in `process.py`: `noqa: S404` and `nosec B404` on the line `import subprocess`, `noqa: S603` and `nosec B603` on the line that calls `subprocess.Popen`.

Tests: `tests/adapters/test_process.py`, `tests/test_process_search.py`, which uses `tests/source_search.py` (the helper from S0003 that parses every module under `src/factory` with `ast`). The children are Python one-liners run with `sys.executable`. A test that proves a process is gone writes the pid to a file, and after the call returns it passes when `os.kill(pid, 0)` raises `ProcessLookupError`, or when `/proc/<pid>/stat` shows the state `Z` (a killed child that no init process has reaped yet). The only waiting in the tests is for a child process that the `time_limit` kills.

## Acceptance criteria

1. `run_process` of a child that prints `out` to stdout and `err` to stderr and exits 0 returns `stdout == "out\n"`, `stderr == "err\n"`, `exit_status == 0`, `timed_out` false and a duration that is not negative; a child that prints its working directory prints `cwd`.
2. A child that exits with status 3 gives `exit_status == 3`; nothing is raised.
3. With `merge_stderr=True`, a child that writes `a` to stdout, `b` to stderr and `c` to stdout (flushing each) gives `stdout == "a\nb\nc\n"` and `stderr == ""`.
4. A given `env` is the child's whole environment: a variable set in the test process is absent in the child and a given variable is present; with `env=None` the child sees the test process's variable.
5. With `time_limit=timedelta(seconds=1)`, a child that sleeps 60 seconds after printing `started` is killed: `exit_status` is `None`, `timed_out` is true, `stdout` still holds `started`, and the call returns within 6 seconds.
6. In the same case, a grandchild that the child started (it writes its pid to a file) is gone after the call returns, by the method named under Tests.
7. A child that ends within the `time_limit` gives `timed_out` false and its real exit status.
8. A missing executable raises `FileNotFoundError`.
9. `ProcessRequest` rejects an empty `argv`, a `time_limit` of zero and a `time_limit` of `timedelta(seconds=-1)` with `ValidationError`, and accepts a `time_limit` of one second and `None`.
10. A child that writes the bytes `\xff ok\n` to stdout gives `stdout == "� ok\n"`.
11. An argument with shell characters, such as `$HOME; echo x`, reaches the child exactly as written: a child that prints `sys.argv[1]` prints that text.
12. Among the modules of `src/factory`, only `factory.adapters.process` imports `subprocess`.
13. No module under `src/factory` uses `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `asyncio.create_subprocess_exec` or `asyncio.create_subprocess_shell`; the search is run against a source snippet that calls `os.system` and finds it.
14. The text `noqa`, `nosec`, `nosemgrep` and `pragma: allowlist secret` occurs under `src/factory` only in `process.py`, and there as exactly the four markers `noqa: S404`, `nosec B404`, `noqa: S603` and `nosec B603`, each on the line named in the Interface.
15. make check stays green.
16. docs: `docs/project-guide.md` states the rule that `subprocess` is started in `factory.adapters.process` only and describes `run_process` (own session, process-group kill at the `time_limit`, whole environment, merged output); `docs/decisions.md` records why the four suppression markers are in `process.py` and why there are no others (WE6.3).

## Demo

```bash
uv run python -c "
import sys
from datetime import timedelta
from pathlib import Path
from factory.adapters.process import ProcessRequest, run_process
code = 'import sys; print(\"out\", flush=True); print(\"err\", file=sys.stderr, flush=True); sys.exit(3)'
result = run_process(ProcessRequest(argv=[sys.executable, '-c', code], cwd=Path('.'), merge_stderr=True))
print(result.exit_status, result.timed_out, repr(result.stdout))
slow = 'import time; print(\"started\", flush=True); time.sleep(60)'
killed = run_process(ProcessRequest(argv=[sys.executable, '-c', slow], cwd=Path('.'), time_limit=timedelta(seconds=1)))
print(killed.exit_status, killed.timed_out, repr(killed.stdout))
"
```
Expect: two lines: `3 False 'out\nerr\n'`, then `None True 'started\n'`: the exit status and the merged output come back, and the child that sleeps is killed at the limit with the output it had written.

```bash
uv run python -c "
import ast, pathlib
found = []
for path in sorted(pathlib.Path('src/factory').rglob('*.py')):
    for node in ast.walk(ast.parse(path.read_text())):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        if 'subprocess' in names:
            found.append(path.as_posix())
print(sorted(set(found)))
"
```
Expect: one line, `['src/factory/adapters/process.py']`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `src/factory/adapters/process.py` names `ProcessRequest`, `ProcessResult` and `run_process` with full signatures. Each stated behaviour (no shell, own session, group kill, `time_limit` None or >0, env None or whole, merged stderr, UTF-8 replace, uncaught `OSError`) has a criterion (1-11).
   - Criteria: each is testable by one test function. The failing sides are covered: empty `argv`, zero and negative `time_limit` (9), missing executable (8), non-zero exit (2), timeout (5, 6), and a child that ends within the limit (7).
   - Demo: both blocks are runnable. The `Expect:` lines are checkable: `3 False 'out\nerr\n'` and `None True 'started\n'` for the first, and `['src/factory/adapters/process.py']` for the second.
   - Architecture: the module sits in `factory.adapters`, uses Pydantic DTOs, has no `dict[str, Any]` crossing a boundary, and is the single process wrapper per R5. The suppression markers match the exception in `CLAUDE.md`, so no question is needed.
   - Scope: this is the feature's "one place that starts a subprocess" and the boundary searches. It stays clear of Out of scope. The `tests/source_search.py` helper comes from S0003, which is earlier in the feature's order.
