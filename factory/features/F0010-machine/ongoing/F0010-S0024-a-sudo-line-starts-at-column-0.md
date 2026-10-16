---
stage: demo
pr: 143
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A sudo line starts at column 0

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`ClaudeCodeRuntime` turns a refused `sudo` into `AgentRuntimeError`. It does so when a call as `os_user` ends without a usable reply and standard error holds a line that *starts* with `sudo:` (`_sudo_line` in `src/factory/adapters/claude_runtime.py`, `SUDO_PREFIX`). `docs/operator-guide.md` and `docs/decisions.md` state the same rule. Any other failure without a reply is the end reason `died`, which is a stall, not an error.

The tests cover only one side of "starts with". The feature acceptance's hand mutation pass replaced `line.startswith(SUDO_PREFIX)` with `SUDO_PREFIX in line`, and the whole suite stayed green. Under that mutant, a dead run whose standard error says `bash: sudo: command not found`, or carries an indented `sudo:`, becomes an `AgentRuntimeError` that takes the error path instead of the stall path. `CLAUDE.md` asks for every limit to be tested on both sides, "at column 0" with an indented case.

This story is tests only: the code already behaves as the criteria say, and the coder expects to change nothing in `src/`.

## Interface

No new or changed names in `src/`. The behaviour pinned is that of `ClaudeCodeRuntime(executable, state_directory, sudo_executable=<stand-in>).run(request)` with `request.os_user == "agent"`, where the `sudo` stand-in writes a given text to standard error and exits 1 without running the agent (`_write_sudo(directory, (stderr, 1))` in `tests/adapters/test_claude_runtime_os_user.py`):

- When standard error holds a line that starts with `sudo:` at column 0, `run` raises `AgentRuntimeError`, and its `detail` holds that line.
- When the only `sudo:` on standard error is inside a line (`bash: sudo: command not found`) or after leading whitespace (`  sudo: a password is required`), `run` returns a result with `end_reason == "died"` and raises nothing.

The test goes in `tests/adapters/test_claude_runtime_os_user.py`, built from its `_write_sudo`, `_runtime` and `_request`. It replaces F0010-S0014's `test_a_sudo_refusal_is_a_runtime_error_naming_its_line`, whose case is criterion 1's row (FEATURE decision 38); the other tests stay as they are.

## Acceptance criteria

1. A call as `agent` whose `sudo` stand-in writes `sudo: a password is required` at column 0 and exits 1 raises `AgentRuntimeError`, and its `detail` contains `sudo: a password is required`.
2. The same call with `bash: sudo: command not found` instead ends with `end_reason == "died"` and raises nothing.
3. The same call with `  sudo: a password is required` (two leading spaces) instead ends with `end_reason == "died"` and raises nothing. Criteria 1 to 3 are the three rows of one parametrized test, which replaces `test_a_sudo_refusal_is_a_runtime_error_naming_its_line`.
4. `make check` stays green.
5. docs: none. `docs/operator-guide.md` ("a line that starts `sudo:`") and `docs/project-guide.md` already state the rule.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_os_user.py
```
Expect: the last line is `12 passed in <time>`: the 9 tests before this story that stay, and the three rows of criteria 1 to 3.

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: no new names in `src/`. It pins `ClaudeCodeRuntime.run` with `os_user == "agent"` against the existing `_write_sudo`, `_runtime` and `_request` helpers (all present in `tests/adapters/test_claude_runtime_os_user.py`). It states the two outcomes: `AgentRuntimeError` with the line in `detail`, or `end_reason == "died"` with nothing raised.
   - Criteria: criteria 1 to 3 are the three rows of one parametrized test, and each row is testable on its own. The rule "starts with `sudo:` at column 0" has its passing side (criterion 1) and two failing sides (criteria 2 and 3: a mid-line `sudo:` and an indented one). Criterion 4 (`make check` stays green) and criterion 5 (docs: none) close the list.
   - Demo: the command is runnable. I counted the expected `12 passed`. The file has 9 test functions, and the last one has 2 parametrized rows, so 10 tests run today. Replacing `test_a_sudo_refusal_is_a_runtime_error_naming_its_line` leaves 9, and the 3 new rows make 12.
   - Architecture: the change is tests only, in `tests/adapters/`, which mirrors `factory.adapters`. The story does not touch layers or wrappers.
   - Scope: the story fits F0010 and is listed in `FEATURE.md` as S0024. Replacing the old test needs the human's leave. That leave is recorded in FEATURE decision 38, which names exactly this replacement.
3. tester: Replaced `test_a_sudo_refusal_is_a_runtime_error_naming_its_line` in `tests/adapters/test_claude_runtime_os_user.py` with one parametrized test that has three rows. The ticket's Interface and FEATURE decision 38 name this replacement. The test uses the file's existing `_write_sudo`, `_runtime` and `_request` helpers, and nothing else in the file changed.
   - criterion 1: tests/adapters/test_claude_runtime_os_user.py::test_only_a_line_starting_with_sudo_makes_a_failure_a_runtime_error[sudo: a password is required-True]. `run` raises `AgentRuntimeError`, and `detail` contains the line.
   - criterion 2: the same test, row `[bash: sudo: command not found-False]`: `end_reason == "died"` and nothing is raised.
   - criterion 3: the same test, row `[  sudo: a password is required-False]` (two leading spaces): `end_reason == "died"` and nothing is raised.
   - criterion 4: `make check`. I ran `make test` and `make lint`, and both are green. I skipped the type check, as the stage says.
   - criterion 5: no test (docs: none).
   Files changed: tests/adapters/test_claude_runtime_os_user.py. I created no new files. The test runner imported every module.
   The tests pass, not fail: this story is tests only, and the code (`_sudo_line` uses `startswith`) already behaves as the criteria say. The rows for criteria 2 and 3 are the ones that catch the `SUDO_PREFIX in line` mutant. The coder should not need to change anything in `src/`. The file should now have 12 tests (9 that stayed plus 3 rows), which matches the Demo. I did not count them in a separate run, because the stage allows only one `make test`.

   `make lint`: lint: green
   `make test`: test: green
4. coder: No change in `src/`. As the ticket expected, this story only adds tests. `_sudo_line` in `src/factory/adapters/claude_runtime.py` already uses `line.startswith(SUDO_PREFIX)`, so the tester's parametrized `test_only_a_line_starting_with_sudo_makes_a_failure_a_runtime_error` passes on all three rows: a line with `sudo:` at column 0 raises `AgentRuntimeError`, while one with `sudo:` mid-line or indented ends with the end reason `died`.
      - Verified: `make check` is green (total coverage 99.54 %). The demo file `tests/adapters/test_claude_runtime_os_user.py` runs 12 tests, all passing, which matches the Demo.
      - Refactor: there is no diff of mine to review, so I made no refactor commit and no commit at all.
      - Rejected: tightening the code, for example by stripping lines before matching. That would turn the indented case into an error and contradict criterion 3.
      - Noticed but did not touch: coverage still misses `claude_runtime.py` lines 384 and 408-409. These are outside this story.

   `make check`: check: green
5. reviewer: No findings.
   - Acceptance criteria: criteria 1 to 3 are the three rows of `test_only_a_line_starting_with_sudo_makes_a_failure_a_runtime_error` in `tests/adapters/test_claude_runtime_os_user.py`. It replaces `test_a_sudo_refusal_is_a_runtime_error_naming_its_line`, as the Interface and FEATURE decision 38 allow. Row 1 checks that `AgentRuntimeError` is raised and that `detail` holds the line. Rows 2 and 3 (`sudo:` mid-line, and indented by two spaces) check `end_reason == "died"` and nothing raised. Both failing sides of "starts at column 0" are covered. I read `_sudo_line` in `src/factory/adapters/claude_runtime.py:283`: with the `SUDO_PREFIX in line` mutant, rows 2 and 3 would raise, so the test catches it. The stand-in comes from `_write_sudo(dir, (stderr, 1))`, which exits 1 without a reply, so the code reaches the died path. The coder's entry reports `make check` green and 12 tests in the demo file.
   - Architecture and security: the diff touches only tests and adds no suppression markers.
   - Quality: the test reuses the file's `_write_sudo`, `_runtime` and `_request` helpers. Each side of the rule is a row of one parametrized test, as `CLAUDE.md` asks.
   - Ticket hygiene: the Assignment matches what was built (no change to `src/`). The coder's entry says what was rejected: stripping lines before matching, which would contradict criterion 3. Criterion 5 (docs: none) still holds, because the operator guide and the project guide already state the rule.
6. documenter: Docs criterion is `none`, so I wrote nothing. No files changed.
   - Cross-read against the diff (tests only, no change in `src/`): `docs/operator-guide.md` line 90 ("a line that starts `sudo:`"), `docs/project-guide.md` line 300 ("a standard-error line starting with `sudo:`") and `docs/decisions.md` line 293. All three state the rule as the code and the new test implement it. Other mentions in the operator guide (lines 109 and 257) are consistent with it.
   - `make check` is green (coverage 99.54 %).
   - Findings: none. Nothing stale seen.

   `make check`: check: green
