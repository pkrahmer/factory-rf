---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 297
comments_read: [6279096558]
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T23:03:54.212628Z'
  lease_duration: 60
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T22:51:56.041325Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T22:52:13.780524Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T22:52:29.188918Z'
  stage: intake
  run: 29fa665e0b1f4342993a9172adc129db
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T22:52:49.376894Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T22:55:12.950010Z'
  stage: tests
  run: e2dcf3b2f1494ea9b7e85d8e299f5161
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T22:55:33.281633Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-19T22:57:27.729919Z'
  stage: doing
  run: 012d6396d4324340bc5f736d6bd0a970
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-19T22:57:48.225681Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-19T22:58:33.421672Z'
  stage: review
  run: 8f538ac2678e45048955757479851abd
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-19T22:58:53.693593Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-19T22:59:12.517622Z'
  stage: doing
  run: 30eccef766474876a9ae9e9c60f0ab6b
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-19T22:59:32.769074Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-19T23:01:20.574439Z'
  stage: tests
  run: 4c2ec8b77b324468812a76ec23d31103
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-19T23:01:40.760924Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-19T23:03:33.581329Z'
  stage: doing
  run: ca9f061fad454930ac3c16e295e0f340
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-19T23:03:54.212628Z'
  stage: review
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
   - `HTTP 500 Internal Server Error, retry after 120 seconds`, with a stand-in that ends with a valid result block instead of waiting: `completed`, `limit_wait` `None`;
   - `HTTP 4281 Precondition Required, retry after 120 seconds`, with a stand-in that ends with a valid result block instead of waiting: `completed`, `limit_wait` `None` (the status must be a whole number, not part of a longer one).
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
4. 2026-10-19 human: (a). Add a row to criterion 1 for a line such as `HTTP 4281 Precondition Required, retry after 120 seconds`, with a stand-in that ends with a valid result block: `completed`, `limit_wait` `None`. Place it before the two closing rows. This follows CLAUDE.md's rule that every limit the Interface states is tested on both sides.
5. factory: started intake as self.
6. intake: accepted
   - Interface: names concrete modules and signatures (`OpencodeRuntime.run`, `run_streaming(request, on_line) -> ProcessResult`); no `src/` module changes. The "whole number" clause now has its failing side (see below).
   - Criteria: each is testable by one parametrized function. Every rule has both sides: a limit line with the status gives `provider_limit`, and a line without it (HTTP 500, or 4281) is no limit. The wait is covered in three forms (named in seconds, named in minutes, none). A stop on a last line is covered on stdout and stderr, and the no-stop row covers the other side. Carried in from journal entry 4 (the human's answer (a)): I added a row to criterion 1 for `HTTP 4281 Precondition Required, retry after 120 seconds`, with a stand-in that ends with a valid result block: `completed`, `limit_wait` `None`. It sits inside criterion 1, before the two closing criteria. That is the human's edit carried in, not my improvement.
   - Smoke test: the commands are runnable and the `Expect:` line is checkable against the two printed lines.
   - Architecture: the new tests sit under `tests/adapters/`, as `CLAUDE.md` requires. They import the shared helpers and change no earlier test.
   - Scope: within F0020's scope, which covers the opencode runtime and `process.py` streaming. Nothing in the feature's Out of scope is touched.
7. factory: started tests as self.
8. tester: Wrote the two new test modules that the Interface names. They import the shared helpers and copy none. No earlier test changed.

   - criterion 1: tests/adapters/test_opencode_limit_wait_on_stderr.py::test_a_limit_line_on_standard_error_gives_the_wait_it_names. It has five rows: `seconds` (provider_limit, 120 s), `minutes` (provider_limit, 420 s), `no-wait` (provider_limit, None), `500` (completed, None) and `4281` (completed, None). Each row puts its line on standard error first through `stand_in_runtime(..., stderr_first=...)`. The provider_limit rows use a stand-in that prints a `step_start` and waits `WAIT_SECONDS`. The completed rows use one that ends with a valid result block. Every row checks the end reason and `limit_wait`, and that the run ended within `BOUND_SECONDS`.
   - criterion 2: tests/adapters/test_process_streaming_last_line.py::test_a_stop_on_a_last_line_without_a_newline_stops_the_call_at_once. It has three rows: `stdout`, `stderr` and `no-stop`. The `Recorder` stops on `go` and the time limit is 30 s. The child writes its pid to a file in `tmp_path`, writes the last line to fd 1 or 2 with no newline, closes that descriptor, and then either sleeps 60 s (the stop rows) or calls `os._exit(0)` (the no-stop row). `os._exit` keeps Python's exit-time flush from writing anything to standard error. Every row checks that the calls are exactly `[(stream, line)]`, plus `stopped` and `exit_status`. The stop rows also check `timed_out` is False, that the call returns within 10 s, and that the child is gone (`is_gone`).
   - criteria 3 and 4 (make check, docs): no test, as they belong to the coder and the documenter.

   Files created: tests/adapters/test_opencode_limit_wait_on_stderr.py, tests/adapters/test_process_streaming_last_line.py.

   Modules the test run could not import: none. This story pins behaviour that already exists and changes no code, so the new tests pass as soon as they are written. `make test` was green, not red, and that is expected here. I could not check that the tests are red under the two mutants the Description names, because the stage does not run `make mutants`. `make lint` is green. I skipped `make types`, as this stage says to.

   Set aside: the separate `then` column in criterion 2's table. Ruff's PLR0917 refused six positional parameters, so the test now picks "sleep" or "exit" from the `stopped` column.

   Nothing was open to interpretation.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.2 s)
9. factory: started doing as self.
10. coder: Built nothing. The story pins behaviour that already exists, and its Interface says no module under `src/factory/` changes. The tester's two new modules, `tests/adapters/test_opencode_limit_wait_on_stderr.py` and `tests/adapters/test_process_streaming_last_line.py`, already pass against the current `src/factory/adapters/opencode_runtime.py` and `src/factory/adapters/process.py`. I ran `make check` in the foreground and it ended `check: green`, with `test: green (40.0 s)` and coverage at 99.13 %.

    Main choice: I left the code as it is. The alternative I rejected was changing the code to make the tests "need" it, which would go beyond the story's scope (R13).

    Refactor: there is no diff under `src/` (git status shows only the factory's costs sidecar), so there was nothing to refactor.

    Description: the journal changed it once. The human's answer (entry 4) added the `4281` row to criterion 1, and intake already carried that into the Description. I did not rewrite it.

    Noticed but did not touch: I did not check whether the new tests fail under the two mutants the Description names. No stage runs `make mutants`, so that check is left for the human's next sweep.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`, which adds two test modules, against the work item. I read the tests against criteria 1 and 2 and checked the shared helpers they import (`tests/adapters/opencode_stand_in.py`, `tests/adapters/claude_stand_in.py`, `tests/process_support.py`). Group 1 holds:
    - Criterion 1 has all five rows, and each row checks `end_reason`, `limit_wait` and `BOUND_SECONDS`. The `seconds` and `minutes` rows would catch the `_stop_at_limit(None)` mutant.
    - Criterion 2 has the rows `stdout`, `stderr` and `no-stop`, with the exact calls and the stop fields. In the stop rows the other stream stays open while the child sleeps for 60 s, so the `return False` mutant would hit the 30 s limit and fail the 10 s bound.
    - The "whole number" rule has its failing side in the `4281` row.
    - The coder's `make check` was green (journal entry 10).

    Groups 2 and 3 hold: the change is test-only, it has no secrets, and the `# noqa: FBT001` it carries is a lint marker, not one of the security markers that need asking. Group 4 fails:

    1. `tests/adapters/test_opencode_limit_wait_on_stderr.py:24`: `REPLYING = Step(stdout=stdout(step_start(), text(result_text()), step_finish()))` is another copy of the reply constant that earlier modules already hold. It matches `REPLY` in `tests/adapters/test_opencode_resumed_words.py:38` exactly, and its `stdout(...)` part is `REPLY` in `tests/adapters/test_opencode_provider_limit.py:33` and six more modules. Fix (tester, under the standing leave): define the reply once in `tests/adapters/opencode_stand_in.py` and import it in the new module. The story says no earlier test changes, so the earlier modules can keep their copies for now.

    Earlier tests: none. Both test files in the diff are new (status `A`), and no file that `main` already holds was changed, renamed or deleted.
13. factory: started doing as self.
14. coder: Round 1 has one finding, the reviewer's group 4 finding in entry 12. It is about a copied test helper, so it is a change to the tests, and the coder makes no test changes (R9). I changed no code. The working tree holds nothing of mine.

    The change for the tester comes under CLAUDE.md's standing leave to move a shared test helper:
    - Define the reply step once in `tests/adapters/opencode_stand_in.py`, under the name `REPLY`, after the step helpers it uses: `Step(stdout=stdout(step_start(), text(result_text()), step_finish()))`.
    - In `tests/adapters/test_opencode_limit_wait_on_stderr.py`, delete the module's own `REPLYING` constant (line 24). Import `REPLY` from `tests.adapters.opencode_stand_in` instead, and use it in the `500` and `4281` rows.
    - No earlier test file changes. The Interface says no earlier test changes, and the reviewer's fix keeps the earlier copies for now: `tests/adapters/test_opencode_resumed_words.py:38`, and the `REPLY` constants in `tests/adapters/test_opencode_provider_limit.py:33` and six more modules.

    Main choice: I end with `tests` rather than `question`. CLAUDE.md gives a standing leave for this move, so the human's word is not needed (see the Lessons). The alternative I rejected was asking the human whether the earlier copies should go as well. That would go beyond the story's "No earlier test changes".

    Description: the journal does not change the meaning of the task. The reviewer's finding moves a test constant and adds no criterion, so I did not rewrite the Description.

    Refactor: none, since there is no diff under `src/`.

    Noticed but did not touch: the earlier test modules still hold their own copies of the reply constant. Removing them would be a story of its own.
15. factory: started tests as self.
16. tester: I made the move named in the coder's entry 14, under CLAUDE.md's standing leave to move a shared test helper. It answers the reviewer's group 4 finding in entry 12.

    - `tests/adapters/opencode_stand_in.py`: I added `REPLY = Step(stdout=stdout(step_start(), text(result_text()), step_finish()))` at the end of the module, after the step helpers it uses.
    - `tests/adapters/test_opencode_limit_wait_on_stderr.py`: I deleted the module's own `REPLYING` constant. The module now imports `REPLY` from `adapters.opencode_stand_in` and uses it in the `500` and `4281` rows. I also dropped the imports the constant alone used (`result_text`, `step_finish`, `text`).

    No earlier test file changed. `opencode_stand_in.py` is a shared helper module, not a test, and the earlier modules keep their own copies of the reply constant, as the Interface ("No earlier test changes") and the reviewer's fix ask.

    The criterion mapping is unchanged:
    - criterion 1: `tests/adapters/test_opencode_limit_wait_on_stderr.py::test_a_limit_line_on_standard_error_gives_the_wait_it_names`
    - criterion 2: `tests/adapters/test_process_streaming_last_line.py::test_a_stop_on_a_last_line_without_a_newline_stops_the_call_at_once`

    Files created: none in this round. Modules the test run could not import: none. The story changes no code, so the tests pass as they did before.

    `make test` is green (coverage 99.13 %) and `make lint` is green. I skipped `make types`, as this stage says to.

    `lint`: lint: green (0.0 s)
    `test`: test: green (45.4 s)
17. factory: started doing as self.
18. coder: Round 1, after the tester's move. The reviewer's only finding (entry 12, the copied reply constant) is answered by the tester's entry 16: `REPLY` now lives in `tests/adapters/opencode_stand_in.py`, and `tests/adapters/test_opencode_limit_wait_on_stderr.py` imports it. I changed no code. That is what the story asks for: the Interface says no module under `src/factory/` changes, and the two new test modules pass against the current `src/factory/adapters/opencode_runtime.py` and `src/factory/adapters/process.py`. The working tree holds nothing of mine; `git status` shows only the factory's costs sidecar.

    I ran `make check` in the foreground and it ended `check: green`, with `test: green (38.1 s)` and coverage at 99.13 %.

    - **Main choice:** I left the code as it is. The alternative I rejected was going back to the finding myself, which would mean editing tests (R9).
    - **Refactor:** I didn't do one, because there is no diff under `src/`.
    - **Description:** the journal does not change the meaning of the task in this round. The human's `4281` row was already carried in by intake.
    - **Noticed but did not touch:** the earlier opencode test modules still hold their own copies of the reply constant, for example `tests/adapters/test_opencode_provider_limit.py:33` and `tests/adapters/test_opencode_resumed_words.py:38`. Removing them would be a story of its own. Nobody has checked that the new tests fail under the two mutants, because no stage runs `make mutants`; that is left to the human's next sweep.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
19. factory: started review as self.
