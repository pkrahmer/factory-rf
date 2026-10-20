---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T20:22:56.751052Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T20:22:56.745690Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T20:22:56.751052Z'
  stage: intake
---

# A call no longer waits for a process that keeps its output open after the call's own process ended

## Description

`run_process` reads a call's output until both pipes close, and after a kill at the time limit it reads again without a limit. A process that left the call's process group and still holds a pipe therefore holds the call until it ends by itself. Under `sudo` no kill reaches it: the agent's own `timeout` kills only its group, and the factory's kill (F0030) leaves out every process it may not signal. On 2026-10-20, in a throwaway container, a `sudo` call killed by its inner `timeout` at 3 seconds returned only at 12 seconds, when such a process ended. After S0002 every project command runs so, as every agent run already does, and this repository's tests start every child in a session of its own. This story bounds that wait in the process module, for every call. Both `run_process` and `run_streaming` notice the end of the child while they read. Once it has ended, they read on for at most `PIPE_DRAIN` (5 seconds); then they stop reading, close the pipes and return the child's own exit status, the output read so far and `output_abandoned=True`. After its kill at the time limit, `run_process` reads what is left for at most the same 5 seconds. So a call under `sudo` ends at most 5 seconds after its inner kill, and a call whose child ended on its own keeps its real result. A call whose pipes close in time, which is every call today, behaves exactly as before. The kill, its rounds and what each caller makes of a result are unchanged; the leftovers program after the call (F0027, S0001) ends the holder.

## Interface

`factory.adapters.process` (`adapters`):

```python
PIPE_DRAIN = timedelta(seconds=5)


class ProcessResult(BaseModel):
    """What a finished or killed process left: its status, its output and how long it ran."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exit_status: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration: timedelta
    stopped: bool = False
    output_abandoned: bool = False


def run_process(request: ProcessRequest) -> ProcessResult: ...  # signature unchanged


def run_streaming(
    request: ProcessRequest, on_line: Callable[[Stream, str], bool]
) -> ProcessResult: ...  # signature unchanged
```

- While a pipe is open, both functions check at least every 0.05 seconds whether the child has ended.
- Once the child has ended on its own, both read on until both pipes close or `PIPE_DRAIN` has passed since the end was noticed, whichever comes first. When the pipes closed, the result is as today and `output_abandoned` is false. When `PIPE_DRAIN` passed first, they stop reading, the pipes are closed, and the result has the child's exit status, `timed_out` false, `stopped` false, `output_abandoned` true, and every byte read until then; `run_streaming` has passed every complete line read until then to `on_line`, and the last line without a line feed is not passed.
- The time limit counts as before: a call whose limit comes before the child's end, or during the drain, is a `timed_out` call as today, and its session is killed as today.
- After that kill, `run_process` reads what is left until both pipes close or `PIPE_DRAIN` has passed since the kill, whichever comes first, then closes the pipes; `output_abandoned` is true when a pipe was still open then. `exit_status` is `None` and `timed_out` true, as today.
- `run_streaming` after a kill at the time limit, a stop by `on_line` or an exception from it: unchanged (no read after the kill), and `output_abandoned` false.
- `PIPE_DRAIN` is read at each call, so a test can set it with `monkeypatch.setattr`. The bound holds also for a request without `time_limit`.
- Unchanged: `ProcessRequest`, `_kill_session` and its rounds and refusals, `replace_process`, the one `subprocess.Popen(` line, the six suppression markers, every caller (the git wrapper, the make class, both runtimes), and what they make of a result.

Tests (the tester writes them): `tests/adapters/test_process_drain.py`. A holder is a grandchild that the test's child starts in a session of its own (`start_new_session=True`) with the child's standard output, or its standard error, inherited, that writes its id to a file in `tmp_path` and sleeps 60 seconds; a fixture kills every holder after the test. Each test sets `PIPE_DRAIN` to 2 seconds. No earlier test changes: a prototype passed every test module of the process module, both runtimes, the make class, `agent_launch`, the git wrapper and `run_sealed` unchanged.

## Acceptance criteria

1. A child that prints `done` and exits 0 at once beside a holder (rows of one parametrized test: `run_process` with the holder on standard output; `run_process` with the holder on standard error, not merged; `run_streaming` with the holder on standard output; each with a `time_limit` of 60 seconds, and `run_process` also without one): the result has `exit_status` 0, `timed_out` false, `output_abandoned` true and `done` in its standard output (for `run_streaming`, `on_line` got `done`), after at least 2 and less than 20 seconds; the holder is still running when the call returns.
2. The other side (rows of one parametrized test, `run_process` and `run_streaming`): a child that exits 0 at once beside a grandchild in a session of its own that writes `late` to the inherited standard output 1 second later and then exits gives `output_abandoned` false and `late` in the output, in less than 15 seconds, before the drain of 2 seconds could have run out after it; a child that exits 0 with no descendant gives `output_abandoned` false.
3. After the kill (`run_process`): a child that prints `started`, starts a holder and sleeps 60 seconds, with a `time_limit` of 3 seconds, gives `exit_status` `None`, `timed_out` true, `output_abandoned` true and `started` in the output, after at least 3 and less than 25 seconds. The same child without a holder gives `output_abandoned` false.
4. `run_streaming` at its time limit beside a holder: `timed_out` true, `output_abandoned` false, as today.
5. `PIPE_DRAIN` is 5 seconds, and `ProcessResult(exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(0)).output_abandoned` is false.
6. `make check` stays green.
7. docs: `docs/project-guide/processes-and-checks.md`, *Starting a process*: `PIPE_DRAIN`, `output_abandoned`, the read after the child's end and after the kill, in the paragraphs on `run_process`, `ProcessResult` and `run_streaming`; the paragraph *Known limits* is replaced: a process that left the session and keeps a pipe holds the call for at most `PIPE_DRAIN` after the child's end or the kill, not until it ends; it is not killed by this module (the leftovers program ends it after a call as another user). `docs/operator-guide.md`, **A `time_limit` under `sudo`.**: a call under `sudo` returns at most 5 seconds after the inner kill, also when a process of `agent` that left the group still holds its output. `docs/decisions.md`: a new entry *A call stops reading five seconds after its own process ended*, dated with the story, with the reasons of the feature's decision 17.

## Smoke test

```bash
d=$(mktemp -d); trap 'for f in "$d"/pid*; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null; done; rm -rf "$d"' EXIT
uv run python - "$d" <<'EOF'
import sys
import time
from datetime import timedelta
from pathlib import Path

from factory.adapters.process import PIPE_DRAIN, ProcessRequest, run_process

d = Path(sys.argv[1])
holder = 'setsid sh -c \'echo $$ > "$1"; exec sleep 60\' holder "$1" & '
for name, script, limit in (("pid1", "echo done", 60), ("pid2", "echo started; sleep 60", 3)):
    start = time.monotonic()
    result = run_process(ProcessRequest(argv=["sh", "-c", holder + script, "sh", str(d / name)], cwd=d, time_limit=timedelta(seconds=limit)))
    took = time.monotonic() - start
    print(result.exit_status, result.timed_out, result.output_abandoned, result.stdout.split(), PIPE_DRAIN.total_seconds() <= took < limit + 20)
EOF
```
Expect: two lines, `0 False True ['done'] True`, then `None True True ['started'] True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
