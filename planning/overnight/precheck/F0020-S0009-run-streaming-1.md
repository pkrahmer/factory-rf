# Pre-check F0020-S0009 (run_streaming), round 1: run_streaming keeps a long output and a line split across reads

Story: `factory/features/F0020-opencode-as-a-second-agent-runtime/backlog/F0020-S0009-run-streaming-keeps-a-long-output-and-a-line-split-across-reads.md` (not changed). Proposed by F0020-A0001 on 2026-10-19.

This file is not `F0020-S0009-1.md`, because that name already holds the pre-check of the deferred spend-window story, which has the same id (finding 1).

I played the story against v1.1's `claude/agents/intake.md` and `factory/story-form.md`, and predicted the later stops from `claude/agents/*.md`. The code facts were checked on a copy of today's checkout (F0022-S0001 merged) in `%TEMP%\prop7`, converted to LF, in throwaway `factory-self-factory` containers (`--network none --cpus 1`). pytest came from the `factory-self_work` volume's environment, mounted read-only, and the copy's `src` was put first on `PYTHONPATH`.

## What I ran

- **Form.** `factory-check-story <story>` gave `ok`, exit 0.
- **Code facts.** All hold:
  - `factory.adapters.process`: `_READ_SIZE = 65536`.
  - `_LineReader.read_ready` holds `self.read_bytes[stream] += chunk` and `self._pending[stream] += chunk` (lines 126-127).
  - `run_streaming(request, on_line) -> ProcessResult` takes its `stdout` and `stderr` from `read_bytes`.
  - `python_argv(code, *args)` is in `tests/process_support.py`.
  - `tests/adapters/test_process_streaming_reads.py` does not exist yet.
  - The paragraph on `run_streaming` is in `docs/project-guide/processes-and-checks.md` (line 57). It does not yet say "whole however many reads".
- **Prototype tests** of criteria 1 and 2 (two parametrized tests, 4 rows):
  - Today's code: 4 passed in about 1 s.
  - Mutant `read_bytes[stream] = chunk`: all 4 fail.
  - Mutant `_pending[stream] = chunk`: all 4 fail.
  - Criterion 1 alone kills both mutants for certain. `print('x' * 200000)` crosses the 64 KiB pipe in at least four reads. Criterion 2 kills them only when the parent reads within the child's 0.5 s pause. Under load the two pieces can land in one read: the test then still passes, just more weakly. It is not flaky.
- **Smoke test** (with `python` in place of `uv run -q python`) on today's code: `[('stdout', 200000)] 200001` and `[('stderr', 'hello'), ('stdout', '{"a":1}')] '{"a":1}\n' 'hello\n'`. These are exactly the `Expect:` lines. The story changes no code, so the smoke test already passes before the story.
- **Leaves.** The story says "No earlier test changes".
  - The new module needs a recording callback.
  - The only one today is `Recorder` in `tests/adapters/test_process_streaming.py` (F0020-S0003's), with `calls`, `threads` and `stop_on`.
  - A test-local copy is what the reviewer's lesson counts as a finding at round 0 ("Count a second copy of an existing helper as a finding").
  - The standing leave of `CLAUDE.md` allows moving it to `tests/process_support.py`. That changes an earlier module, so the story should say so (finding 2).

## Intake outcome (as v1.1's intake would end)

Format check: passed. Likely `tests`, entry starting `accepted`:

- **Interface:** no module changes. `run_streaming`'s signature and its two pinned rules are named, as are the new test module and `python_argv`.
- **Criteria:** 1 and 2 are each one parametrized test with a standard-output row and a standard-error row, with exact lengths and texts. These are pins with no refused side.
- **Smoke test:** one block, runnable from the root, with two exact lines.
- **Architecture:** tests only, in `tests/adapters/`, which mirrors `factory.adapters.process`.
- **Scope:** `process.py` (`run_streaming`) is in F0020's Scope. Nothing in Out of scope is touched.

Possible question (about 1 in 3): `feature.md` gives S0009 to "The factory keeps its spend within a window before each run (deferred, decision 15)". Its Scope bullets also cite "(S0009)" for `spend.py` and `FACTORY_SPEND_WINDOW`. The intake reads `feature.md` and may ask which S0009 this is. F0020-A0001's report says itself: "collides with the deferred S0009 in `planning/`. The human renumbers."

## Predicted later stops, by role

- **tester:** writes the module. Its tests pass at once, because the story pins behaviour the code already has (as in F0019-S0008, entry 5). The entry says so. `make lint` is green.
  - Without edit 2, it writes its own recorder (a lambda or a class).
- **coder:** builds nothing. The entry says no file under `src/` changed. `make check` is green.
- **reviewer:** with edit 2, no findings, and item 6 names `tests/adapters/test_process_streaming.py` under the standing leave. Without it, a likely round-0 finding: a copy of `Recorder`.
- **documenter:** one sentence in `processes-and-checks.md`. `documents ok`.
- **smoke tester:** both lines met (verified above).
- Cost: about 6 runs, under $2.

## Verdict

`F0020-S0009 (run_streaming): pass with two edits (1 recommended before start, 2 recommended)`

**Edit 1 (recommended before start, the human's rename; no text inside changes).** Rename `factory/features/F0020-opencode-as-a-second-agent-runtime/backlog/F0020-S0009-run-streaming-keeps-a-long-output-and-a-line-split-across-reads.md` to `factory/features/F0020-opencode-as-a-second-agent-runtime/backlog/F0020-S0012-run-streaming-keeps-a-long-output-and-a-line-split-across-reads.md`. The id S0009 stays with the deferred spend window, which `feature.md` (Scope, Stories, decision 15) and `planning/overnight/stories/F0020-*/deferred/` cite. Otherwise, once the deferred story is built, two files in `done/` would carry `F0020-S0009`.

**Edit 2 (recommended).** In `## Interface`, replace:

> Tests (the tester writes them): `tests/adapters/test_process_streaming_reads.py` (new), with real Python child processes and the helper `python_argv` from `tests/process_support.py`, imported, not copied. No earlier test changes.

with:

> Tests (the tester writes them): `tests/adapters/test_process_streaming_reads.py` (new), with real Python child processes, the helper `python_argv` from `tests/process_support.py` and the callback `Recorder`, imported, not copied. Under the standing leave of `CLAUDE.md` (*Tests*) the tester moves `Recorder` from `tests/adapters/test_process_streaming.py` to `tests/process_support.py`, and `tests/adapters/test_process_streaming.py` imports it from there; its tests keep their names and what they check. No other earlier test changes.
