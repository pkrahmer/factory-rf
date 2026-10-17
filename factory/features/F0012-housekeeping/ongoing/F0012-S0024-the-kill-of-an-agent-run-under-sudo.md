---
stage: accept
pr: 174
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The kill of an agent run under sudo at its time limit

## Assignment (as of log entry 1)

`run_process` kills the process group of a call at its time limit. When the agent runs as another user, the group's leader is `sudo`, owned by root, which the factory's user may not signal: the kill fails with `PermissionError`, the run becomes an `AgentRuntimeError`, and the `claude` process under `agent` runs on (F0010 decision 30, open until now). The human's answer of 2026-10-17 (item 1.8): `timeout --signal=KILL <limit>` inside the `sudo` call, so that the agent's own user kills its own process tree at the limit; the end read as `time_limit`; and a grace time on the outer call, so that the factory's own kill fires only when the inner one did not. This story builds it in `ClaudeCodeRuntime` (FEATURE decision 27). A call without an operating-system user does not change. It is observed for real at the first start (step 3). One test of F0010-S0014 that pins the head of the `sudo` call changes by the human's leave (FEATURE decision 41).

## Interface

`src/factory/adapters/claude_runtime.py`:

- `TIMEOUT_EXECUTABLE = "timeout"` and `SUDO_GRACE = timedelta(seconds=30)`.
- A request with an `os_user` is started as `[<sudo>, "-n", "-u", <user>, "--", "timeout", "--signal=KILL", "<seconds>s", "env", "-i", <assignments>..., <claude>, <arguments>...]`, where `<seconds>` is the call's time limit in whole seconds rounded up (`30` for 30 s, `2` for 1.5 s). The outer `ProcessRequest`'s `time_limit` is the call's time limit plus `SUDO_GRACE`.
- A call with an `os_user` whose process ended with exit status `137` or `-9` (killed by `SIGKILL`, as `subprocess` reports a signal) after a duration of at least its time limit is a call ended by its time limit: its end reason is `time_limit` and it has no measures (no decision, entry, turns, tokens, cost or model time), exactly as a call the factory's own kill ended. The same exit status before the time limit is not; it is `died`, as today.
- The rule for a `sudo:` line (an `AgentRuntimeError` when the call ended without a usable reply and `sudo` printed a line starting `sudo:`) treats an inner kill like an outer one: a `sudo:` line then stops the run with that error.
- The resume of a budget stop goes through the same call, with what is left of the time limit as its limit.
- A request without an `os_user` is started and limited as today.

Tests: `tests/adapters/test_claude_runtime_sudo_time_limit.py`, with the `sudo` stand-in of `tests/adapters/test_claude_runtime_os_user.py` (its script and helpers may be imported from there), the `claude` stand-in of `tests/adapters/claude_stand_in.py`, and the real `timeout` of coreutils (criteria 1, 2 and 4); for criteria 3, 5 and 6, `run_process` of `factory.adapters.claude_runtime` replaced through pytest's `monkeypatch` by a recorder that keeps each `ProcessRequest` and returns the `ProcessResult` the test gives, as `tests/adapters/test_git_cli_arguments.py` replaces `check_git_argument`. By the human's leave (FEATURE decision 41), and no other change to an earlier story's test: the expected head of the call in `test_with_a_user_sudo_gets_the_user_env_i_the_environment_and_the_executable` becomes `["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]`, with the assignments and the executable after it.

## Acceptance criteria

1. With an `os_user` and a time limit of 30 s, the `sudo` stand-in receives `-n -u agent -- timeout --signal=KILL 30s env -i`, then the assignments, then the `claude` executable; with a time limit of 1.5 s the limit argument is `2s`. Rows of one parametrized test.
2. With an `os_user`, a `claude` stand-in that prints a reply and then waits 60 s under a time limit of 1 s ends with `end_reason == "time_limit"`, no decision, no entry and no measures, and the call took less than the 31 s of the outer limit.
3. With the recorder returning the module's reply on standard output and a time limit of 30 s: with an `os_user`, exit status `137` or `-9` after a duration of 30 s is `time_limit` with no decision, entry or measure; `137` or `-9` after 29.9 s is `died`; exit status `1` after 30 s is `died`; without an `os_user`, `137` after 30 s is `died`. Rows of one parametrized test.
4. With an `os_user`, a `sudo` stand-in that prints `sudo: unable to resolve host x` before the inner kill at the limit raises `AgentRuntimeError` whose detail holds that line (the existing test still passes).
5. With the recorder and a time limit of 30 s, the process request has a time limit of 60 s (30 s and `SUDO_GRACE`) with an `os_user`, and of 30 s without one, whose arguments then hold no `timeout`. Rows of one parametrized test.
6. With an `os_user` and the recorder answering the first call with a budget-stop reply (`subtype` `error_max_budget_usd`) at once, the resume's arguments hold `timeout --signal=KILL 30s` (what is left of 30 s, rounded up) and its process request's time limit is more than 59 s and at most 60 s.
7. Every other test of `tests/adapters/test_claude_runtime_os_user.py`, `tests/adapters/test_claude_runtime.py` and `tests/adapters/test_claude_runtime_resume.py` still passes.
8. `make check` stays green.
9. docs: the operator guide's section *The agent runs as a second user* replaces the paragraph that says a `time_limit` under `sudo` is not solved: the runtime puts `timeout --signal=KILL <limit>s` inside the `sudo` call, reads status 137 (or a death by `SIGKILL`) after the limit as `time_limit`, and kills the call itself only after 30 more seconds; the morning observation of a `time_limit` under `sudo` says what to see (no `claude` process of `agent` left after the limit); the decision log records the human's answer to F0010 decision 30 and why the inner kill is the agent's own; the project guide's description of the `claude -p` runtime names the call's new form. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_sudo_time_limit.py tests/adapters/test_claude_runtime_os_user.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
grep -n "TIMEOUT_EXECUTABLE = \|SUDO_GRACE = " src/factory/adapters/claude_runtime.py
```
Expect: two lines, `TIMEOUT_EXECUTABLE = "timeout"` and `SUDO_GRACE = timedelta(seconds=30)`, each after its line number.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted.
   - Interface: names concrete module `src/factory/adapters/claude_runtime.py`, both constants with values, the exact argument vector of the `sudo` call, the rounding rule, the outer limit, the exit statuses (137, -9) and the resume. The test files and stand-ins it names are the ones in the repository's test conventions.
   - Criteria: each is testable by one parametrized or single test function. Every behaviour in the Interface has a criterion: the argument vector and rounding (1), the end reason and no measures (2, 3), the `sudo:` line (4), the outer limit and the call without a user (5), the resume (6). The failing sides are covered: 137 or -9 before the limit is `died`, status 1 after the limit is `died`, and 137 without an `os_user` is `died` (3). The one earlier test that changes is named, with FEATURE decision 41 as the leave (7).
   - Demo: both commands are runnable. The `Expect:` lines are checkable: the pytest summary line has no failed, error or skipped count, and the grep prints two exact lines.
   - Architecture: the change sits wholly in `factory.adapters.claude_runtime`, the agent-runtime wrapper, and uses the existing `run_process` and `ProcessRequest`. No other layer is touched.
   - Scope: within F0012 item 1.8, which is S0024's own scope. Nothing in "Out of scope" is touched.
3. tester: Wrote the tests for criteria 1 to 7. The red tests are the coder's specification.

   Which criterion maps to which test:
   - criterion 1: tests/adapters/test_claude_runtime_sudo_time_limit.py::test_with_a_user_sudo_runs_the_agent_under_timeout_with_the_limit_rounded_up (rows `whole` 30 s → `30s`, `rounded-up` 1.5 s → `2s`). It uses the real `sudo` stand-in, the real `claude` stand-in and coreutils `timeout`.
   - criterion 2: …::test_with_a_user_the_inner_kill_at_the_limit_is_a_time_limit_without_measures. The `claude` stand-in prints a reply and then waits 60 s; the time limit is 1 s. Expected: `time_limit`, no decision, entry, turns, tokens, cost or model time, and the call ends in under 31 s.
   - criterion 3: …::test_a_kill_status_at_the_limit_under_sudo_is_a_time_limit_and_otherwise_a_death. Six rows: 137 or -9 at 30 s is `time_limit` with no measures; 137 or -9 at 29.9 s is `died`; status 1 at 30 s is `died`; 137 at 30 s without an `os_user` is `died`. It uses the `recorder` fixture, which puts a recorder in place of `claude_runtime.run_process` through monkeypatch.
   - criterion 4: …::test_a_sudo_line_before_the_inner_kill_is_a_runtime_error. The `sudo` stand-in prints `sudo: unable to resolve host x`; the time limit is 1 s. Expected: `AgentRuntimeError` whose detail holds that line.
   - criterion 5: …::test_the_outer_limit_adds_the_grace_only_under_sudo. Rows: with a user the outer limit is 60 s; without one it is 30 s and the arguments hold no `timeout`.
   - criterion 6: …::test_the_resume_under_sudo_is_limited_by_what_is_left_of_the_time_limit. The first call returns a budget-stop reply. Expected for the resume: `timeout --signal=KILL 30s` in its arguments, and a time limit above 59 s and at most 60 s.
   - criterion 7: the existing tests stay as they are. By the leave of FEATURE decision 41, I changed only the expected head in tests/adapters/test_claude_runtime_os_user.py::test_with_a_user_sudo_gets_the_user_env_i_the_environment_and_the_executable to `["-n", "-u", "agent", "--", "timeout", "--signal=KILL", "30s", "env", "-i"]`, with the slice offsets moved from 6 to 9.

   Files:
   - created tests/adapters/test_claude_runtime_sudo_time_limit.py; it imports `_request` and `_write_sudo` from test_claude_runtime_os_user.py, as the Interface allows
   - edited tests/adapters/test_claude_runtime_os_user.py, the one test above only

   Imports: every module imports. These tests fail with a wrong result, not a missing name:
   - the os_user head test
   - both rows of criterion 1
   - the two `time_limit` rows of criterion 3
   - the with-a-user row of criterion 5
   - criterion 6

   `make lint` is green.

   Open points for the next stage:
   - Criteria 2 and 4 already pass today, because the factory's own outer kill gives the same result at a 1 s limit. They guard the new path once `timeout` sits inside the `sudo` call, but they do not tell an inner kill from an outer one. Criterion 2's bound of 31 s is the one that would catch an inner kill that never fires.
   - `SUDO_GRACE` and `TIMEOUT_EXECUTABLE` are not imported by the tests. Criterion 5 pins the 60 s outer limit as a literal, and the demo's grep checks the two constants.
   - I ran `make test` twice instead of once: the first run had a lint fix still pending, and the second confirmed which tests fail.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/adapters/test_claude_runtime_sudo_time_limit.py::test_the_resume_under_sudo_is_limited_by_what_is_left_of_the_time_limit
4. coder: Built the inner kill under `sudo` in `src/factory/adapters/claude_runtime.py` (commit 9f6c1b3).

   What I built:
   - Three new constants: `TIMEOUT_EXECUTABLE = "timeout"`, `SUDO_GRACE = timedelta(seconds=30)` and `KILL_STATUSES = frozenset({137, -9})`.
   - `_process_request` now starts a request that has an `os_user` as `sudo -n -u <user> -- timeout --signal=KILL <ceil(seconds)>s env -i <assignments> <claude> ...`. The outer `ProcessRequest`'s `time_limit` is the call's limit plus `SUDO_GRACE`.
   - `_limit_argument` rounds the limit up with `math.ceil`, so 1.5 s becomes `2s`.
   - A request without an `os_user` is started and limited as before.
   - `_killed_at_limit(request, process, time_limit)` is true when all three hold: the request has an `os_user`, the exit status is 137 or -9, and the duration is at least that call's own limit.
   - When it is true, `_call` sets `timed_out=True` on the `ProcessResult` (with `model_copy`) before anything else reads it.

   Main design decision: I mark the inner kill as `timed_out` in `_call`, so the existing paths treat it like the factory's own kill without any change of their own:
   - `_end_reason` returns `time_limit`.
   - `_result` drops the measures.
   - `_sudo_refusal` raises on a `sudo:` line even when the reply parsed (criterion 4).
   - The resume already passes `left` to `_call`, so its `timeout` argument and outer limit follow from it (criterion 6).

   The alternative I rejected was passing the call's limit into `_end_reason`, `_result` and `_sudo_refusal` and checking for the kill in each of them. That would have meant three signatures changed and the same rule repeated three times.

   Refactor: I read my diff and found nothing to change, so there is no refactor commit.

   Checks:
   - `make check` is green: lint, types, layers, sast, secrets, licenses and test.
   - `make duplicates`: 0 new, 39 known, 0 gone.

   Open, not touched:
   - The docs criterion (9) is the documenter's.
   - The real run under `sudo` is still to be observed at the first start, as the assignment says.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.

   - Acceptance criteria: each of criteria 1 to 7 has a test in `tests/adapters/test_claude_runtime_sudo_time_limit.py` or in the existing suites, and each test checks what its criterion says.
     - Criterion 1: both rounding rows (30 s and 1.5 s).
     - Criterion 3: both sides of the 30 s duration boundary (30.0 s and 29.9 s), status 1, and no `os_user`.
     - Criterion 5: with and without a user.
     - Criterion 6: the resume's `timeout` argument and its outer limit, which must be above 59 s and at most 60 s.
     - The one earlier test that changed is the head assertion in `tests/adapters/test_claude_runtime_os_user.py`, as FEATURE decision 41 allows.
     - The coder's entry reports the factory's `make check` as green.
     - The tester's open point still holds. At a 1 s limit, criteria 2 and 4 cannot tell the inner kill from the outer one. Only criterion 2's bound of under 31 s catches an inner kill that never fires. That is acceptable, and the real run is still to be observed at the first start, as the assignment says.
   - Architecture: the change is only in `factory.adapters.claude_runtime`, which builds the argument list for the existing `run_process`. No new process call or layer import.
   - Security: the argument list is built as a list, never a shell string. `ceil` of a positive time limit is always at least 1, so `timeout 0s` (no limit at all) cannot happen; `run` returns before the resume when nothing is left. No markers that silence a check.
   - Quality: `_call` sets `timed_out` on the result once, so `_end_reason`, `_result` and `_sudo_refusal` stay unchanged. That is simpler than the alternative the coder rejected. The comments on `SUDO_GRACE` and `KILL_STATUSES` say why. `make duplicates` reports 0 new.
     - Minor, not raised as a finding: the criterion 1 test reads `sudo-calls.jsonl` inline instead of importing `_sudo_calls` from the os_user test module. It is three lines and not a separate helper.
   - Ticket hygiene: the log gives the main decision and what was rejected. `Assignment` matches what was built. Criterion 9 still says what the documenter must write.
6. documenter: Docs for the inner `timeout` kill under `sudo`.

   Files changed:
   - docs/operator-guide.md: the `sudo` call in "The agent runs as a second user" now shows `timeout --signal=KILL <limit>s`. I replaced the "not solved" paragraph with "A `time_limit` under `sudo`". It covers the inner kill, status 137/-9 at or after the limit read as `time_limit`, the 30 s grace before the factory's own kill, and what to see in the morning (no `claude` process of `agent` after the limit). The morning table row points to it.
   - docs/project-guide.md: the `claude -p` runtime's argument vector includes `timeout`. I added `TIMEOUT_EXECUTABLE`, `SUDO_GRACE`, `KILL_STATUSES`, the `timed_out` marking in `_call`, and the resume.
   - docs/decisions.md: new entry for the human's answer to F0010 decision 30, with why the agent's own kill is used and what was rejected.

   Cross-read and found current: README (it has no `sudo` text), the rest of the operator guide's `sudo:` rule paragraph (consistent with the diff), and the project guide's other runtime text. `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only documents.

   Findings: none. The code matches the Interface. The real run under `sudo` is still to be observed at the first start.

   Stale text I saw but did not touch: none.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran both demo commands from the repository root, in order. Both met their `Expect:` lines. No findings.

   1. `uv run pytest --no-header -p no:cacheprovider tests/adapters/test_claude_runtime_sudo_time_limit.py tests/adapters/test_claude_runtime_os_user.py`
   ```
   .........................                                                [100%]
   25 passed in 5.26s
   ```
   Met: the last line reads `25 passed in 5.26s`, with no failed, error or skipped count.

   2. `grep -n "TIMEOUT_EXECUTABLE = \|SUDO_GRACE = " src/factory/adapters/claude_runtime.py`
   ```
   54:TIMEOUT_EXECUTABLE = "timeout"
   57:SUDO_GRACE = timedelta(seconds=30)
   ```
   Met: two lines, each constant with the value the Interface gives, after its line number.

   Against the acceptance criteria:
   - The test run covers criteria 1 to 6 and the os_user part of criterion 7. Nothing in the output contradicts any of them.
   - The demo does not run the rest of criterion 7 (`test_claude_runtime.py` and `test_claude_runtime_resume.py`), criterion 8 (`make check`) or criterion 9 (docs). Nothing it shows contradicts them. The coder's entry reports `make check` green, and the documenter's entry reports `documents ok`.

   Still open, as the assignment says: the real kill under `sudo` is to be observed at the first start (step 3).
