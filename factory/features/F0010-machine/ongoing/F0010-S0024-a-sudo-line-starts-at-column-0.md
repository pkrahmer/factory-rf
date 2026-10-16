---
stage: tests
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
