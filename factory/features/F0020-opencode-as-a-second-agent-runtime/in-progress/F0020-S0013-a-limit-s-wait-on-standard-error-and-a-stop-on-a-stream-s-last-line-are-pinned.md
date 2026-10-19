---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 297
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T22:50:23.310059Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T22:50:23.316636Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T22:50:39.073686Z'
  stage: intake
  run: e886143e59e24b999efb445da95a841c
  blocked: question
---

# A limit's wait on standard error and a stop on a stream's last line are pinned

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0020's second acceptance ran `make mutants` against the final code. Two survivors sit on the path by which a provider limit reaches an opencode run, and no test would notice if either broke:

- In `_Watch.on_line` of `factory.adapters.opencode_runtime`, `self._stop_at_limit(line)` → `self._stop_at_limit(None)` survives. A limit line on standard error ends the run `provider_limit`, but no test checks that a wait the line names ("retry after 120 seconds") becomes the run's `limit_wait`. The existing test plays only a line with no wait. Decision 12 promises the wait for "a line of standard error" too, and `PatientRuns` waits exactly that long instead of the cool-down.
- In `_LineReader.read_ready` of `factory.adapters.process`, the `return True` after `_pass_last_line` → `return False` survives. When the callback says stop on a stream's last line (one that ends without a newline when the stream closes), the call has to stop at once, as it does for a complete line. Under the mutant it reads on until the other stream ends or the time limit passes.

The code does both today: the second acceptance's smoke tests show `provider_limit 0:02:00` and a stop within a second. This story writes the tests and changes no code.

## Interface

No module under `src/factory/` changes. The behaviour pinned is the following, as it is:

- `OpencodeRuntime.run` (`factory.adapters.opencode_runtime`, adapters): a line on standard error that holds the provider limit's status as a whole number (`ProviderLimit.status`, 428 by default) ends the run `provider_limit` at once. Its `limit_wait` is `named_wait(<that line>)` (`factory.domain.provider_limits`): the wait the line names, or `None` when it names none. A line on standard error that names a wait but not the status is no limit, and the run goes on.
- `run_streaming(request, on_line) -> ProcessResult` (`factory.adapters.process`, adapters): a stream's last line that ends without a newline is handed to `on_line` when the stream closes. When `on_line` returns `True` for it, the call stops at once and kills the process group, as it does for a complete line: `stopped` is `True`, `exit_status` `None` and `timed_out` `False`, even though the other stream is still open.

Tests (the tester writes them), new modules, with the helpers imported, not copied:

- `tests/adapters/test_opencode_limit_wait_on_stderr.py` (criterion 1), with `Step` of `tests/adapters/claude_stand_in.py` and `stand_in_runtime(..., stderr_first=...)`, `opencode_request`, `step_start`, `stdout`, `text`, `result_text`, `step_finish`, `RESUME_REPLY`, `WAIT_SECONDS` and `BOUND_SECONDS` of `tests/adapters/opencode_stand_in.py`, as `tests/adapters/test_opencode_provider_limit.py` uses them;
- `tests/adapters/test_process_streaming_last_line.py` (criterion 2), with `python_argv`, `Recorder` and `is_gone` of `tests/process_support.py`.

No earlier test changes.

## Acceptance criteria

1. One parametrized test. The stand-in prints a `step_start` on standard output and waits `WAIT_SECONDS`; the line on standard error comes first (`stderr_first`). Each row checks the end reason and `limit_wait`, and that the run ended within `BOUND_SECONDS`:
   - `HTTP 428 spend limit reached, retry after 120 seconds`: `provider_limit`, `limit_wait` 120 seconds;
   - `HTTP 428 Precondition Required: try again in 7 minutes`: `provider_limit`, `limit_wait` 420 seconds;
   - `HTTP 428 Precondition Required`: `provider_limit`, `limit_wait` `None`;
   - `HTTP 500 Internal Server Error, retry after 120 seconds`, with a stand-in that ends with a valid result block instead of waiting: `completed`, `limit_wait` `None`.
2. One parametrized test of `run_streaming` with a `Recorder` that stops on `go`, and a time limit of 30 seconds. The child writes the stream's last line without a newline, flushes it, closes that stream and then sleeps 60 seconds with the other stream open:
   - row `stdout`: the last line `go` on standard output. The recorder's calls are exactly `[("stdout", "go")]`, `stopped` is `True`, `exit_status` `None`, `timed_out` `False`, the call returns within 10 seconds, and the child is gone afterwards (`is_gone`);
   - row `stderr`: the same on standard error, with the calls `[("stderr", "go")]`;
   - row `no-stop`: the last line `gone` on standard output, after which the child exits 0 at once instead of sleeping. The calls are exactly `[("stdout", "gone")]`, `stopped` is `False` and `exit_status` is `0`.
3. `make check` stays green.
4. docs: `docs/project-guide/agents.md` (*The opencode runtime*), the passage on a provider limit: one sentence saying that a limit line on standard error gives `limit_wait` from the wait it names, as an `error` event does. `docs/project-guide/processes-and-checks.md`, the paragraph on `run_streaming`: one sentence saying that a stop on a last line without a newline stops the call as a complete line does, and its `Tests:` line names `tests/adapters/test_process_streaming_last_line.py`. The documenter adds each only where the passage does not already say it.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work" "$d/state"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
printf '%s\n' '{"type":"step_start","timestamp":1000,"sessionID":"ses_s","part":{"type":"step-start"}}'
echo "HTTP 428 spend limit reached, retry after 120 seconds" >&2
sleep 30
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import sys, time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.process import ProcessRequest, run_streaming
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="anthropic/claude-sonnet-5-5", tools=["Bash"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
started = time.monotonic()
result = OpencodeRuntime(str(d / "opencode"), d / "state").run(request)
print(result.end_reason, result.limit_wait, result.session, time.monotonic() - started < 10)
child = "import os, sys, time; sys.stdout.write('go'); sys.stdout.flush(); os.close(1); time.sleep(60)"
seen = []
started = time.monotonic()
stopped = run_streaming(ProcessRequest(argv=[sys.executable, "-c", child], cwd=d, time_limit=timedelta(seconds=30)), lambda stream, line: seen.append((stream, line)) is None and line == "go")
print(seen, stopped.stopped, stopped.exit_status, stopped.timed_out, time.monotonic() - started < 10)
EOF
```
Expect: two lines, `provider_limit 0:02:00 ses_s True` and `[('stdout', 'go')] True None False True`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says a limit line on standard error must hold the status "as a whole number". No criterion covers the failing side of that clause. Criterion 1's last row uses `HTTP 500`, which is a different status, not a number that merely contains 428. Two coders could read the clause two ways, for example a substring match against a whole-number match, and both would pass the tests. Options: (a) add a row to criterion 1 for a line such as `HTTP 4281 Precondition Required, retry after 120 seconds`, with a stand-in that ends with a valid result block: `completed`, `limit_wait` `None`; (b) drop "as a whole number" from the Interface. I would choose (a), with the new criterion placed before the two closing ones.

   Everything else I checked is fine, as follows.
   - Interface: it names concrete modules and signatures, and no `src/` module changes.
   - Criteria: each is testable by one function, and each rule's passing and failing sides are covered, apart from the point above.
   - Smoke test: the commands are runnable, and the `Expect:` line is checkable against the printed output.
   - Architecture: the new tests sit under `tests/adapters/`, as `CLAUDE.md` requires, and they import the shared helpers.
   - Scope: the story is within F0020's scope, and no earlier test changes.

   The format check passed.
