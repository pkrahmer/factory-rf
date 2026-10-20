---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 363
comments_read: [6300695093]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T20:26:48.795037Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T20:23:18.746506Z'
  stage: intake
  run: ca51d3ed10314fa49b28fa6ede541688
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T20:25:41.530548Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T20:25:59.533786Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T20:26:27.866780Z'
  stage: intake
  run: a2860186deba4903acdaa9053f0577f5
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T20:26:48.795037Z'
  stage: tests
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

1. A child that prints `done` and exits 0 at once beside a holder (rows of one parametrized test: `run_process` with the holder on standard output; `run_process` with the holder on standard error, not merged; `run_streaming` with the holder on standard output; each with a `time_limit` of 60 seconds, and `run_process` and `run_streaming` also without one): the result has `exit_status` 0, `timed_out` false, `output_abandoned` true and `done` in its standard output (for `run_streaming`, `on_line` got `done`), after at least 2 and less than 20 seconds; the holder is still running when the call returns.
2. The other side (rows of one parametrized test, `run_process` and `run_streaming`): a child that exits 0 at once beside a grandchild in a session of its own that writes `late` to the inherited standard output 1 second later and then exits gives `output_abandoned` false and `late` in the output, the call returning after at least 1 and less than 15 seconds; the same with a grandchild that writes `late` 1.5 seconds later (the end of the child is noticed in time, so the line is read in full within the drain of 2 seconds); a child that exits 0 with no descendant gives `output_abandoned` false.
3. After the kill (`run_process`): a child that prints `started`, starts a holder and sleeps 60 seconds, with a `time_limit` of 3 seconds, gives `exit_status` `None`, `timed_out` true, `output_abandoned` true and `started` in the output, after at least 3 and less than 25 seconds. The same child without a holder gives `output_abandoned` false.
4. `run_streaming` beside a holder, rows of one parametrized test: at its time limit (`timed_out` true); a stop by `on_line` returning True (`stopped` true); an exception from `on_line` (it propagates); each with `output_abandoned` false, as today.
5. `PIPE_DRAIN` is 5 seconds, and `ProcessResult(exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(0)).output_abandoned` is false.
6. A limit that falls during the drain (rows of one parametrized test, `run_process` and `run_streaming`): a child that exits at once beside a holder, with a `time_limit` of 1 second and `PIPE_DRAIN` of 2 seconds, gives `timed_out` true; for `run_process` `exit_status` is `None` and `output_abandoned` true (the bounded read after the kill ran out beside the holder); for `run_streaming` `output_abandoned` is false.
7. `run_streaming` with a child that prints `a\nb` (no final line feed) beside a holder: after the drain, `on_line` got `a` and not `b`, `b` is still in `stdout`, and `output_abandoned` is true.
8. `make check` stays green.
9. docs: `docs/project-guide/processes-and-checks.md`, *Starting a process*: `PIPE_DRAIN`, `output_abandoned`, the read after the child's end and after the kill, in the paragraphs on `run_process`, `ProcessResult` and `run_streaming`; the paragraph *Known limits* is replaced: a process that left the session and keeps a pipe holds the call for at most `PIPE_DRAIN` after the child's end or the kill, not until it ends; it is not killed by this module (the leftovers program ends it after a call as another user). `docs/operator-guide.md`, **A `time_limit` under `sudo`.**: a call under `sudo` returns at most 5 seconds after the inner kill, also when a process of `agent` that left the group still holds its output. `docs/decisions.md`: a new entry *A call stops reading five seconds after its own process ended*, dated with the story, with the reasons of the feature's decision 17.

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
3. intake: The format check passed. The Interface, the architecture and the scope are fine, and the smoke test is runnable with checkable `Expect:` lines. I cannot accept the criteria yet: five Interface clauses have no criterion of their own, and nobody will test them otherwise. Each question below has my recommended answer, which is to add one criterion for it, before the two closing ones.

   1. "The time limit counts as before: a call whose limit comes before the child's end, or during the drain, is a `timed_out` call". Criterion 3 covers only the limit before the child's end. Add a criterion for a limit that falls during the drain: the child exits at once beside a holder, `time_limit` is 1 second and `PIPE_DRAIN` is 2 seconds. Expected result: `timed_out` true, `exit_status` as the interface says, and the session killed. Please state what `exit_status` and `output_abandoned` are in that case, because the Interface leaves both open for a limit during the drain. For `run_process`, the kill is followed by a bounded read, so `exit_status` would be `None`. Is that the intent?
   2. "`run_streaming` ... the last line without a line feed is not passed" to `on_line` when the drain runs out. Criterion 1 checks only that `done` arrived. Add a criterion: the child prints `a\nb` (no final line feed) beside a holder, and `on_line` got `a` but not `b`. Is `b` still in `stdout`, given "every byte read until then"?
   3. "`run_streaming` after ... a stop by `on_line` or an exception from it: unchanged, `output_abandoned` false". Criterion 4 covers only the kill at the time limit. Add rows for a stop by `on_line` returning True or False (whichever stops it; please name which) and for an exception from `on_line`, each beside a holder, each with `output_abandoned` false.
   4. "While a pipe is open, both functions check at least every 0.05 seconds whether the child has ended." No criterion tests this. Either add one or state that the timing criteria (1 and 2) cover it. A test can show that the end is noticed well within the drain: for example, a child that exits at once beside a grandchild that writes at 1.5 seconds with `PIPE_DRAIN` at 2 seconds must be read in full, which fails if the end was noticed late. Please say which you want.
   5. "The bound holds also for a request without `time_limit`." Criterion 1 includes the no-limit row for `run_process` only. Add the no-limit row for `run_streaming`, or say that `run_process` alone is intended.

   Also, a wording point in criterion 2: "before the drain of 2 seconds could have run out after it" is unclear. Please state the checkable condition, for example: the call returns after at least 1 and less than 15 seconds, with `late` in the output.
4. 2026-10-20 human: Answers (2026-10-20):
   1. Add it. A limit that falls during the drain is a `timed_out` call; for `run_process` `exit_status` is `None`, as for any kill, and `output_abandoned` says whether the bounded read after the kill ran out (true beside a holder that keeps the pipe).
   2. Add it: `on_line` gets `a` and not `b`; `b` is still in `stdout` (every byte read until then).
   3. Add the rows: a stop by `on_line` (with the return value that stops it today, as `run_streaming`'s docstring says) and an exception from `on_line`, each beside a holder, each with `output_abandoned` false.
   4. No separate test of the 0.05 s polling: put your example into criterion 1 or 2 (a child that exits at once beside a grandchild that writes at 1.5 s, `PIPE_DRAIN` 2 s, read in full). That shows the end is noticed in time.
   5. Add the no-limit row for `run_streaming`.
   Criterion 2's wording: use your checkable form (the call returns after at least 1 and less than 15 seconds, with `late` in the output).
   Keep every new row's limits and waits as short as the rule allows; the suite's slowest tests are already time-limit tests.
5. factory: started intake as self.
6. intake: accepted. I carried the human's answers (journal entry 4) into the story's criteria and changed nothing else. The Description's meaning is unchanged, so I left it alone.
   - Interface: accepted. It names `factory.adapters.process`, `PIPE_DRAIN`, `ProcessResult.output_abandoned` and the unchanged signatures of `run_process` and `run_streaming`. Every clause now has a criterion, including the 0.05 s polling, which the 1.5 s case in criterion 2 covers (answer 4).
   - Criteria: accepted. Each is testable by one parametrized test, and the failing side of each rule has a row. Edits from entry 4:
     - Criterion 1 gets the no-limit row for `run_streaming` (answer 5).
     - Criterion 2 is reworded to "returns after at least 1 and less than 15 seconds, with `late` in the output", plus the 1.5 s grandchild case (answers 4 and the wording point).
     - Criterion 4 is now rows for the time limit, a stop by `on_line` returning True (the value `run_streaming`'s docstring says stops it), and an exception from `on_line`, each with `output_abandoned` false (answer 3).
     - New criterion 6 is a limit that falls during the drain: `timed_out` true, `exit_status` `None` and `output_abandoned` true for `run_process`, `output_abandoned` false for `run_streaming` (answer 1).
     - New criterion 7 is `a\nb` beside a holder: `on_line` gets `a` and not `b`, `b` stays in `stdout`, `output_abandoned` true (answer 2).
     - `make check` and `docs:` are now criteria 8 and 9 and stay last.
     - Answer 1 only states the `run_process` case. I wrote the `run_streaming` row from its Interface line: no read after a kill, so `output_abandoned` false.
   - Smoke test: accepted. It is runnable. Each `Expect:` line is checkable: the status, `timed_out`, `output_abandoned`, the output and the timing bound. No pytest command, so no `-q` question.
   - Architecture: accepted. The change sits in `factory.adapters.process`, the one module that starts processes. No layer, interface or caller changes.
   - Scope: accepted. It matches the feature's S0005 scope line and decision 17, and no earlier test changes.
7. factory: started tests as self.
