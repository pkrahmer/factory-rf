---
stage: review
pr: 140
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A timed-out run as the agent user

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`ClaudeCodeRuntime` turns a refused `sudo` into `AgentRuntimeError`. The rule comes from F0010-S0014's Interface: when a call as `os_user` ends without a result, a standard-error line that starts with `sudo:` is a refusal. The runtime counts a call that timed out as one without a result, as `_result` does. S0014's reviewer (entry 5, finding 1) found that the coder had left timed-out calls out of the rule. The coder fixed it in `0ebb835`: `_sudo_refusal` returns `None` only for a parsed reply from a call that did not time out.

No test pins that fix. The feature acceptance's hand mutation pass dropped `and not process.timed_out` from `_sudo_refusal` (`src/factory/adapters/claude_runtime.py:293`), and the whole test suite stayed green. The rows of S0014's criteria 8, 9 and 15 all finish within their time limit.

This story pins both sides of the rule for a call that reaches its `time_limit`. It is tests only: the code already behaves as the criteria say, and the coder expects to change nothing in `src/`.

The rule stays as S0014's Interface has it (the human's call, taken with the default of the feature acceptance's section 6, point 8): a run that times out while `sudo` printed a harmless warning (`sudo: unable to resolve host x`) is an `AgentRuntimeError`, which takes the crash path, not the end reason `time_limit`. The kill of a call under the real `sudo` is not enforced anyway (FEATURE.md decision 30, out of scope); this story pins only how the runtime reads a call that reached its limit, with stand-ins that the test's own user can kill.

## Interface

No new or changed names in `src/`. The behaviour pinned is that of `ClaudeCodeRuntime(executable, state_directory, sudo_executable=<stand-in>).run(request)`, with `request.os_user == "agent"` and `request.time_limit == timedelta(seconds=1)`, and a `sudo` stand-in that runs the agent stand-in. The agent stand-in is `write_stand_in(<directory>, [Step(stdout_before_wait=REPLY, wait_seconds=60)])`: it prints the module's `REPLY` and flushes it, then waits past the limit and is killed:

- When the stand-in `sudo` writes a line that starts with `sudo:` to standard error, `run` raises `AgentRuntimeError`. Its `detail` holds that line.
- When the stand-in writes no such line, `run` returns a result with `end_reason == "time_limit"`, and its `decision` and `entry` are `None`.

`Step` in `tests/adapters/claude_stand_in.py` gains one field, `stdout_before_wait: str = ""`, which the stand-in script writes to standard output and flushes before its wait; nothing else in that file changes (FEATURE.md decision 37). Without it the stand-in prints only after its wait, so a killed call's standard output is empty and the rule's timed-out side is never reached. The tests go in `tests/adapters/test_claude_runtime_os_user.py`, built from its `_write_sudo` (its `warning` parameter), `_request` (with `time_limit` replaced) and `REPLY`. S0014's tests stay as they are.

## Acceptance criteria

1. A call as `agent` that reaches its `time_limit` of 1 second, while the `sudo` stand-in has written `sudo: unable to resolve host x` to standard error, raises `AgentRuntimeError` whose `detail` contains `sudo: unable to resolve host x`. This holds even though the agent stand-in printed a reply before it waited.
2. The same call without the warning ends with `end_reason == "time_limit"`, `decision is None` and `entry is None`, and raises nothing. Criteria 1 and 2 are the two rows of one parametrized test.
3. `make check` stays green.
4. docs: none. `docs/operator-guide.md` and `docs/decisions.md` already state the refusal rule. F0010-S0018 adds it to the project guide.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_os_user.py
```
Expect: the last line is `10 passed in <time>` (8 tests before this story, and the two rows of criteria 1 and 2).

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: no new names in src/; it pins `ClaudeCodeRuntime(...).run` with `os_user="agent"` and `time_limit=1s`, and adds one field, `Step.stdout_before_wait`, to `tests/adapters/claude_stand_in.py`. FEATURE.md decision 37 allows that change. `Step` currently lacks the field. `_sudo_refusal` at claude_runtime.py:293 does carry `not process.timed_out`, as the story says.
   - Criteria: criterion 1 is the refused side (a `sudo:` line leads to `AgentRuntimeError`, with the line in `detail`). Criterion 2 is the passing side (`end_reason == "time_limit"`, `decision` and `entry` None). Both are rows of one parametrized test, and each is testable. Criteria 3 and 4 are the closing two.
   - Demo: the pytest command is runnable. The expected `10 passed` matches the 8 tests now in the file plus the 2 rows. I counted 8 `def test_` functions.
   - Architecture: tests only, in `tests/adapters/`, which mirrors `factory.adapters`. Nothing crosses a layer.
   - Scope: the story is inside F0010 (S0022 is listed in FEATURE.md). The kill of a call under the real `sudo` stays out of scope (decision 30), and the story says so.
3. tester: Wrote the tests for the timed-out side of the sudo-refusal rule. They are green, not red: this is a tests-only story, and the code already has the fix (`not process.timed_out` in `_sudo_refusal`, from 0ebb835). So the only failure expected is the mutation the story describes.
   - criterion 1: tests/adapters/test_claude_runtime_os_user.py::test_a_timed_out_call_with_a_sudo_line_is_a_runtime_error_and_without_one_a_time_limit, row `warning="sudo: unable to resolve host x\n"`. It expects `AgentRuntimeError`, and its `detail` must contain that line.
   - criterion 2: the same test, row `warning=None`. It expects `end_reason == "time_limit"`, `decision is None` and `entry is None`.
   - Both rows use `_write_sudo(warning=...)`, `_request(tmp_path, "agent")` with `time_limit` set to 1 second through `model_copy`, and `write_stand_in(..., [Step(stdout_before_wait=REPLY, wait_seconds=60)])`.
   - Files changed:
     - tests/adapters/claude_stand_in.py: `Step` gains `stdout_before_wait: str = ""`. The script writes and flushes it before the wait. The docstring now says "print, wait, print".
     - tests/adapters/test_claude_runtime_os_user.py: the new parametrized test.
   - Modules the runner could not import: none.
   - `make test` output: "test: green", total coverage 99.54 %. `make lint` is green after `ruff format`.
   - I did not rerun with the mutation applied, because this stage allows one test run. The reviewer or demo may want to confirm that dropping `and not process.timed_out` makes the first row fail.
   - Nothing in `src/` needs changing. The coder only has to run `make check`.

   `make lint`: lint: green
   `make test`: test: green
4. coder: Nothing to build. This is a tests-only story, and `src/` already behaves as the criteria say: `_sudo_refusal` in `src/factory/adapters/claude_runtime.py` has `and not process.timed_out`, from 0ebb835. The tester's parametrized test in `tests/adapters/test_claude_runtime_os_user.py`, together with `Step.stdout_before_wait` in `tests/adapters/claude_stand_in.py`, is green. I ran `make check` on the committed state and it is green: every check passed, coverage 99.54 %.
   - I made no commits because there was no change to commit. The refactor pass had no diff of mine to review.
   - Open: I tried to confirm that the new test catches the mutation (drop `and not process.timed_out` and expect the first row to fail). The permission layer denied that command before it ran, so the working tree is still clean and untouched. The mutation check is still not done. The reviewer or the demo should run it by hand.

   `make check`: check: green
